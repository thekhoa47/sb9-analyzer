# app/services/zillow_redfin.py
import logging
import json
from openai import OpenAI
from app.config import settings

log = logging.getLogger("sb9.zillow")

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def fetch_listings_via_gpt(saved_search) -> list[dict]:
    """
    Calls GPT to fetch Zillow/Redfin deals that match the saved_search.
    Returns a list of dicts similar to RESO API output:
        { "ListingKey": "some-unique-id", "UnparsedAddress": "...", "ListPrice": 123456 }
    """
    prompt = f"""
    Find me the latest deals on Zillow or Redfin that match:
      - City: {saved_search.city}
      - Beds >= {saved_search.beds_min}
      - Baths >= {saved_search.baths_min}
      - Max Price: {saved_search.max_price}
    Return only structured JSON with fields:
      - ListingKey (string, unique, can be URL or ID)
      - UnparsedAddress (string)
      - ListPrice (number)
    """

    log.info("Prompting GPT for search %s (%s)", saved_search.id, saved_search.city)

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # small & cheap model
        messages=[
            {"role": "system", "content": "You are a real estate data fetcher."},
            {"role": "user", "content": prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "listing_response",
                "schema": {
                    "type": "object",
                    "properties": {
                        "listings": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "ListingKey": {"type": "string"},
                                    "UnparsedAddress": {"type": "string"},
                                    "ListPrice": {"type": "number"},
                                },
                                "required": [
                                    "ListingKey",
                                    "UnparsedAddress",
                                    "ListPrice",
                                ],
                            },
                        }
                    },
                    "required": ["listings"],
                },
            },
        },
        temperature=0,
    )

    try:
        raw = response.choices[0].message.content
        parsed = json.loads(raw)
        return parsed.get("listings", [])
    except Exception as e:
        log.exception("GPT fetch parse error: %s", e)
        return []
