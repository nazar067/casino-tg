import requests
from config import PAYPAL_API_URL, PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, RETURN_URL, CANCEL_URL


def get_paypal_access_token():
    """
    Получить токен доступа PayPal
    """
    url = f"{PAYPAL_API_URL}/v1/oauth2/token"
    headers = {"Accept": "application/json", "Accept-Language": "en_US"}
    data = {"grant_type": "client_credentials"}
    response = requests.post(
        url,
        headers=headers,
        data=data,
        auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
    )
    response.raise_for_status()
    return response.json()["access_token"]


def create_payment(access_token, amount, currency="USD"):
    """
    Создать платеж через PayPal
    """
    url = f"{PAYPAL_API_URL}/v1/payments/payment"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    payload = {
        "intent": "sale",
        "payer": {
            "payment_method": "paypal",
        },
        "transactions": [
            {
                "amount": {
                    "total": amount,
                    "currency": currency,
                },
                "description": "Оплата через Telegram-бота",
            }
        ],
        "redirect_urls": {
            "return_url": RETURN_URL,
            "cancel_url": CANCEL_URL,
        },
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
