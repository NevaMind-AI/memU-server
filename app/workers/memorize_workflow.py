"""Temporal workflow for memorize tasks."""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from app.workers.memorize_activity import task_memorize


@workflow.defn(name="MemorizeWorkflow")
class MemorizeWorkflow:
    """Workflow that orchestrates a memorize task via Temporal.

    Receives a spec dict and delegates to the task_memorize activity.
    """

    @workflow.run
    async def run(self, spec: dict) -> dict:
        """Execute the memorize workflow.

        Args:
            spec: Dict containing task_id, resource_url, user_id, agent_id, etc.

        Returns:
            Dict with task result from the activity.
        """
        return await workflow.execute_activity(
            task_memorize,
            spec,
            start_to_close_timeout=timedelta(minutes=10),
        )
