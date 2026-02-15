"""MemU service factory for creating MemoryService instances."""

from memu.app import MemoryService

from config.memu import build_memu_config
from config.settings import Settings


def create_memory_service(
    settings: Settings | None = None,
    memorize_config: dict | None = None,
    retrieve_config: dict | None = None,
) -> MemoryService:
    """Create a configured MemoryService instance.

    Args:
        settings: Application settings. Uses default if not provided.
        memorize_config: Optional memorize workflow config override.
        retrieve_config: Optional retrieve workflow config override.

    Returns:
        Configured MemoryService instance.
    """
    if settings is None:
        settings = Settings()

    memu_config = build_memu_config(settings)

    kwargs = {**memu_config}
    if memorize_config:
        kwargs["memorize_config"] = memorize_config
    if retrieve_config:
        kwargs["retrieve_config"] = retrieve_config

    return MemoryService(**kwargs)
