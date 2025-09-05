import httpx
import json


def crypto_prices(product_id: str) -> str:
    """Fetch Coinbase brokerage product ticker/metadata.

    Args:
        product_id: Coinbase product ID (e.g., "BTC-USD").

    Returns:
        JSON string of the API response or a JSON error string.
    """
    url = f"https://api.coinbase.com/api/v3/brokerage/market/products/{product_id}"
    response = httpx.get(url, headers={"Content-Type": "application/json"}, timeout=60)
    try:
        response.raise_for_status()
    except Exception:
        return json.dumps({"error": f"HTTP {response.status_code}"})
    try:
        return json.dumps(response.json(), ensure_ascii=False)
    except Exception:
        return json.dumps({"result": response.text})
