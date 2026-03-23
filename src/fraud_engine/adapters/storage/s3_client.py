from __future__ import annotations

from typing import Any

import aioboto3
import structlog

from fraud_engine.config import Settings

logger = structlog.get_logger()


class S3StorageClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._bucket = settings.s3_bucket_name
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

    async def put(self, key: str, data: bytes, content_type: str = "application/json") -> None:
        async with self._session.client("s3", **self._boto_kwargs()) as s3:
            await s3.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            logger.debug("s3_object_stored", bucket=self._bucket, key=key)

    async def get(self, key: str) -> bytes | None:
        try:
            async with self._session.client("s3", **self._boto_kwargs()) as s3:
                response = await s3.get_object(Bucket=self._bucket, Key=key)
                return await response["Body"].read()
        except Exception:
            logger.debug("s3_object_not_found", bucket=self._bucket, key=key)
            return None
