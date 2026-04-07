# Test an OpenEnv Environment

Run a quick validation loop against a running OpenEnv environment.

## Steps

1. Check if the environment server is running. If not, remind the user to start it:
   ```bash
   docker compose up   # or: uvicorn src.<env>.server:app --reload
   ```
2. Read the client file at `src/*/client.py` (or `$ARGUMENTS`) to find the client class name and `base_url`.
3. Write and run a short async test script that:
   - Calls `reset()` and prints the first observation.
   - Calls `step(action)` with a sample action and prints the `StepResult`.
   - Calls `state()` and prints episode metadata.
   - Asserts `done` eventually becomes `True` within 20 steps to confirm the episode terminates.
4. Report any type errors, missing fields, or exceptions found during the test.
5. If all checks pass, confirm the environment is ready for RL training integration.

## Usage

```
/test-env [path/to/client.py]
```
