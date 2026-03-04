"""Temporal worker entrypoint for memu-server."""

import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from app.workers.memorize_activity import task_memorize
from app.workers.memorize_workflow import MemorizeWorkflow
from config.settings import Settings

logger = logging.getLogger(__name__)

TASK_QUEUE = "memu-worker"


async def create_temporal_client(settings: Settings) -> Client:
    """Create and return a Temporal client."""
    temporal_url = settings.temporal_url
    namespace = settings.TEMPORAL_NAMESPACE
    logger.info("Connecting to Temporal at %s (namespace=%s)", temporal_url, namespace)

    client = await Client.connect(
        temporal_url,
        namespace=namespace,
    )
    logger.info("Connected to Temporal successfully")
    return client


async def run_worker(client: Client) -> None:
    """Run the Temporal worker with memorize workflow and activities."""
    worker = Worker(
        client=client,
        task_queue=TASK_QUEUE,
        workflows=[MemorizeWorkflow],
        activities=[task_memorize],
        identity="memu-worker",
    )

    logger.info("Starting Temporal worker on task queue: %s", TASK_QUEUE)

    async with worker:
        logger.info("Temporal worker is running. Press Ctrl+C to stop.")
        await asyncio.Future()  # Run forever


async def async_main() -> None:
    """Async entrypoint for worker."""
    logging.basicConfig(level=logging.INFO)
    settings = Settings()

    client = await create_temporal_client(settings)
    try:
        await run_worker(client)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    finally:
        await client.close()


def main() -> None:
    """Sync entrypoint for worker."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
