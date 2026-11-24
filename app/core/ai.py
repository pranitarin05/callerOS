import json
from typing import Optional

import httpx

from app.core.config import settings

MODELS = [
    settings.groq_model,
    "llama-3.1-8b-instant",
]

REQUIRED_FIELDS = (
    "lead_status",
    "interest",
    "requirements",
    "sentiment",
    "call_outcome",
    "next_action",
)

ENUM_FIELDS = ("lead_status", "interest", "sentiment", "call_outcome")

SYSTEM_PROMPT = (
    "You analyse sales call transcripts. Return ONLY a JSON object with these keys: "
    "lead_status (new|interested|qualified|not_interested), "
    "interest (low|medium|high), requirements (string), "
    "sentiment (positive|negative|neutral), "
    "call_outcome (interested|not_interested|callback|appointment_booked), "
    "next_action (string). Do not invent facts not present in the transcript."
)


def _clean(qualification: dict) -> Optional[dict]:
    if not isinstance(qualification, dict):
        return None
    if not all(field in qualification for field in REQUIRED_FIELDS):
        return None
    clean = {field: str(qualification[field]) for field in REQUIRED_FIELDS}
    allowed = {
        "lead_status": {"new", "interested", "qualified", "not_interested"},
        "interest": {"low", "medium", "high"},
        "sentiment": {"positive", "negative", "neutral"},
        "call_outcome": {"interested", "not_interested", "callback", "appointment_booked"},
    }
    for field, values in allowed.items():
        if clean[field].lower() not in values:
            clean[field] = ""
    return clean


async def generate_qualification(transcript: str, fallback: dict) -> dict:
    """Try Groq keys in order with model fallback; never raise to caller."""
    clean_fallback = _clean(fallback) or {}
    if not transcript or not settings.groq_api_keys:
        return clean_fallback

    url = "https://api.groq.com/openai/v1/chat/completions"
    for api_key in settings.groq_api_keys:
        for model in MODELS:
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    response = await client.post(
                        url,
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": model,
                            "temperature": 0.1,
                            "max_tokens": 400,
                            "response_format": {"type": "json_object"},
                            "messages": [
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {
                                    "role": "user",
                                    "content": f"Transcript:\n{transcript[:12000]}",
                                },
                            ],
                        },
                    )
                if response.status_code != 200:
                    continue
                content = response.json()["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                clean = _clean(parsed)
                if clean and all(clean[field] for field in ENUM_FIELDS):
                    return clean
            except Exception:
                continue

    return clean_fallback
