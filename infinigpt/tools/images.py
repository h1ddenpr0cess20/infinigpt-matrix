import base64
import datetime
import httpx
import json
import os


def _config_path() -> str:
    return os.environ.get("INFINIGPT_CONFIG") or os.environ.get("INFINIGPT_CONFIG_PATH") or "config.json"


def _get_api_key(provider: str, env_name: str) -> str:
    # Prefer environment variables for secrets
    env = os.environ.get(env_name)
    if env:
        return env
    # Fallback to config file path
    try:
        with open(_config_path(), "r") as f:
            cfg = json.load(f)
        return cfg.get("llm", {}).get("api_keys", {}).get(provider, "")
    except Exception:
        return ""


def openai_image(prompt: str, quality: str = "medium") -> str:
    url = "https://api.openai.com/v1/images/generations"
    openai_key = _get_api_key("openai", "OPENAI_API_KEY")
    if not openai_key:
        return json.dumps({"error": "Missing OpenAI API key (OPENAI_API_KEY or llm.api_keys.openai)"})
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {openai_key}"}
    data = {"model": "gpt-image-1", "prompt": prompt, "n": 1, "moderation": "low", "quality": quality}
    with httpx.Client() as client:
        res = client.post(url, json=data, headers=headers, timeout=180)
        try:
            res.raise_for_status()
        except Exception:
            return json.dumps({"error": f"HTTP {res.status_code}: {res.text}"})
        result = res.json()
    if "data" in result and len(result["data"]) > 0 and "b64_json" in result["data"][0]:
        b64_data = result["data"][0]["b64_json"]
        image_data = base64.b64decode(b64_data)
        os.makedirs("./images", exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = f"./images/openai_image_{timestamp}.png"
        with open(file_path, "wb") as fp:
            fp.write(image_data)
        return file_path
    return json.dumps({"error": "No image data returned"})


def grok_image(prompt: str, model: str = "grok-2-image-1212") -> str:
    api_key = _get_api_key("xai", "XAI_API_KEY")
    if not api_key:
        return json.dumps({"error": "Missing xAI API key (XAI_API_KEY or llm.api_keys.xai)"})
    url = "https://api.x.ai/v1/images/generations"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"model": model, "prompt": prompt}
    with httpx.Client() as client:
        res = client.post(url, json=payload, headers=headers, timeout=60)
        try:
            res.raise_for_status()
        except Exception:
            return json.dumps({"error": f"HTTP {res.status_code}: {res.text}"})
        image_url = res.json().get("data", [{}])[0].get("url")
        if not image_url:
            return json.dumps({"error": "No image url returned"})
        img = client.get(image_url, timeout=60)
        try:
            img.raise_for_status()
        except Exception:
            return json.dumps({"error": f"HTTP {img.status_code}: {img.text}"})
        os.makedirs("./images", exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"./images/grok_image_{timestamp}.png"
        with open(filename, "wb") as fp:
            fp.write(img.content)
        return filename


def gemini_image(prompt: str, model: str = "gemini-2.5-flash-image-preview") -> str:
    api_key = _get_api_key("google", "GOOGLE_API_KEY")
    if not api_key:
        return json.dumps({"error": "Missing Google API key (GOOGLE_API_KEY or llm.api_keys.google)"})
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}}
    with httpx.Client() as client:
        res = client.post(url, json=payload, timeout=120)
        try:
            res.raise_for_status()
        except Exception:
            return json.dumps({"error": f"HTTP {res.status_code}: {res.text}"})
        response_json = res.json()
    parts = response_json.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    for part in parts:
        inline = part.get("inlineData", {})
        if "data" in inline:
            img_bytes = base64.b64decode(inline["data"])
            os.makedirs("./images", exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"./images/gemini_image_{timestamp}.png"
            with open(filename, "wb") as fp:
                fp.write(img_bytes)
            return filename
    return json.dumps({"error": "No image bytes returned"})
