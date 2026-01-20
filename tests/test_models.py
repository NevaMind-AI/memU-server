"""Tests for database models."""

from datetime import datetime, timezone

import pytest

from app.models import (
    Memory,
    MemoryCategory,
    MemorizeTask,
    TaskStatus,
)


def test_base_model_auto_fields():
    """Test that BaseModel automatically generates id and timestamps."""
    memory = Memory(
        user_id="user123",
        memory_id="mem123",
        content="Test memory",
    )
    
    assert memory.id is not None
    assert len(memory.id) > 0
    assert memory.created_at is not None
    assert memory.updated_at is not None


def test_memory_model_creation():
    """Test Memory model creation with required fields."""
    memory = Memory(
        user_id="user123",
        agent_id="agent456",
        memory_id="mem123",
        category="profile",
        content="User likes Python programming",
        embedding=[0.1] * 1536,
        links=["https://example.com"],
        happened_at=datetime.now(timezone.utc),
    )
    
    assert memory.user_id == "user123"
    assert memory.agent_id == "agent456"
    assert memory.memory_id == "mem123"
    assert memory.category == "profile"
    assert memory.content == "User likes Python programming"
    assert len(memory.embedding) == 1536
    assert memory.links == ["https://example.com"]
    assert memory.happened_at is not None


def test_memory_category_model():
    """Test MemoryCategory model creation."""
    category = MemoryCategory(
        user_id="user123",
        name="profile",
        category_type="auto",
        description="User profile information",
        config={"max_memories": 100},
        is_active=True,
        memory_count=5,
    )
    
    assert category.user_id == "user123"
    assert category.name == "profile"
    assert category.category_type == "auto"
    assert category.description == "User profile information"
    assert category.config["max_memories"] == 100
    assert category.is_active is True
    assert category.memory_count == 5


def test_memorize_task_model():
    """Test MemorizeTask model creation."""
    task = MemorizeTask(
        user_id="user123",
        agent_id="agent456",
        status=TaskStatus.PENDING,
        content="Remember this important fact",
        category="knowledge",
        task_metadata={"priority": "high"},
    )
    
    assert task.user_id == "user123"
    assert task.agent_id == "agent456"
    assert task.status == TaskStatus.PENDING
    assert task.content == "Remember this important fact"
    assert task.category == "knowledge"
    assert task.task_metadata["priority"] == "high"
    assert task.result is None
    assert task.error is None
    assert task.finished_at is None


def test_task_status_enum():
    """Test TaskStatus enum values."""
    assert TaskStatus.PENDING == "pending"
    assert TaskStatus.PROCESSING == "processing"
    assert TaskStatus.SUCCESS == "success"
    assert TaskStatus.FAILURE == "failure"
    assert TaskStatus.CANCELLED == "cancelled"


def test_memory_optional_fields():
    """Test Memory model with minimal required fields."""
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