import logging
from datetime import datetime
from typing import Literal, TypeVar

import segment.analytics as analytics
from fastapi import BackgroundTasks
from qdrant_analytics_events.SegmentIdentify import Model as SegmentIdentify
from qdrant_analytics_events.SegmentPage import Model as SegmentPage
from qdrant_analytics_events.SegmentTrack import Model as SegmentTrack

from app.constants import NON_CONSENTED_USER_ID

logger = logging.getLogger(__name__)

TSegmentPage = TypeVar("TSegmentPage", bound=SegmentPage)
TSegmentTrack = TypeVar("TSegmentTrack", bound=SegmentTrack)
TSegmentIdentify = TypeVar("TSegmentIdentify", bound=SegmentIdentify)


class SegmentService:
    """
    Segment service acts as a facade for Segment API with background tasks.
    """

    def __init__(
        self,
        *,
        write_key: str,
        background_tasks: BackgroundTasks,
        source_name: Literal[
            "default", "cluster_api", "cloud_ui", "marketing"
        ] = "default",
        send: bool = True,
    ):
        """
        Initialize Segment service.

        :param str write_key: Segment's workspace write key
        :param BackgroundTasks background_tasks: Background task manager
        :param str source_name: Source/Origin Name
        """
        self.analytics = analytics.Client(
            write_key=write_key,
            sync_mode=True,
            max_retries=2,
            timeout=3,
            upload_size=1,  # 1 event per request, to avoid batching
            send=send,
            on_error=self._on_error,
        )
        self.background_tasks = background_tasks
        self.source_name = source_name

    ############
    # Identify #
    ############
    def identify(self, event: TSegmentIdentify) -> None:  # type: ignore
        """
        Identify Segment user in a background task, after the response is sent.

        :param str user_id: User id
        :param str anonymous_id: Anonymous id
        :param TSegmentIdentify event: Identify event model
        :return: None
        """

        try:
            event = SegmentIdentify.model_validate(event)
            event_props = event.model_dump(mode="json")
            user_id = event_props.pop("user_id", None)
            anonymous_id = event_props.pop("anonymous_id", NON_CONSENTED_USER_ID)

            if user_id is None or anonymous_id is None:
                raise ValueError("`user_id` and `anonymous id` are required")

            self.background_tasks.add_task(
                self._identify, user_id, anonymous_id, event_props
            )
        except Exception as error:
            self._on_error(error)

    def _identify(
        self,
        user_id: str | None,
        anonymous_id: str | None,
        event_props: dict,
    ) -> None:
        """
        Identify (event) in Segment.
        If an exception occurs, the background task will be dropped
        and the event will not be tracked.

        :param str user_id: User id
        :param str anonymous_id: Anonymous id
        :param TSegmentIdentify event: SegmentIdentify event model
        """

        try:
            event_props["timestamp"] = (
                datetime.strptime(event_props["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ")
                if event_props["timestamp"]
                else None
            )

            success, msg = self.analytics.identify(
                user_id=user_id, anonymous_id=anonymous_id, **event_props
            )
            if success:
                logger.info("User identify succeeded: %s. %s", msg, event_props)
            else:
                logger.warning(
                    "User identify did not succeed: %s. %s", msg, event_props
                )
        except Exception as error:
            self._on_error(error)

    #############
    # Page View #
    #############
    def page_viewed(self, event: TSegmentPage) -> None:  # type: ignore
        """
        Page event in Segment in a background task, after the response is sent.

        :param str user_id: User id
        :param str anonymous_id: Anonymous id (set to "not_consented" if user hasn't opted in)
        :param TSegmentPage event: SegmentPage event model
        :return: None
        """

        event = SegmentPage.model_validate(event)
        event_props = event.model_dump(mode="json")
        user_id = event_props.pop("user_id", None)
        anonymous_id = event_props.pop("anonymous_id", NON_CONSENTED_USER_ID)

        if user_id is None and anonymous_id is None:
            raise ValueError("`user_id` or `anonymous id` are required")

        self.background_tasks.add_task(
            self._page_viewed, user_id, anonymous_id, event_props
        )

    def _page_viewed(
        self,
        user_id: str | None,
        anonymous_id: str | None,
        event_props: dict,
    ) -> None:
        """
        Track Page Viewed (event) in Segment.
        If an exception occurs, the background task will be dropped
        and the event will not be tracked.

        :param str user_id: User id
        :param str anonymous_id: Anonymous id (set to "not_consented" if user hasn't opted in)
        :param dict event_props: { properties, context, integrations, timestamp }
        """

        try:
            event_props["timestamp"] = (
                datetime.strptime(event_props["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ")
                if event_props["timestamp"]
                else None
            )
            event_props["properties"]["source"] = self.source_name

            success, msg = self.analytics.page(
                user_id=user_id, anonymous_id=anonymous_id, **event_props
            )
            if success:
                logger.info("Event tracking succeeded: %s. %s", msg, event_props)
            else:
                logger.warning(
                    "Event tracking did not succeed: %s. %s", msg, event_props
                )
        except Exception as error:
            self._on_error(error)

    #########
    # Track #
    #########
    def track_event(self, event: TSegmentTrack) -> None:  # type: ignore
        """
        Track event in Segment in a background task, after the response is sent.

        :param str user_id: User id
        :param TSegmentTrack event: SegmentTrack event model
        :return: None
        """

        event = SegmentTrack.model_validate(event)
        event_props = event.model_dump(mode="json")
        user_id = event_props.pop("user_id", None)
        anonymous_id = event_props.pop("anonymous_id", NON_CONSENTED_USER_ID)
        event_name = event_props.pop("event_name", None)

        if (user_id is None and anonymous_id is None) or event_name is None:
            raise ValueError(
                "`user_id` (or `anonymous_id`) and `event_name` are required"
            )

        self.background_tasks.add_task(
            self._track_event, user_id, anonymous_id, event_name, event_props
        )

    def _track_event(
        self,
        user_id: str | None,
        anonymous_id: str | None,
        event_name: str,
        event_props: dict,
    ) -> None:
        """
        Track event in Segment.
        If an exception occurs, the background task will be dropped
        and the event will not be tracked.

        :param str user_id: User id
        :param str anonymous_id: Anonymous id (set to "not_consented" if user hasn't opted in)
        :param str event_name: Event name
        :param dict event_props: { properties, context, integrations, timestamp }
        """

        try:
            event_props["timestamp"] = (
                datetime.strptime(event_props["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ")
                if event_props["timestamp"]
                else None
            )

            success, msg = self.analytics.track(
                user_id=user_id,
                anonymous_id=anonymous_id,
                event=event_name,
                **event_props,
            )

            if success:
                logger.info("Event tracking succeeded: %s. %s", msg, event_props)
            else:
                logger.warning(
                    "Event tracking did not succeed: %s. %s", msg, event_props
                )
        except Exception as error:
            self._on_error(error)

    def _on_error(self, error: Exception) -> None:
        """
        Handle error in Segment.

        :param Exception error: Error
        """

        logging.error(error, exc_info=True)