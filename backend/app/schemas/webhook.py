from typing import Any, Optional
from pydantic import BaseModel, Field


class RazorpayError(BaseModel):
    code: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    step: Optional[str] = None
    reason: Optional[str] = None


class CustomerInfo(BaseModel):
    id: Optional[str] = None
    email: Optional[str] = None
    contact: Optional[str] = None
    name: Optional[str] = None


class PaymentEntity(BaseModel):
    id: str
    amount: int
    currency: str = "INR"
    status: str
    order_id: Optional[str] = None
    invoice_id: Optional[str] = None
    international: Optional[bool] = False
    method: Optional[str] = None
    amount_refunded: Optional[int] = 0
    captured: Optional[bool] = False
    description: Optional[str] = None
    card_id: Optional[str] = None
    bank: Optional[str] = None
    wallet: Optional[str] = None
    vpa: Optional[str] = None
    email: Optional[str] = None
    contact: Optional[str] = None
    customer_id: Optional[str] = None
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    error_source: Optional[str] = None
    error_step: Optional[str] = None
    error_reason: Optional[str] = None


class SubscriptionEntity(BaseModel):
    id: str
    plan_id: Optional[str] = None
    customer_id: Optional[str] = None
    status: str
    current_start: Optional[int] = None
    current_end: Optional[int] = None
    ended_at: Optional[int] = None
    quantity: Optional[int] = 1
    charge_at: Optional[int] = None
    start_at: Optional[int] = None
    end_at: Optional[int] = None
    auth_attempts: Optional[int] = 0
    total_count: Optional[int] = None
    paid_count: Optional[int] = 0
    customer_notify: Optional[bool] = True
    created_at: Optional[int] = None


class PaymentLinkEntity(BaseModel):
    id: str
    user_id: Optional[str] = None
    amount: int
    currency: str = "INR"
    status: str
    amount_paid: Optional[int] = 0
    customer: Optional[CustomerInfo] = None
    short_url: Optional[str] = None


class WebhookPayload(BaseModel):
    payment: Optional[dict[str, Any]] = None
    subscription: Optional[dict[str, Any]] = None
    payment_link: Optional[dict[str, Any]] = None


class WebhookEvent(BaseModel):
    entity: str = "event"
    account_id: Optional[str] = None
    event: str
    contains: list[str] = Field(default_factory=list)
    payload: WebhookPayload
    created_at: int
