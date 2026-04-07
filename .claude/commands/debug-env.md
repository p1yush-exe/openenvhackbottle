# Debug an OpenEnv Environment via Web UI

Use the OpenEnv built-in web interface to interactively inspect and debug an environment.

## Steps

1. Ensure the environment server is running locally:
   ```bash
   uvicorn src.<env>.server:app --reload --port 8000
   ```
2. Open the web UI at `http://localhost:8000` — it provides:
   - A two-pane layout with action input and observation output.
   - Dynamically generated forms for each `Action` field.
   - Real-time WebSocket updates showing each `StepResult`.
   - Full action history for the current episode.
3. Read `src/*/server.py` if the user reports unexpected behavior, and check:
   - `reset()` returns a valid initial `Observation` (non-null fields, correct types).
   - `step()` does not raise unhandled exceptions on edge-case actions.
   - `state()` returns consistent `step_count` that increments each step.
4. For WebSocket errors, check that the server mounts the `/ws` route and that no firewall blocks the port.
5. Summarize any bugs found and propose fixes in `server.py`.

## Usage

```
/debug-env
```
