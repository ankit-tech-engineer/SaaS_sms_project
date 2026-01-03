from fastapi import APIRouter, Depends
from app.modules.payments.schema import PaymentWebhookRequest, PaymentResponse
from app.modules.payments.model import Payment
from app.utils.response import APIResponse
from app.core.database import get_database
from app.core.dependencies import check_permissions
from app.core.permissions import Permission
from app.utils.dependent_details import fetch_dependent_details

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

@router.get("", dependencies=[Depends(check_permissions([Permission.MANAGE_ORGS]))])
async def list_payments():
    db = await get_database()
    cursor = db["payments"].find().sort("created_at", -1)
    payments = await cursor.to_list(length=100)
    
    # Enrichment
    DEPENDENCY_MAP = {
        "subscription_id": {
            "collection": "subscriptions",
            # Subscription doesn't have a clear "name", sticking to status or None. 
            # Or assume user might iterate properly on frontend.
            # "name_field": "status" 
        }
    }
    
    enriched_data = await fetch_dependent_details(payments, DEPENDENCY_MAP)
    
    return APIResponse.success(enriched_data, "Payments retrieved successfully")
