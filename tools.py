# Example tools, add your own tools here and add them to the schema.json file

import httpx
import json
import base64
import datetime

async def crypto_prices(product_id):
    url = f"https://api.coinbase.com/api/v3/brokerage/market/products/{product_id}"
    response = httpx.get(url, headers={'Content-Type': 'application/json'})
    return json.dumps(response.json())


async def openai_image(prompt, quality="medium"):
    url = "https://api.openai.com/v1/images/generations"
    with open("config.json", 'r') as f:
        config = json.load(f)
    openai_key = config['llm']['api_keys']['openai']
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_key}"
    }
    data = {
        "model": "gpt-image-1",
        "prompt": prompt,
        "n": 1,
        "moderation": "low",
        "quality": quality,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers, timeout=httpx.Timeout(180.0))
        try:
            response.raise_for_status()
            result = response.json()
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"
        
        if 'data' in result and len(result['data']) > 0 and 'b64_json' in result['data'][0]:
            b64_data = result['data'][0]['b64_json']
            
            image_data = base64.b64decode(b64_data)
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            file_path = f"./images/openai_image_{timestamp}.png"
            with open(file_path, "wb") as image_file:
                image_file.write(image_data)
            return file_path

async def grok_image(prompt, model="grok-2-image-1212"):
    with open("config.json", "r") as f:
        api_key = json.load(f)["llm"]["api_keys"]["xai"]

    url = "https://api.x.ai/v1/images/generations"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"model": model, "prompt": prompt}

    with httpx.Client() as client:
        res = client.post(url, json=payload, headers=headers, timeout=60)
        res.raise_for_status()
        image_url = res.json()["data"][0]["url"]
        img = client.get(image_url, timeout=60)
        img.raise_for_status()

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"./images/grok_image_{timestamp}.png"
    with open(filename, "wb") as f:
        f.write(img.content)
    return filename

async def gemini_image(prompt, model="gemini-2.0-flash-exp-image-generation"):
    with open("config.json", "r") as f:
        api_key = json.load(f)["llm"]["api_keys"]["google"]

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
    }

    with httpx.Client() as client:
        res = client.post(url, json=payload, timeout=120)
        res.raise_for_status()
        data_b64 = (res.json()["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
        img_bytes = base64.b64decode(data_b64)

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"./images/gemini_image_{timestamp}.png"
    with open(filename, "wb") as f:
        f.write(img_bytes)
    return filename

async def openai_search(query: str):
    """
    Perform a web search using OpenAI's gpt-4o-mini-search-preview model and return structured search results.
    """
    url = "https://api.openai.com/v1/chat/completions"
    with open("config.json", "r") as f:
        openai_key = json.load(f)["llm"]["api_keys"]["openai"]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_key}"
    }
    data = {
        "model": "gpt-4o-mini-search-preview",
        "messages": [
            {"role": "user", "content": query}
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "search_results",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query that was executed."},
                        "total_results": {"type": "number", "description": "The total number of results found for the query."},
                        "results": {
                            "type": "array",
                            "description": "An array of result objects that match the search query.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "description": "The title of the search result."},
                                    "url": {"type": "string", "description": "The URL of the search result."},
                                    "snippet": {"type": "string", "description": "A brief snippet or summary of the search result."}
                                },
                                "required": ["title", "url", "snippet"],
                                "additionalProperties": False
                            }
                        },
                        "timestamp": {"type": "string", "description": "The time when the search was performed."}
                    },
                    "required": ["query", "total_results", "results", "timestamp"],
                    "additionalProperties": False
                }
            }
        },
        "web_search_options": {
            "search_context_size": "medium",
            "user_location": {
                "type": "approximate",
                "approximate": {
                    "country": "",
                    "timezone": "America/New_York"
                }
            }
        },
        "store": False
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data, timeout=httpx.Timeout(60.0))
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error occurred: {e.response.status_code} - {e.response.text}"}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}

