from typing import Annotated

from fastapi import BackgroundTasks, Depends

from app.config import AppConfig, get_app_config
from app.segment.service import SegmentService


def resolve_segment_service(
    app_config: Annotated[AppConfig, Depends(get_app_config)],
    background_tasks: BackgroundTasks,
):
    return SegmentService(
        write_key=app_config.segment_write_key, background_tasks=background_tasks
    )
