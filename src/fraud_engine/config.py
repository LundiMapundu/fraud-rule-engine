from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "fraud-rule-engine"
    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_key: str = "dev-api-key-change-me"

    # Database (RDS PostgreSQL)
    database_url: str = "postgresql+asyncpg://fraud_user:fraud_pass@localhost:5432/fraud_engine"

    # Cache (ElastiCache Redis)
    redis_url: str = "redis://localhost:6379/0"

    # AWS
    aws_region: str = "af-south-1"
    aws_endpoint_url: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    sqs_queue_url: str = "http://localhost:4566/000000000000/fraud-engine-transactions"
    sns_topic_arn: str = "arn:aws:sns:af-south-1:000000000000:fraud-alerts"
    s3_bucket_name: str = "fraud-engine-audit"

    # Event processing
    sync_mode: bool = False
    sqs_poll_interval_seconds: int = 1
    sqs_max_messages: int = 10

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def get_boto_config(self) -> dict[str, str | None]:
        config: dict[str, str | None] = {"region_name": self.aws_region}
        if self.aws_endpoint_url:
            config["endpoint_url"] = self.aws_endpoint_url
        if self.aws_access_key_id:
            config["aws_access_key_id"] = self.aws_access_key_id
        if self.aws_secret_access_key:
            config["aws_secret_access_key"] = self.aws_secret_access_key
        return config


settings = Settings()
