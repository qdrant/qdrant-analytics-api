import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from qdrant_analytics_events.SegmentIdentify import Model as SegmentIdentify
from qdrant_analytics_events.SegmentPage import Model as SegmentPage

from app.config import get_app_config
from app.constants import NON_CONSENTED_USER_ID, QDRANT_ANONYMOUS_ID_KEY
from app.dependencies import authenticate
from app.segment.resolver import resolve_segment_service
from app.segment.service import SegmentService
from app.utils import create_args

logger = logging.getLogger(__name__)
logging.basicConfig(level=get_app_config().log_level)

router = APIRouter()


@router.get("/healthcheck")
async def healthcheck(request: Request):
    return {"message": "healthcheck successful"}


@router.get("/anonymous_id")
async def get_anonymous_id(
    response: Response, request: Request, _: str = Depends(authenticate)
):
    anonymous_id = str(uuid.uuid4())
    response.set_cookie(
        key=QDRANT_ANONYMOUS_ID_KEY,
        value=anonymous_id,
        domain="localhost",
        path="/",
        httponly=False,
        secure=False,  # Set to True in production with HTTPS
        samesite="None",  # Required for cross-site cookies
    )

    return JSONResponse(
        content={QDRANT_ANONYMOUS_ID_KEY: anonymous_id}, status_code=200
    )


# https://segment.com/docs/connections/sources/catalog/libraries/server/python/#identify
@router.post("/identify")
async def identify(
    request: Request,
    segment_service: Annotated[SegmentService, Depends(resolve_segment_service)],
    _: str = Depends(authenticate),
):
    try:
        user_id, anonymous_id, args, data = await create_args(
            request, exclude_properties=True
        )
        args["traits"] = data.get("traits", {})

        if (
            anonymous_id != NON_CONSENTED_USER_ID
        ):  # DO NOT associate a user_id with NON_CONSENTED_USER_ID
            segment_service.identify(
                SegmentIdentify(user_id=user_id, anonymous_id=anonymous_id, **args)
            )
        else:
            msg = f"User ({NON_CONSENTED_USER_ID}) was not identified"
            logger.warning(msg)
            return {"message": msg}

        return {"message": "User identified successfully"}
    except Exception as error:
        logger.error(f"Error (calling identify): {error}")
        return {"Error": error}


# https://segment.com/docs/connections/sources/catalog/libraries/server/python/#track
@router.post("/track")
async def track_event(
    request: Request,
    segment_service: Annotated[SegmentService, Depends(resolve_segment_service)],
    _: str = Depends(authenticate),
):
    try:
        data = await request.json()
        args = await create_args(request, data)

        success = segment_service.track_event(args)

        if success:
            return {"message": "Event tracked successfully"}
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Event track failed. Check logs for event: {args['event_name']}",
            )

    except Exception as error:
        msg = f"Error (calling /track): {error}"

        logger.error(msg)

        raise HTTPException(
            status_code=500,
            detail=msg,
        )


# https://segment.com/docs/connections/spec/page/
@router.post("/page")
async def page_viewed(
    request: Request,
    segment_service: Annotated[SegmentService, Depends(resolve_segment_service)],
    _: str = Depends(authenticate),
):
    user_id, anonymous_id, args, data = await create_args(request)
    args["category"] = data.get("category")

    segment_service.page_viewed(
        SegmentPage(
            user_id=user_id,
            anonymous_id=anonymous_id,
            name=data.get("name"),  # was formally title
            **args,
        )
    )

    return {"message": "Page view tracked successfully"}
