from fastapi import APIRouter
from app.modules.payments.schema import PaymentWebhookRequest, PaymentResponse
from app.modules.payments.model import Payment
from app.utils.response import APIResponse
from app.core.database import get_database

router = APIRouter()

@router.post("/webhook", response_model=PaymentResponse)
async def payment_webhook(payment_in: PaymentWebhookRequest):
    db = await get_database()
    
    new_payment = Payment(
        subscription_id=payment_in.subscription_id,
        transaction_id=payment_in.transaction_id,
        amount=payment_in.amount,
        status=payment_in.status
    )
    
    await db["payments"].insert_one(new_payment.model_dump(by_alias=True))
    
    return APIResponse.success({"message": "Payment recorded"}, "Payment processed successfully")
