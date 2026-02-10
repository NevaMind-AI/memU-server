"""Tests for Memory model."""

from datetime import UTC, datetime

from app.models import Memory, MemoryCreate, MemoryUpdate
from app.models.memory import EMBEDDING_DIM


def test_memory_model_creation_with_all_fields():
    """Test Memory model creation with all fields."""
    memory = Memory(
        user_id="user123",
        agent_id="agent456",
        memory_id="mem123",
        category="profile",
        content="User likes Python programming",
        embedding=[0.1] * EMBEDDING_DIM,
        links=["https://example.com"],
        happened_at=datetime.now(UTC),
    )

    assert memory.user_id == "user123"
    assert memory.agent_id == "agent456"
    assert memory.memory_id == "mem123"
    assert memory.category == "profile"
    assert memory.content == "User likes Python programming"
    assert len(memory.embedding) == EMBEDDING_DIM
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
    """Test that embedding accepts correct dimensional vectors."""
    embedding = [0.5] * EMBEDDING_DIM

    memory = Memory(
        user_id="user123",
        memory_id="mem123",
        content="Test content",
        embedding=embedding,
    )

    assert memory.embedding is not None
    assert len(memory.embedding) == EMBEDDING_DIM


def test_memory_links_as_json():
    """Test that links field accepts JSON array data."""
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
    # Verify that the SQLAlchemy columns are configured with indexes
    table = Memory.__table__
    columns = table.c

    # Check that these columns are marked as indexed in the table schema
    assert columns.user_id.index is True
    assert columns.agent_id.index is True
    assert columns.memory_id.index is True
    assert columns.category.index is True

    # Also verify the primary key on id (inherited from BaseModel)
    # Note: primary_key already implies indexing in PostgreSQL, no separate index needed
    assert columns.id.primary_key is True
