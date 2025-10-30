from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Callable

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties
from pydantic import ValidationError

from .config import settings
from .schemas import CompletedSearchTaskMessage, RawSearchTaskMessage
from .statuses import SearchTaskStatus


def _parameters() -> pika.URLParameters:
    return pika.URLParameters(settings.rabbitmq_url)


@contextmanager
def _connection():
    connection = pika.BlockingConnection(_parameters())
    try:
        yield connection
    finally:
        connection.close()


def _ensure_queues(channel: BlockingChannel) -> None:
    channel.queue_declare(queue=settings.raw_queue_name, durable=True)
    channel.queue_declare(queue=settings.completed_queue_name, durable=True)


def publish_raw_task(message: RawSearchTaskMessage) -> None:
    with _connection() as connection:
        channel = connection.channel()
        _ensure_queues(channel)
        channel.basic_publish(
            exchange="",
            routing_key=settings.raw_queue_name,
            body=message.model_dump_json(by_alias=True),
            properties=pika.BasicProperties(delivery_mode=2),
        )


def publish_completed_task(message: CompletedSearchTaskMessage) -> None:
    with _connection() as connection:
        channel = connection.channel()
        _ensure_queues(channel)
        channel.basic_publish(
            exchange="",
            routing_key=settings.completed_queue_name,
            body=message.model_dump_json(by_alias=True),
            properties=pika.BasicProperties(delivery_mode=2),
        )


def consume_raw_tasks(
    handler: Callable[[RawSearchTaskMessage], CompletedSearchTaskMessage],
    *,
    prefetch_count: int = 1,
) -> None:
    connection = pika.BlockingConnection(_parameters())
    channel = connection.channel()
    _ensure_queues(channel)
    channel.basic_qos(prefetch_count=prefetch_count)

    def _on_message(ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes) -> None:
        try:
            payload = RawSearchTaskMessage.model_validate_json(body)
        except ValidationError as exc:
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            print(f"[queue] invalid payload dropped: {exc}")  # noqa: T201
            return

        try:
            result = handler(payload)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            failure = CompletedSearchTaskMessage(
                task_id=payload.task_id,
                telegram_id=payload.telegram_id,
                status=SearchTaskStatus.FAILED,
                short_summary="AI search failed",
                summary=str(exc),
                completed_at=datetime.now(timezone.utc),
            )
            publish_completed_task(failure)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        publish_completed_task(result)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=settings.raw_queue_name, on_message_callback=_on_message, auto_ack=False)
    try:
        channel.start_consuming()
    finally:
        connection.close()


def consume_completed_tasks(
    handler: Callable[[CompletedSearchTaskMessage], None],
    *,
    prefetch_count: int = 1,
) -> None:
    connection = pika.BlockingConnection(_parameters())
    channel = connection.channel()
    _ensure_queues(channel)
    channel.basic_qos(prefetch_count=prefetch_count)

    def _on_message(ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes) -> None:
        try:
            payload = CompletedSearchTaskMessage.model_validate_json(body)
        except ValidationError as exc:
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            print(f"[queue] invalid completed payload dropped: {exc}")  # noqa: T201
            return
        handler(payload)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=settings.completed_queue_name, on_message_callback=_on_message, auto_ack=False)
    try:
        channel.start_consuming()
    finally:
        connection.close()
