"""
FastAPI application for the MedAgent Environment.

Endpoints (provided by openenv.core):
    POST /reset   – reset environment, returns initial observation
    POST /step    – execute action, returns observation + reward
    GET  /state   – current episode state
    GET  /schema  – action / observation JSON schemas
    WS   /ws      – WebSocket for persistent sessions
"""

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError(
        "openenv-core is required. Install it with:\n"
        "    pip install openenv-core[core]\n"
    ) from e

try:
    from ..models import MedAgentAction, MedAgentObservation
    from .medagent_environment import MedAgentEnvironment
except (ModuleNotFoundError, ImportError):
    from models import MedAgentAction, MedAgentObservation
    from server.medagent_environment import MedAgentEnvironment


app = create_app(
    MedAgentEnvironment,
    MedAgentAction,
    MedAgentObservation,
    env_name="medagent_env",
    max_concurrent_envs=4,
)


def run(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
