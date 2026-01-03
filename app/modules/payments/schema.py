from pydantic import BaseModel

class PaymentWebhookRequest(BaseModel):
    subscription_id: str
    transaction_id: str
    amount: float
    status: str

class PaymentResponse(BaseModel):
    message: str
