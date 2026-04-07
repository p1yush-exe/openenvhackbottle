"""
ClinicalBench typed HTTP/WebSocket client.

Usage (async):
    import asyncio
    from clinical_bench import ClinicalBenchClient, ClinicalAction

    async def main():
        async with ClinicalBenchClient(base_url="ws://localhost:8080") as env:
            result = await env.reset(task_name="clinical_calc", task_index=0)
            print(result.observation.task_description)
            result = await env.step(ClinicalAction(code="answer = 42\\nprint(answer)"))
            print(result.observation.reward)

    asyncio.run(main())

Usage (sync):
    env = ClinicalBenchClient(base_url="ws://localhost:8080").sync()
    with env:
        result = env.reset(task_name="biostat_power")
        result = env.step(ClinicalAction(code="print(0.95)"))

Usage (from Docker image):
    async with await ClinicalBenchClient.from_docker_image("clinical-bench:latest") as env:
        result = await env.reset()

Usage (from Hugging Face Space):
    async with await ClinicalBenchClient.from_env("your-org/clinical-bench") as env:
        result = await env.reset()
"""

from __future__ import annotations

from openenv.core.env_client import EnvClient
from openenv.core.client_types import StepResult

from .models import ClinicalAction, ClinicalObservation, ClinicalState


class ClinicalBenchClient(EnvClient[ClinicalAction, ClinicalObservation, ClinicalState]):
    """
    Typed async client for the ClinicalBench environment server.

    Inherits ``reset``, ``step``, ``state``, ``from_docker_image``,
    ``from_env``, and ``.sync()`` from the openenv-core base class.
    """

    def _step_payload(self, action: ClinicalAction) -> dict:
        return action.model_dump()

    def _parse_result(self, payload: dict) -> StepResult[ClinicalObservation]:
        obs_data = payload.get("observation", payload)
        obs = ClinicalObservation(**obs_data)
        return StepResult(
            observation=obs,
            reward=float(obs.reward) if obs.reward is not None else 0.0,
            done=bool(obs.done),
        )

    def _parse_state(self, payload: dict) -> ClinicalState:
        return ClinicalState(**payload)
