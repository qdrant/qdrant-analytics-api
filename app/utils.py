import os
from datetime import datetime, timezone
from typing import Tuple

from dotenv import load_dotenv
from fastapi import Request

from app.config import get_app_config
from app.constants import NON_CONSENTED_USER_ID

load_dotenv()

date_format = "%Y-%m-%dT%H:%M:%S.%fZ"


def now_tz() -> datetime:
    """
    Create a `datetime` instance with proper `tzinfo` in it. This will not be converted
    to `UTC`
    """
    config = get_app_config()
    return datetime.now(config.timezone)


def utc_now() -> datetime:
    """
    Create a `datetime` instance with proper `tzinfo` in it already `UTC` converted.
    """
    return now_tz().astimezone(timezone.utc)


def get_allowed_origins():
    origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
    return [origin.strip() for origin in origins if origin.strip()]


def get_ids(data: dict) -> Tuple[str, str]:
    user_id = data.get("user_id", None) if "user_id" in data else None
    anonymous_id = data.get("anonymous_id", None) or NON_CONSENTED_USER_ID

    return user_id, anonymous_id


def format_properties(request: Request, data: dict) -> dict:
    """
    Formatting the "properties" object for Segment consumption
    """

    properties = data.get("properties", {})

    origin = request.headers.get("origin", False)
    if "url" in properties and origin:
        path_and_search = properties["url"].replace(origin, "")
        path, _, search = path_and_search.partition("?")
        properties["path"] = path
        properties["search"] = search

    properties["referrer"] = request.headers.get("referer", None)
    properties["originalTimestamp"] = data.get("originalTimestamp", None)

    if data.get("name"):  # Page events have a name property
        properties["name"] = data.get("name")

    return properties


def format_context(
    request: Request, data: dict, properties: dict, anonymous_id: str
) -> dict:
    """
    Formatting the "context" object for Segment consumption
    ONLY IF a user has consented to tracking
    """

    if anonymous_id == NON_CONSENTED_USER_ID:
        return {}

    context = data.get("context", {})

    context["ip"] = request.client.host
    context["userAgent"] = request.headers.get("user-agent", None)
    context["locale"] = request.headers.get("Accept-Language", "").split(",")[0]

    properties = format_properties(request, properties)
    properties.pop("name", None)
    context["page"] = properties

    return context


async def create_args(
    request: Request, data: dict, exclude_properties: bool = False
) -> dict:
    [user_id, anonymous_id] = get_ids(data)

    args = {
        "event_name": data.get("event_name", "no event name"),
        "user_id": user_id,
        "anonymous_id": anonymous_id,
        "integrations": data.get("integrations", {}),
        "timestamp": data.get("originalTimestamp", utc_now().strftime(date_format)),
    }

    properties = format_properties(request, data)

    if not exclude_properties:
        args["properties"] = properties

    args["context"] = format_context(request, data, properties, anonymous_id)

    return args
