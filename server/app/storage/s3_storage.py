import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.config import Settings


class S3ObjectStorage:
	"""MinIO / S3 兼容对象存储。"""

	def __init__(self, settings: Settings) -> None:
		self._bucket = settings.s3_bucket
		self._client = boto3.client(
			's3',
			endpoint_url=settings.s3_endpoint,
			aws_access_key_id=settings.s3_access_key,
			aws_secret_access_key=settings.s3_secret_key,
			region_name=settings.s3_region,
			config=Config(signature_version='s3v4'),
		)
		self._ensure_bucket()

	def _ensure_bucket(self) -> None:
		try:
			self._client.head_bucket(Bucket=self._bucket)
		except ClientError:
			self._client.create_bucket(Bucket=self._bucket)

	def put_bytes(self, key: str, data: bytes, content_type: str) -> None:
		self._client.put_object(
			Bucket=self._bucket,
			Key=key,
			Body=data,
			ContentType=content_type,
		)

	def get_bytes(self, key: str) -> bytes:
		try:
			response = self._client.get_object(Bucket=self._bucket, Key=key)
		except ClientError as exc:
			if exc.response['Error']['Code'] in {'NoSuchKey', '404'}:
				raise FileNotFoundError(key) from exc
			raise
		return response['Body'].read()

	def delete(self, key: str) -> None:
		self._client.delete_object(Bucket=self._bucket, Key=key)

	def exists(self, key: str) -> bool:
		try:
			self._client.head_object(Bucket=self._bucket, Key=key)
			return True
		except ClientError as exc:
			if exc.response['Error']['Code'] in {'404', 'NoSuchKey', 'NotFound'}:
				return False
			raise
