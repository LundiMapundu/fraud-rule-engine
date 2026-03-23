from __future__ import annotations

import json
from typing import Any

import aioboto3
import structlog

from fraud_engine.config import Settings

logger = structlog.get_logger()


class SnsPublisher:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._topic_arn = settings.sns_topic_arn
        self._session = aioboto3.Session()

    def _boto_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"region_name": self._settings.aws_region}
        if self._settings.aws_endpoint_url:
            kwargs["endpoint_url"] = self._settings.aws_endpoint_url
        if self._settings.aws_access_key_id:
            kwargs["aws_access_key_id"] = self._settings.aws_access_key_id
        if self._settings.aws_secret_access_key:
            kwargs["aws_secret_access_key"] = self._settings.aws_secret_access_key
        return kwargs

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        async with self._session.client("sns", **self._boto_kwargs()) as sns:
            message = json.dumps({"event_type": event_type, "payload": payload})
            await sns.publish(
                TopicArn=self._topic_arn,
                Message=message,
                Subject=event_type,
                MessageAttributes={"event_type": {"DataType": "String", "StringValue": event_type}},
            )
            logger.info("sns_message_published", event_type=event_type, topic=self._topic_arn)
