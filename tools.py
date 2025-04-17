# Example tools, add your own tools here and add them to the schema.json file

import httpx
import json
import asyncio

async def crypto_prices(product_id):
    url = f"https://api.coinbase.com/api/v3/brokerage/market/products/{product_id}"
    response = httpx.get(url, headers={'Content-Type': 'application/json'})
    return json.dumps(response.json())
