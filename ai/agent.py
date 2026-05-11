"""
Customer chat agent — AI takım üyesinin yaklaşımına uyarlandı.

Google'ın yeni `google.genai` SDK'sı + function calling kullanıyor.
Tool'lar DB'den DOĞRUDAN okur (HTTP yok → auth/JWT derdi yok).

Contract:
  run_agent(customer_id: Optional[int], message: str) -> (reply: str, used_tools: list[str])

`AI_ENABLED=false` iken Gemini'ye gitmez, placeholder döner.
`customer_id` verilirse konuşma geçmişi DB'de tutulur (ChatMessage tablosu).
"""
import os
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from google import genai
from google.genai import types

from backend.database import SessionLocal
from backend.models import Order, OrderDetail, Product, ChatMessage

MODEL_NAME = "gemini-2.0-flash"  # gemini-2.5-flash free tier 20/gün, 2.0-flash 1500/gün
HISTORY_LIMIT = 10
MAX_ITER = 5

SYSTEM_PROMPT = """You are an AI assistant for an SMB e-commerce management system.
You help business owners with questions about their orders, products, inventory, and daily operations.

CRITICAL RULES:
1. ALWAYS call a tool to get real data. Never answer about specific products, orders, stock, or counts from memory.
2. For SPECIFIC items (e.g., "order #5", "tomatoes stock", "most expensive product"), call the broadest tool
   that returns the full list, then filter/analyze in your final answer. Do not refuse just because no
   filter parameter exists — the data is there in the list.
3. If user asks for an action (cancel, update, delete), say you cannot perform write operations,
   only read data.
4. If question is out of scope (weather, general knowledge), politely redirect to business topics.
5. Keep answers short and clear (max 3-4 sentences)."""


def _ai_enabled() -> bool:
    return os.environ.get("AI_ENABLED", "false").lower() == "true"


def _get_client() -> genai.Client:
    return genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))


# ============================================================
# TOOLS — bizim DB'den okur, HTTP yok
# ============================================================

def _tool_get_orders(db: Session) -> list:
    rows = db.query(Order).order_by(Order.id.desc()).all()
    out = []
    for o in rows:
        first = db.query(OrderDetail).filter(OrderDetail.order_id == o.id).first()
        product_name, quantity = "-", 0
        if first:
            quantity = first.quantity
            p = db.query(Product).filter(Product.id == first.product_id).first()
            if p:
                product_name = p.name
        out.append({
            "order_id": o.id,
            "customer": o.customer.name if o.customer else "-",
            "product": product_name,
            "quantity": quantity,
            "status": o.status,
            "total_price": o.total_amount,
            "tracking_no": o.tracking_no,
            "shipping_carrier": o.shipping_carrier,
            "order_date": o.order_date.strftime("%Y-%m-%d") if o.order_date else None,
            "estimated_delivery": o.estimated_delivery.strftime("%Y-%m-%d") if o.estimated_delivery else None,
        })
    return out


def _tool_get_products(db: Session) -> list:
    return [
        {
            "product_id": p.id,
            "name": p.name,
            "category": p.category,
            "price": p.price,
            "stock_quantity": p.stock_quantity,
            "critical_stock_level": p.critical_stock_level,
        }
        for p in db.query(Product).order_by(Product.id).all()
    ]


def _tool_get_inventory(db: Session) -> list:
    return [
        {
            "product_id": p.id,
            "name": p.name,
            "current_stock": p.stock_quantity,
            "critical_level": p.critical_stock_level,
            "is_critical": p.stock_quantity <= p.critical_stock_level,
        }
        for p in db.query(Product).order_by(Product.id).all()
    ]


def _tool_get_dashboard(db: Session) -> dict:
    return {
        "total_products": db.query(func.count(Product.id)).scalar() or 0,
        "total_orders": db.query(func.count(Order.id)).scalar() or 0,
        "pending_orders": db.query(func.count(Order.id)).filter(Order.status == "Pending").scalar() or 0,
        "preparing_orders": db.query(func.count(Order.id)).filter(Order.status == "Preparing").scalar() or 0,
        "completed_orders": db.query(func.count(Order.id)).filter(Order.status == "Completed").scalar() or 0,
        "low_stock_products": db.query(func.count(Product.id)).filter(
            Product.stock_quantity <= Product.critical_stock_level
        ).scalar() or 0,
    }


TOOL_FUNCTIONS = {
    "get_orders": _tool_get_orders,
    "get_products": _tool_get_products,
    "get_inventory": _tool_get_inventory,
    "get_dashboard": _tool_get_dashboard,
}


# Gemini'ye sunulan tool şemaları
TOOL_DECLARATIONS = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="get_orders",
        description="Get all orders with customer name, product, quantity, status, total price, tracking and shipping info.",
        parameters=types.Schema(type=types.Type.OBJECT, properties={}),
    ),
    types.FunctionDeclaration(
        name="get_products",
        description="Get all products with stock levels, prices, categories and critical stock thresholds.",
        parameters=types.Schema(type=types.Type.OBJECT, properties={}),
    ),
    types.FunctionDeclaration(
        name="get_inventory",
        description="Get inventory levels for all products with critical stock alerts (which products are below critical).",
        parameters=types.Schema(type=types.Type.OBJECT, properties={}),
    ),
    types.FunctionDeclaration(
        name="get_dashboard",
        description="Get dashboard summary numbers: total products, total orders, pending/preparing/completed orders count, low stock product count.",
        parameters=types.Schema(type=types.Type.OBJECT, properties={}),
    ),
])


# ============================================================
# HISTORY (ChatMessage tablosunda kalıcı)
# ============================================================

def _save_message(db: Session, customer_id: Optional[int], role: str, content: str):
    if customer_id is None:
        return
    db.add(ChatMessage(customer_id=customer_id, role=role, content=content))
    db.commit()


def _load_history(db: Session, customer_id: Optional[int], limit: int = HISTORY_LIMIT) -> list:
    if customer_id is None:
        return []
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.customer_id == customer_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    rows.reverse()
    return [(r.role, r.content) for r in rows]


def _placeholder_reply(msg: str) -> str:
    return (
        "[AI agent disabled - set AI_ENABLED=true to enable] "
        f"Your message: \"{msg}\""
    )


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def run_agent(customer_id: Optional[int], user_message: str) -> tuple[str, list[str]]:
    """
    Agent'ı tek bir kullanıcı mesajı için çalıştırır.

    Returns: (final_reply_text, list_of_tool_names_used)
    """
    db = SessionLocal()
    try:
        # 1) User mesajını kalıcı yap (customer_id varsa)
        _save_message(db, customer_id, "user", user_message)

        # 2) AI kapalıysa placeholder dön
        if not _ai_enabled():
            reply = _placeholder_reply(user_message)
            _save_message(db, customer_id, "assistant", reply)
            return reply, []

        client = _get_client()

        # 3) Konuşma geçmişini Gemini formatına çevir
        history = _load_history(db, customer_id)
        contents = []
        for role, content in history:
            gemini_role = "user" if role == "user" else "model"
            contents.append(types.Content(role=gemini_role, parts=[types.Part(text=content)]))
        contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[TOOL_DECLARATIONS],
        )

        used_tools: list[str] = []

        # 4) Agent loop — tool çağrısı kalmayana kadar dön
        for _ in range(MAX_ITER):
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=config,
            )

            cand = response.candidates[0]
            parts = cand.content.parts or []

            # Tool çağrısı var mı?
            function_calls = [(p.function_call, p) for p in parts if getattr(p, "function_call", None)]

            if not function_calls:
                # Tool çağrısı kalmadı — final cevap
                final_text = (response.text or "").strip()
                _save_message(db, customer_id, "assistant", final_text)
                return final_text, used_tools

            # Model'in tool-call mesajını contents'e ekle
            contents.append(types.Content(role="model", parts=parts))

            # Her tool'u çalıştır, sonuçları topla
            tool_response_parts = []
            for fc, _orig_part in function_calls:
                used_tools.append(fc.name)
                tool_fn = TOOL_FUNCTIONS.get(fc.name)
                if tool_fn is None:
                    result_payload = {"error": f"Unknown tool: {fc.name}"}
                else:
                    try:
                        raw = tool_fn(db)
                        # liste ise wrap, dict ise olduğu gibi
                        result_payload = {"result": raw} if not isinstance(raw, dict) else raw
                    except Exception as e:
                        result_payload = {"error": str(e)}

                tool_response_parts.append(types.Part(
                    function_response=types.FunctionResponse(
                        name=fc.name,
                        response=result_payload,
                    )
                ))

            contents.append(types.Content(role="user", parts=tool_response_parts))

        # 5) Loop limit
        fallback = "I had trouble completing that request. Please try rephrasing."
        _save_message(db, customer_id, "assistant", fallback)
        return fallback, used_tools

    finally:
        db.close()
