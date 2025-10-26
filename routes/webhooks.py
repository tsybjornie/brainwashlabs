from fastapi import APIRouter, Request, HTTPException
import stripe, json, hmac, hashlib, os
import requests

router = APIRouter(prefix="/api/finance", tags=["finance"])

# ───────────────────────────────────────────────
# ⚙️ Stripe Webhook
# ───────────────────────────────────────────────
@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type in ["checkout.session.completed", "invoice.paid", "payment_intent.succeeded"]:
        email = data.get("customer_email") or data.get("receipt_email")
        amount = data.get("amount_total", 0) / 100
        print(f"✅ Stripe payment success for {email} — ${amount}")

        # 🚀 Call account creation endpoint
        try:
            requests.post(
                "https://brainwashlabs.onrender.com/api/auth/auto_create",
                json={"email": email, "plan": "Pro", "source": "Stripe"},
                timeout=10
            )
        except Exception as e:
            print("⚠️ Error creating user:", e)

    return {"status": "ok"}


# ───────────────────────────────────────────────
# ⚙️ Coinbase Webhook
# ───────────────────────────────────────────────
@router.post("/coinbase/webhook")
async def coinbase_webhook(request: Request):
    secret = os.getenv("COINBASE_API_KEY")
    signature = request.headers.get("X-CC-Webhook-Signature", "")
    body = await request.body()

    computed = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed, signature):
        raise HTTPException(status_code=400, detail="Invalid Coinbase signature")

    data = json.loads(body)
    event = data.get("event", {})
    event_type = event.get("type", "")
    charge = event.get("data", {})

    if event_type == "charge:confirmed":
        email = charge.get("metadata", {}).get("customer_email")
        amount = charge.get("pricing", {}).get("local", {}).get("amount")
        print(f"✅ Coinbase payment success for {email} — ${amount}")

        try:
            requests.post(
                "https://brainwashlabs.onrender.com/api/auth/auto_create",
                json={"email": email, "plan": "Pro", "source": "Coinbase"},
                timeout=10
            )
        except Exception as e:
            print("⚠️ Error creating user:", e)

    return {"status": "ok"}
