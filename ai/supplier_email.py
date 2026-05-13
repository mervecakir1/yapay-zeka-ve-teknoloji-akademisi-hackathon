"""
Supplier email draft service.

Stoğu kritik seviyenin altına düşen ürün için tedarikçiye gönderilecek
profesyonel bir İngilizce mail taslağı üretir.

İki mod:
  - AI_ENABLED=true  → Gemini'ye gider, doğal dilde mail üretir
  - AI_ENABLED=false (veya hata) → güvenli template'e düşer

Contract:
  input: product/supplier bilgileri + suggested_order_qty
  output: SupplierEmailDraft (subject, body, recipient, product_id)
"""
import os
import re
import logging

from google import genai
from google.genai import types

from backend.schemas import SupplierEmailDraft

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-flash-latest"

SYSTEM_PROMPT = """You are a procurement assistant for an SMB e-commerce business.
Generate a short, professional email in English to a supplier requesting stock replenishment.

OUTPUT FORMAT (strict):
SUBJECT: <one line subject>
BODY:
<email body, max 6 lines>

Rules:
- Professional but warm tone
- Mention the current stock, critical threshold, and the suggested order quantity
- Ask for delivery time confirmation
- Sign off with "Best regards"
- Do not invent additional details (no fake names, no fake dates, no fake offers)"""


def _ai_enabled() -> bool:
    return os.environ.get("AI_ENABLED", "false").lower() == "true"


def _template_draft(
    product_id: int,
    product_name: str,
    current_stock: int,
    critical_level: int,
    supplier_name: str,
    supplier_email: str,
    suggested_order_qty: int,
) -> SupplierEmailDraft:
    """AI_ENABLED=false veya Gemini hatası durumunda kullanılan güvenli template."""
    subject = f"Stock Replenishment Request - {product_name}"
    body = (
        f"Dear {supplier_name} Team,\n\n"
        f"Our stock for {product_name} has dropped to {current_stock} units "
        f"(critical threshold: {critical_level}). Based on our recent sales data, "
        f"we would like to place an order for {suggested_order_qty} units.\n\n"
        f"Please confirm availability and provide an estimated delivery date.\n\n"
        f"Best regards."
    )
    return SupplierEmailDraft(
        subject=subject,
        body=body,
        recipient=supplier_email,
        product_id=product_id,
    )


def _gemini_draft(
    product_id: int,
    product_name: str,
    current_stock: int,
    critical_level: int,
    supplier_name: str,
    supplier_email: str,
    suggested_order_qty: int,
) -> SupplierEmailDraft:
    """Gemini'ye prompt gönderip mail taslağı ürettirir."""
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

    user_msg = (
        f"Supplier: {supplier_name}\n"
        f"Product: {product_name}\n"
        f"Current stock: {current_stock} units\n"
        f"Critical threshold: {critical_level} units\n"
        f"Suggested order quantity: {suggested_order_qty} units\n"
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_msg,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )

    raw = (response.text or "").strip()

    # SUBJECT/BODY ayrıştır
    subject_match = re.search(r"SUBJECT:\s*(.+)", raw)
    body_match = re.search(r"BODY:\s*(.+)", raw, re.DOTALL)

    subject = subject_match.group(1).strip() if subject_match else f"Stock Replenishment Request - {product_name}"
    body = body_match.group(1).strip() if body_match else raw

    return SupplierEmailDraft(
        subject=subject,
        body=body,
        recipient=supplier_email,
        product_id=product_id,
    )


def draft_supplier_email(
    product_id: int,
    product_name: str,
    current_stock: int,
    critical_level: int,
    supplier_name: str,
    supplier_email: str,
    suggested_order_qty: int,
) -> SupplierEmailDraft:
    """
    Tedarikçi mail taslağı üretir.
    AI_ENABLED=true ise Gemini'yi dener, başarısız olursa template'e düşer.
    """
    args = (product_id, product_name, current_stock, critical_level,
            supplier_name, supplier_email, suggested_order_qty)

    if not _ai_enabled():
        return _template_draft(*args)

    try:
        return _gemini_draft(*args)
    except Exception:
        # Gemini hatası (quota, network, vb.) → güvenli template'e düş.
        # Sebebi log'ta olan gerçek bug'lar "quota" sanılmasın.
        logger.exception("Gemini supplier email draft failed; falling back to template")
        return _template_draft(*args)
