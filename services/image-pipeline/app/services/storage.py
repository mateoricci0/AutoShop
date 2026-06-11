"""MinIO S3 storage client for generated images."""
from __future__ import annotations

import io
import uuid
import structlog

import boto3
from botocore.client import Config

logger = structlog.get_logger()


class ImageStorage:
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        public_endpoint: str | None = None,
    ) -> None:
        self._bucket = bucket
        self._public_endpoint = public_endpoint or endpoint
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except Exception:
            try:
                self._client.create_bucket(Bucket=self._bucket)
                # Make bucket publicly readable
                self._client.put_bucket_policy(
                    Bucket=self._bucket,
                    Policy=_public_read_policy(self._bucket),
                )
                logger.info("bucket_created", bucket=self._bucket)
            except Exception as e:
                logger.warning("bucket_create_failed", error=str(e))

    def upload(
        self,
        image_bytes: bytes,
        store_id: str,
        candidate_id: str,
        image_type: str,
        fmt: str = "png",
    ) -> tuple[str, str]:
        """Upload image bytes and return (storage_key, public_url)."""
        key = f"{store_id}/{candidate_id}/{image_type}/{uuid.uuid4()}.{fmt}"
        content_type = f"image/{fmt}" if fmt != "jpg" else "image/jpeg"

        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=io.BytesIO(image_bytes),
            ContentType=content_type,
        )

        url = f"{self._public_endpoint}/{self._bucket}/{key}"
        return key, url

    def delete(self, storage_key: str) -> None:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=storage_key)
        except Exception as e:
            logger.warning("storage_delete_failed", key=storage_key, error=str(e))


def _public_read_policy(bucket: str) -> str:
    import json
    return json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::{bucket}/*",
        }],
    })


_storage_instance: ImageStorage | None = None


def get_storage(settings) -> ImageStorage:  # type: ignore[type-arg]
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = ImageStorage(
            endpoint=settings.S3_ENDPOINT,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            bucket=settings.S3_BUCKET,
        )
    return _storage_instance
