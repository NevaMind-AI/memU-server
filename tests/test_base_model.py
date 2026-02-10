"""Tests for BaseModel."""

from datetime import UTC, datetime

from app.models.base import BaseModel


def test_base_model_generates_id():
    """Test that BaseModel automatically generates a unique id."""

    class TestModel(BaseModel, table=False):
        """Test model for testing BaseModel."""

        name: str

    model1 = TestModel(name="test1")
    model2 = TestModel(name="test2")

    assert model1.id is not None
    assert model2.id is not None
    assert model1.id != model2.id
    assert len(model1.id) > 0


def test_base_model_generates_timestamps():
    """Test that BaseModel automatically generates timestamps."""

    class TestModel(BaseModel, table=False):
        """Test model for testing BaseModel."""

        name: str

    before = datetime.now(UTC)
    model = TestModel(name="test")
    after = datetime.now(UTC)

    assert model.created_at is not None
    assert model.updated_at is not None
    assert before <= model.created_at <= after
    assert before <= model.updated_at <= after


def test_base_model_timestamps_are_timezone_aware():
    """Test that timestamps have timezone information."""

    class TestModel(BaseModel, table=False):
        """Test model for testing BaseModel."""

        name: str

    model = TestModel(name="test")

    assert model.created_at.tzinfo is not None
    assert model.updated_at.tzinfo is not None


def test_base_model_id_is_ksuid_format():
    """Test that generated id follows KSUID format."""

    class TestModel(BaseModel, table=False):
        """Test model for testing BaseModel."""

        name: str

    model = TestModel(name="test")

    # KSUID should be 40 characters (hex string)
    assert len(model.id) == 40
    # KSUID should be a valid hex string
    assert all(c in "0123456789abcdef" for c in model.id.lower())
