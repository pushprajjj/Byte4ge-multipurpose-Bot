import aiohttp
import os

GEMINI_API_KEY = "AIzaSyD6SLazFl1He7A5sfBNyuKLqrGItaLepIg"  # Replace with your API Key

async def get_gemini_response(prompt: str):
    """Fetch response from Gemini AI API."""
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateText"
    headers = {"Content-Type": "application/json"}
    payload = {
        "prompt": {"text": prompt},
        "temperature": 0.7,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, params={"key": GEMINI_API_KEY}, headers=headers) as response:
            data = await response.json()
            if "candidates" in data:
                return data["candidates"][0]["output"]
            return "I'm having trouble thinking right now. Try again later!"
