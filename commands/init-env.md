# Initialize a New OpenEnv Environment

Scaffold a new OpenEnv environment project using `openenv init`.

## Steps

1. Ask the user for the environment name if not provided as `$ARGUMENTS`.
2. Run `openenv init <name>` to scaffold the project.
3. Show the generated directory structure.
4. Open `src/<name>/server.py` and explain the three methods the user must implement:
   - `reset()` — initialize episode, return first `Observation`
   - `step(action)` — apply action, return `StepResult` with observation, reward, done flag
   - `state()` — return `State` with episode metadata
5. Open `src/<name>/models.py` and list the `Action` fields so the user knows what their environment will accept.
6. Suggest next steps: implement the methods, then run `/test-env` to validate.

## Usage

```
/init-env <env_name>
```
