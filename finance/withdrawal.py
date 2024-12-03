import requests
from config import PAYPAL_API_URL, PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET


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


def create_payout(access_token, receiver_email, amount, currency="USD"):
    """
    Создать выплату через PayPal
    """
    url = f"{PAYPAL_API_URL}/v1/payments/payouts"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    payload = {
        "sender_batch_header": {
            "email_subject": "Вы получили выплату!",
        },
        "items": [
            {
                "recipient_type": "EMAIL",
                "amount": {
                    "value": amount,
                    "currency": currency,
                },
                "receiver": receiver_email,
            }
        ],
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
