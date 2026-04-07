# Implement OpenEnv Environment Methods

Help implement or review the core methods of an OpenEnv environment server.

## Steps

1. Read `src/*/server.py` (or the path given in `$ARGUMENTS`) to understand the current implementation.
2. Read `src/*/models.py` to understand the `Action`, `Observation`, `State`, and `StepResult` types.
3. For each unimplemented or stub method (`reset`, `step`, `state`), propose a concrete implementation based on the environment's domain.
4. Ensure:
   - `reset()` returns a valid `Observation` and resets all episode state.
   - `step(action)` returns a `StepResult(observation, reward, done, info)`.
   - `state()` returns a `State` with at least `step_count` and `done`.
   - No blocking I/O inside async methods — use `asyncio` equivalents or run in executor.
5. After implementing, check that the `Action` model covers all fields the `step` method uses.
6. Suggest adding the environment to `pyproject.toml` entry points if missing.

## Usage

```
/implement-env [path/to/server.py]
```
