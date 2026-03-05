"""Request/response schemas for memory endpoints."""

from pydantic import BaseModel, Field, model_validator


# ── Memorize (async) ──
class MemorizeRequest(BaseModel):
    """Request to memorize a conversation."""

    conversation: dict | list = Field(..., description="Conversation data to memorize")
    user_id: str = Field(..., description="User ID")
    agent_id: str = Field(default="", description="Agent ID")
    override_config: dict | None = Field(default=None, description="Override MemU config")


class MemorizeResponse(BaseModel):
    """Response after submitting an async memorize task."""

    task_id: str = Field(..., description="Task ID for tracking (Temporal workflow ID)")
    status: str = Field(default="PENDING", description="Initial task status")
    message: str = Field(default="Memorization task submitted", description="Response message")


# ── Task Status ──
class TaskStatusResponse(BaseModel):
    """Response for task status query."""

    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Task status: PENDING, RUNNING, COMPLETED, FAILED")
    detail: str | None = Field(default=None, description="Status detail or error message")


class ClearMemoriesRequest(BaseModel):
    """Request to clear memories for a user/agent."""

    user_id: str | None = Field(default=None, description="User ID")
    agent_id: str | None = Field(default=None, description="Agent ID")

    @model_validator(mode="after")
    def check_user_or_agent(self) -> "ClearMemoriesRequest":
        if self.user_id is None and self.agent_id is None:
            msg = "At least one of user_id or agent_id must be provided"
            raise ValueError(msg)
        return self


class ClearMemoriesResponse(BaseModel):
    """Response after clearing memories."""

    purged_categories: int = Field(default=0, description="Number of deleted categories")
    purged_items: int = Field(default=0, description="Number of deleted items")
    purged_resources: int = Field(default=0, description="Number of deleted resources")


# ── Categories ──


class ListCategoriesRequest(BaseModel):
    """Request to list memory categories."""

    user_id: str = Field(..., description="User ID")
    agent_id: str | None = Field(default=None, description="Agent ID")


class CategoryObject(BaseModel):
    """A single memory category."""

    name: str
    description: str
    user_id: str
    agent_id: str | None = None
    summary: str | None = None


class ListCategoriesResponse(BaseModel):
    """Response with list of memory categories."""

    categories: list[CategoryObject] = Field(default_factory=list)
