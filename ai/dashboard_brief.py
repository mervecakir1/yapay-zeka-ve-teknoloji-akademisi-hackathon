"""
Dashboard AI brief service.

İşletme sahibine günlük operasyon özetini 3-4 cümlelik doğal bir paragrafla sunar.

İki mod:
  - AI_ENABLED=true  → Gemini sayıları yorumlar, akıcı İngilizce metin üretir
  - AI_ENABLED=false (veya hata) → güvenli kural-tabanlı özete düşer

Contract:
  input: stats dict (pending_orders, preparing_orders, shipped_today, low_stock_count, today_revenue)
  output: str (3-4 cümlelik özet)
"""
import os
import logging
import time

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-flash-latest"
BRIEF_CACHE_TTL_SECONDS = 15 * 60

_BRIEF_CACHE: dict[tuple, tuple[float, str]] = {}

SYSTEM_PROMPT = """You are an operations assistant for an SMB e-commerce business.
The user gives you today's metrics. Produce a short morning brief (3-4 sentences max)
in clear English that:
  - Mentions the numbers naturally (not just listing them)
  - Highlights action items (pending orders, critical stock)
  - Sounds like a human assistant, not a robotic report
  - Never invents numbers — use only what's given"""


def _ai_enabled() -> bool:
    return os.environ.get("AI_ENABLED", "false").lower() == "true"


def _rule_based_brief(stats: dict) -> str:
    """AI_ENABLED=false veya Gemini hatası durumunda kullanılan kural-tabanlı özet."""
    parts = []
    if stats.get("pending_orders"):
        parts.append(f"{stats['pending_orders']} pending orders.")
    if stats.get("preparing_orders"):
        parts.append(f"{stats['preparing_orders']} in preparation.")
    if stats.get("shipped_today"):
        parts.append(f"{stats['shipped_today']} shipped today.")
    if stats.get("low_stock_count"):
        parts.append(f"{stats['low_stock_count']} products at critical stock.")
    # Revenue 0 olsa bile göster — "bugün satış yok" da bilgi.
    revenue = stats.get("today_revenue")
    if revenue is not None:
        parts.append(f"Today's revenue: ${revenue:.2f}.")
    return " ".join(parts) if parts else "No pending work for today."


def _gemini_brief(stats: dict) -> str:
    """Gemini'ye stats gönderip akıcı bir özet ürettir."""
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

    user_msg = (
        f"Pending orders: {stats.get('pending_orders', 0)}\n"
        f"In preparation: {stats.get('preparing_orders', 0)}\n"
        f"Shipped today: {stats.get('shipped_today', 0)}\n"
        f"Products at critical stock: {stats.get('low_stock_count', 0)}\n"
        f"Today's revenue: ${stats.get('today_revenue', 0):.2f}\n"
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_msg,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )
    return (response.text or "").strip()


def _stats_cache_key(stats: dict) -> tuple:
    return tuple(sorted(stats.items()))


def generate_brief(stats: dict) -> str:
    """
    Dashboard sabah özeti üretir.
    AI_ENABLED=true ise Gemini'yi dener, başarısız olursa kural-tabanlı'ya düşer.
    """
    cache_key = _stats_cache_key(stats)
    now = time.monotonic()
    cached = _BRIEF_CACHE.get(cache_key)
    if cached is not None:
        expires_at, cached_text = cached
        if now < expires_at:
            return cached_text

    if not _ai_enabled():
        return _rule_based_brief(stats)

    try:
        result = _gemini_brief(stats)
        final_text = result if result else _rule_based_brief(stats)
        _BRIEF_CACHE[cache_key] = (now + BRIEF_CACHE_TTL_SECONDS, final_text)
        return final_text
    except Exception:
        # Gemini hatası → güvenli fallback. Sebebi log'la ki sessizce yutmayalım.
        logger.exception("Gemini dashboard brief failed; falling back to rule-based summary")
        fallback = _rule_based_brief(stats)
        _BRIEF_CACHE[cache_key] = (now + 60, fallback)
        return fallback
