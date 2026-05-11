"""
Supplier email draft stub.

AI takım üyesinin domain'i. Bu fonksiyonun içini Gemini ile profesyonel bir mail
taslağı üretecek şekilde doldurun.

Beklenen contract:
  - input: product/supplier bilgileri + suggested_order_qty
  - output: SupplierEmailDraft (subject, body, recipient, product_id)

Şu anki implementasyon: basit Türkçe şablon döner.
"""
from backend.schemas import SupplierEmailDraft


def draft_supplier_email(
    product_id: int,
    product_name: str,
    current_stock: int,
    critical_level: int,
    supplier_name: str,
    supplier_email: str,
    suggested_order_qty: int,
) -> SupplierEmailDraft:
    subject = f"Stock Replenishment Request - {product_name}"
    body = (
        f"Dear {supplier_name} Team,\n\n"
        f"Our stock for {product_name} has dropped to {current_stock} units "
        f"(critical threshold: {critical_level}). Based on our recent sales data, "
        f"we would like to place an order for {suggested_order_qty} units.\n\n"
        f"Please confirm availability and provide an estimated delivery date.\n\n"
        f"Best regards.\n\n"
        f"[AI not yet implemented - app/services/supplier_email.py]"
    )
    return SupplierEmailDraft(
        subject=subject,
        body=body,
        recipient=supplier_email,
        product_id=product_id,
    )
