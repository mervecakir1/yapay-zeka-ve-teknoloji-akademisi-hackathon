"""
Dashboard AI brief stub.

AI takım üyesinin domain'i. İşletme sahibi için 3-4 cümlelik Türkçe sabah özeti
üretmek üzere Gemini ile doldurun.

Beklenen contract:
  - input: stats dict (pending_orders, preparing_orders, shipped_today,
    low_stock_count, today_revenue)
  - output: str (Türkçe brief)

Şu anki implementasyon: basit kural-tabanlı özet döner.
"""


def generate_brief(stats: dict) -> str:
    parts = []
    if stats.get("pending_orders"):
        parts.append(f"{stats['pending_orders']} pending orders.")
    if stats.get("preparing_orders"):
        parts.append(f"{stats['preparing_orders']} in preparation.")
    if stats.get("shipped_today"):
        parts.append(f"{stats['shipped_today']} shipped today.")
    if stats.get("low_stock_count"):
        parts.append(f"{stats['low_stock_count']} products at critical stock.")
    if stats.get("today_revenue"):
        parts.append(f"Today's revenue: ${stats['today_revenue']:.2f}.")
    base = " ".join(parts) if parts else "No pending work for today."
    return f"{base} [AI brief not yet implemented]"
