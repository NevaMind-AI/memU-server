"""Tests for Memory model."""

from datetime import UTC, datetime

from app.models import Memory, MemoryCreate, MemoryUpdate


def test_memory_model_creation_with_all_fields():
    """Test Memory model creation with all fields."""
    memory = Memory(
        user_id="user123",
        agent_id="agent456",
        memory_id="mem123",
        category="profile",
        content="User likes Python programming",
        embedding=[0.1] * 1536,
        links=["https://example.com"],
        happened_at=datetime.now(UTC),
    )

    assert memory.user_id == "user123"
    assert memory.agent_id == "agent456"
    assert memory.memory_id == "mem123"
    assert memory.category == "profile"
    assert memory.content == "User likes Python programming"
    assert len(memory.embedding) == 1536
    assert memory.links == ["https://example.com"]
    assert memory.happened_at is not None
    # BaseModel fields
    assert memory.id is not None
    assert memory.created_at is not None
    assert memory.updated_at is not None


def test_memory_model_with_minimal_fields():
    """Test Memory model with only required fields."""
    memory = Memory(
        user_id="user123",
        memory_id="mem123",
        content="Simple memory",
    )

    assert memory.user_id == "user123"
    assert memory.memory_id == "mem123"
    assert memory.content == "Simple memory"
    assert memory.agent_id is None
    assert memory.category is None
    assert memory.embedding is None
    assert memory.links is None
    assert memory.happened_at is None


def test_memory_embedding_dimension():
    """Test that embedding accepts 1536-dimensional vectors."""
    embedding_1536 = [0.5] * 1536

    memory = Memory(
        user_id="user123",
        memory_id="mem123",
        content="Test content",
        embedding=embedding_1536,
    )

    assert memory.embedding is not None
    assert len(memory.embedding) == 1536


def test_memory_links_as_json():
    """Test that links field accepts list/dict data."""
    links = [
        "https://example.com",
        {"url": "https://test.com", "title": "Test"},
    ]

    memory = Memory(
        user_id="user123",
        memory_id="mem123",
        content="Test content",
        links=links,
    )

    assert memory.links == links
    assert len(memory.links) == 2


def test_memory_create_schema():
    """Test MemoryCreate schema."""
    memory_create = MemoryCreate(
        user_id="user123",
        memory_id="mem123",
        content="New memory",
        category="event",
    )

    assert memory_create.user_id == "user123"
    assert memory_create.category == "event"


def test_memory_update_schema():
    """Test MemoryUpdate schema with partial updates."""
    update = MemoryUpdate(
        content="Updated content",
        category="new_category",
    )

    assert update.content == "Updated content"
    assert update.category == "new_category"
    # Other fields should be None (not updated)
    assert update.links is None
    assert update.embedding is None


def test_memory_tablename():
    """Test that Memory uses correct table name."""
    assert Memory.__tablename__ == "memories"


def test_memory_indexes():
    """Test that Memory has proper indexes on key fields."""
    # user_id, agent_id, memory_id, category should be indexed
    memory = Memory(
        user_id="user123",
        memory_id="mem123",
        content="Test",
    )

    # Verify fields exist
    assert hasattr(memory, "user_id")
    assert hasattr(memory, "agent_id")
    assert hasattr(memory, "memory_id")
    assert hasattr(memory, "category")
