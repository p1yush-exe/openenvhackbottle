"""
FastAPI application entry point for the ClinicalBench OpenEnv server.

Start with:
    uvicorn clinical_bench.server.app:app --host 0.0.0.0 --port 8080
"""

import os
from pathlib import Path

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openenv.core.env_server.http_server import create_app

from ..models import ClinicalAction, ClinicalObservation
from .environment import ClinicalBenchEnvironment, DATA_PATH


def _make_env() -> ClinicalBenchEnvironment:
    """Factory called by HTTPEnvServer for each new session."""
    return ClinicalBenchEnvironment(data_path=DATA_PATH)


app = create_app(
    env=_make_env,
    action_cls=ClinicalAction,
    observation_cls=ClinicalObservation,
    env_name="clinical_bench",
    max_concurrent_envs=4,
)

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_DIST / "assets"),
        name="frontend-assets",
    )

    @app.get("/", include_in_schema=False)
    async def frontend_index():
        return FileResponse(FRONTEND_DIST / "index.html")


def main():
    """Entry point for running the server directly."""
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
