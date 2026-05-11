from typing import Annotated

from fastapi import APIRouter, HTTPException
from starlette import status

from ..database import db_dependency
from ..models import Customer
from ..schemas import ChatRequest, ChatResponse
from ai.agent import run_agent

router = APIRouter(prefix="/chat", tags=["Chat"])






@router.post("/", response_model=ChatResponse)
def send_message(payload: ChatRequest, db: db_dependency):
    """
    Mesajı AI agent'a iletir (services/agent.py).
    - customer_id opsiyonel: verilirse müşteri doğrulanır + konuşma geçmişi kaydedilir.
    - customer_id None: staff/anonim sorgu (geçmiş tutulmaz).
    """
    if payload.customer_id is not None:
        customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
        if customer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    reply, used_tools = run_agent(payload.customer_id, payload.message)
    return ChatResponse(reply=reply, used_tools=used_tools)
