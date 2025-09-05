import json
import logging
from openai import OpenAI
from app.config import settings

log = logging.getLogger("sb9.analyze")

SYSTEM_PROMPT = (
    "You are Khoa’s Listing Analyst. Return STRICT JSON per the provided schema. "
    "Be conservative. Scoring: 90-100 exceptional, 80-89 strong, 70-79 decent, "
    "60-69 marginal, <60 pass. "
    "Flip: >=12% gross margin over all-in; "
    "MTR: CoC>=8% at 80% occ; "
    "Buy&Hold: DSCR>=1.15 at base+150bps. "
    "List concise next steps. If uncertain, say so."
)

SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
        "summary": {"type": "string"},
        "strategyFit": {
            "type": "array",
            "items": {"type": "string", "enum": ["Buy&Hold", "MTR", "Flip"]},
        },
        "rentEst": {"type": "integer"},
        "arvEst": {"type": "integer"},
        "pros": {"type": "array", "items": {"type": "string"}},
        "cons": {"type": "array", "items": {"type": "string"}},
        "dealBreakers": {"type": "array", "items": {"type": "string"}},
        "nextSteps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["score", "summary", "strategyFit", "pros", "cons", "nextSteps"],
}

# Initialize the OpenAI client once
client = OpenAI(api_key=settings.OPENAI_API_KEY)


def analyze_listing(listing: dict) -> dict:
    """
    Analyze a listing using OpenAI. Returns a dict per SCHEMA.
    Falls back to mock if no API key is configured.
    """
    if not settings.OPENAI_API_KEY:
        # fallback mock for local dev
        return {
            "score": 75,
            "summary": "Solid 4/3 candidate; verify rents and school rating.",
            "strategyFit": ["Buy&Hold", "MTR"],
            "rentEst": 4200,
            "arvEst": listing.get("ListPrice", 0),
            "pros": ["4/3 config", "reasonable price"],
            "cons": ["unknown HOA", "lot size average"],
            "dealBreakers": [],
            "nextSteps": [
                "Pull comps 0.5mi/6mo",
                "Estimate rehab",
                "Confirm DSCR at 7.5%",
            ],
        }

    user_payload = {
        "address": listing.get("UnparsedAddress"),
        "price": listing.get("ListPrice"),
        "beds": listing.get("BedroomsTotal"),
        "baths": listing.get("BathroomsTotalInteger"),
        "sqft": listing.get("LivingArea"),
        "lot": listing.get("LotSizeArea"),
        "remarks": listing.get("PublicRemarks"),
    }

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-5.1-mini" if enabled
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(user_payload)},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "ListingAnalysis", "schema": SCHEMA},
            },
            temperature=0,
        )

        raw = resp.choices[0].message.content
        parsed = json.loads(raw)
        return parsed

    except Exception as e:
        log.exception("analyze_listing failed: %s", e)
        return {
            "score": 60,
            "summary": "Error during analysis; manual review needed.",
            "strategyFit": [],
            "rentEst": 0,
            "arvEst": listing.get("ListPrice", 0),
            "pros": [],
            "cons": [],
            "dealBreakers": [],
            "nextSteps": ["Retry with valid API key / response"],
        }
