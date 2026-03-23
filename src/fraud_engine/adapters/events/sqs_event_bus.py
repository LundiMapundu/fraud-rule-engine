from __future__ import annotations

import asyncio
import contextlib
import json
from collections.abc import Callable, Coroutine
from typing import Any

import aioboto3
import structlog

from fraud_engine.config import Settings

logger = structlog.get_logger()


class SqsEventBus:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._queue_url = settings.sqs_queue_url
        self._session = aioboto3.Session()
        self._running = False
        self._handler: Callable[[str, dict[str, Any]], Coroutine[Any, Any, None]] | None = None
        self._consumer_task: asyncio.Task[None] | None = None

    def set_handler(
        self, handler: Callable[[str, dict[str, Any]], Coroutine[Any, Any, None]]
    ) -> None:
        self._handler = handler

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
        async with self._session.client("sqs", **self._boto_kwargs()) as sqs:
            message = json.dumps({"event_type": event_type, "payload": payload})
            await sqs.send_message(
                QueueUrl=self._queue_url,
                MessageBody=message,
                MessageAttributes={"event_type": {"DataType": "String", "StringValue": event_type}},
            )
            logger.info("sqs_message_published", event_type=event_type)

    async def start_consuming(self) -> None:
        self._running = True
        self._consumer_task = asyncio.create_task(self._poll_loop())
        logger.info("sqs_consumer_started", queue_url=self._queue_url)

    async def stop_consuming(self) -> None:
        self._running = False
        if self._consumer_task:
            self._consumer_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._consumer_task
        logger.info("sqs_consumer_stopped")

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                async with self._session.client("sqs", **self._boto_kwargs()) as sqs:
                    response = await sqs.receive_message(
                        QueueUrl=self._queue_url,
                        MaxNumberOfMessages=self._settings.sqs_max_messages,
                        WaitTimeSeconds=self._settings.sqs_poll_interval_seconds,
                        MessageAttributeNames=["All"],
                    )

                    messages = response.get("Messages", [])
                    for msg in messages:
                        try:
                            body = json.loads(msg["Body"])
                            event_type = body.get("event_type", "unknown")
                            payload = body.get("payload", {})

                            if self._handler:
                                await self._handler(event_type, payload)

                            await sqs.delete_message(
                                QueueUrl=self._queue_url,
                                ReceiptHandle=msg["ReceiptHandle"],
                            )
                            logger.info("sqs_message_processed", event_type=event_type)

                        except Exception:
                            logger.exception(
                                "sqs_message_processing_failed",
                                message_id=msg.get("MessageId"),
                            )

            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("sqs_poll_error")
                await asyncio.sleep(5)
