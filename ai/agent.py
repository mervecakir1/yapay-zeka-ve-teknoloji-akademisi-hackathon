"""
Customer chat agent.

Google `google.genai` SDK + function calling kullanÄ±r.
Tool'lar DB'den DOÄRUDAN okur (HTTP yok â†’ auth/JWT derdi yok).

Contract:
  run_agent(customer_id: Optional[int], message: str) -> (reply: str, used_tools: list[str])

DavranÄ±ÅŸ:
  - AI_ENABLED=false â†’ Gemini'ye gitmez, placeholder dÃ¶ner
  - AI_ENABLED=true ama Gemini hata verirse (quota, network, vb.) â†’ graceful quota-fallback
  - customer_id verilirse konuÅŸma geÃ§miÅŸi DB'de tutulur (ChatMessage tablosu)
"""
import os
import logging
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from google import genai
from google.genai import types

from backend.database import SessionLocal
from backend.models import Order, OrderDetail, Product, Supplier, ChatMessage

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-flash-latest"
HISTORY_LIMIT = 10
MAX_ITER = 5

SYSTEM_PROMPT = """You are an AI assistant for an SMB e-commerce management system.
You help business owners with questions about their orders, products, inventory, suppliers, and daily operations.

CRITICAL RULES:
1. ALWAYS call a tool to get real data. Never answer about specific products, orders, suppliers, stock, or counts from memory.
2. For SPECIFIC items (e.g., "order #5", "tomatoes stock", "Anatolia supplier phone", "most expensive product"), call the broadest tool
   that returns the full list, then filter/analyze in your final answer. Do not refuse just because no
   filter parameter exists â€” the data is there in the list.
3. If user asks for an action (cancel, update, delete), say you cannot perform write operations,
   only read data.
4. If question is out of scope (weather, general knowledge), politely redirect to business topics.
5. Keep answers short and clear (max 3-4 sentences)."""


def _ai_enabled() -> bool:
    return os.environ.get("AI_ENABLED", "false").lower() == "true"


def _get_client() -> genai.Client:
    return genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))


# ============================================================
# TOOLS â€” bizim DB'den okur, HTTP yok
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


def _tool_get_suppliers(db: Session) -> list:
    return [
        {
            "supplier_id": s.id,
            "name": s.name,
            "email": s.email,
            "phone": s.phone,
            "products_count": len(s.products),
            "products": [
                {
                    "product_id": p.id,
                    "name": p.name,
                    "stock_quantity": p.stock_quantity,
                    "critical_stock_level": p.critical_stock_level,
                }
                for p in s.products
            ],
        }
        for s in db.query(Supplier).order_by(Supplier.id).all()
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
    "get_suppliers": _tool_get_suppliers,
    "get_dashboard": _tool_get_dashboard,
}


# Gemini'ye sunulan tool ÅŸemalarÄ±
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
        name="get_suppliers",
        description="Get all suppliers with supplier name, email, phone number, product count, and linked products.",
        parameters=types.Schema(type=types.Type.OBJECT, properties={}),
    ),
    types.FunctionDeclaration(
        name="get_dashboard",
        description="Get dashboard summary numbers: total products, total orders, pending/preparing/completed orders count, low stock product count.",
        parameters=types.Schema(type=types.Type.OBJECT, properties={}),
    ),
])


# ============================================================
# HISTORY (ChatMessage tablosunda kalÄ±cÄ±)
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


def _quota_error_reply(msg: str) -> str:
    return (
        "[AI service temporarily unavailable - quota limit reached. "
        "Please try again later.] "
        f"Your message: \"{msg}\""
    )


def _missing_key_error_reply(msg: str) -> str:
    return (
        "[AI configuration error - GOOGLE_API_KEY is missing or unreadable. "
        "Please check your .env file.] "
        f"Your message: \"{msg}\""
    )


def _generic_ai_error_reply(msg: str) -> str:
    return (
        "[AI service temporarily unavailable. Please try again later.] "
        f"Your message: \"{msg}\""
    )


def _error_reply_from_exception(msg: str, exc: Exception) -> str:
    err_text = str(exc).lower()
    if "no api key" in err_text or "api key" in err_text and "provided" in err_text:
        return _missing_key_error_reply(msg)
    if "quota" in err_text or "rate limit" in err_text or "429" in err_text:
        return _quota_error_reply(msg)
    return _generic_ai_error_reply(msg)


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def run_agent(
    customer_id: Optional[int],
    user_message: str,
    db: Optional[Session] = None,
) -> tuple[str, list[str]]:
    """
    Agent'Ä± tek bir kullanÄ±cÄ± mesajÄ± iÃ§in Ã§alÄ±ÅŸtÄ±rÄ±r.

    Args:
        customer_id: Varsa konuÅŸma geÃ§miÅŸi DB'de tutulur, yoksa stateless.
        user_message: KullanÄ±cÄ± sorusu.
        db: Caller tarafÄ±ndan aÃ§Ä±lmÄ±ÅŸ SQLAlchemy session (Ã¶rn. FastAPI dependency).
            Verilirse boÅŸa connection aÃ§Ä±lmaz; verilmezse iÃ§eride yenisi aÃ§Ä±lÄ±r.

    Returns: (final_reply_text, list_of_tool_names_used)

    NOT: User mesajÄ± DB'ye burada DEÄÄ°L, _run_gemini_agent iÃ§inde geÃ§miÅŸ
    yÃ¼klendikten SONRA kaydedilir. Aksi halde Gemini aynÄ± mesajÄ± iki kez gÃ¶rÃ¼r
    (history'de + son content'te).
    """
    # DÄ±ÅŸarÄ±dan session geldiyse onu kullan; gelmediyse kendi session'umuzu aÃ§ ve sonda kapat.
    owns_db = db is None
    if owns_db:
        db = SessionLocal()
    try:
        # AI kapalÄ±ysa placeholder dÃ¶n
        if not _ai_enabled():
            _save_message(db, customer_id, "user", user_message)
            reply = _placeholder_reply(user_message)
            _save_message(db, customer_id, "assistant", reply)
            return reply, []

        # AI aÃ§Ä±k â€” Gemini'yi dene, hata olursa quota fallback'a dÃ¼ÅŸ
        try:
            return _run_gemini_agent(db, customer_id, user_message)
        except Exception as e:
            # GerÃ§ek hata sebebini log'la, kullanÄ±cÄ±ya graceful mesaj dÃ¶n.
            logger.exception("Gemini agent failed for customer_id=%s", customer_id)
            _save_message(db, customer_id, "user", user_message)
            reply = _error_reply_from_exception(user_message, e)
            _save_message(db, customer_id, "assistant", reply)
            return reply, []
    finally:
        if owns_db:
            db.close()


def _run_gemini_agent(db: Session, customer_id: Optional[int], user_message: str) -> tuple[str, list[str]]:
    """Gemini'ye gerÃ§ek Ã§aÄŸrÄ± + tool calling loop. Hata fÄ±rlatabilir."""
    client = _get_client()

    # KonuÅŸma geÃ§miÅŸini Gemini formatÄ±na Ã§evir
    # Ã–NEMLÄ°: history'yi user mesajÄ±nÄ± DB'ye kaydetmeden Ã–NCE yÃ¼kle, yoksa
    # son user mesajÄ± hem history'de hem de aÅŸaÄŸÄ±daki append'te yer alÄ±r
    # (Gemini iÃ§in duplikasyon).
    history = _load_history(db, customer_id)
    contents = []
    for role, content in history:
        gemini_role = "user" if role == "user" else "model"
        contents.append(types.Content(role=gemini_role, parts=[types.Part(text=content)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))

    # GeÃ§miÅŸ alÄ±ndÄ±ktan SONRA mesajÄ± kalÄ±cÄ± yap â€” bir sonraki Ã§aÄŸrÄ±da gÃ¶rÃ¼lsÃ¼n.
    _save_message(db, customer_id, "user", user_message)

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[TOOL_DECLARATIONS],
    )

    used_tools: list[str] = []

    # Agent loop â€” tool Ã§aÄŸrÄ±sÄ± kalmayana kadar dÃ¶n
    for _ in range(MAX_ITER):
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=config,
        )

        cand = response.candidates[0]
        parts = cand.content.parts or []

        # Tool Ã§aÄŸrÄ±sÄ± var mÄ±?
        function_calls = [(p.function_call, p) for p in parts if getattr(p, "function_call", None)]

        if not function_calls:
            # Tool Ã§aÄŸrÄ±sÄ± kalmadÄ± â€” final cevap
            final_text = (response.text or "").strip()
            _save_message(db, customer_id, "assistant", final_text)
            return final_text, used_tools

        # Model'in tool-call mesajÄ±nÄ± contents'e ekle
        contents.append(types.Content(role="model", parts=parts))

        # Her tool'u Ã§alÄ±ÅŸtÄ±r, sonuÃ§larÄ± topla
        tool_response_parts = []
        for fc, _orig_part in function_calls:
            used_tools.append(fc.name)
            tool_fn = TOOL_FUNCTIONS.get(fc.name)
            if tool_fn is None:
                result_payload = {"error": f"Unknown tool: {fc.name}"}
            else:
                try:
                    raw = tool_fn(db)
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

    # Loop limit
    fallback = "I had trouble completing that request. Please try rephrasing."
    _save_message(db, customer_id, "assistant", fallback)
    return fallback, used_tools
