# Integrate OpenEnv with an RL Training Framework

Wire an OpenEnv environment into a supported RL training framework.

## Supported Frameworks

- **TRL** (Hugging Face)
- **torchforge** (PyTorch agentic RL)
- **Unsloth**
- **SkyRL**
- **ART**
- **Oumi**

## Steps

1. Ask the user which RL framework they are using if not specified in `$ARGUMENTS`.
2. Read `src/*/client.py` to identify the client class, `Action` fields, and `Observation` structure.
3. Generate a minimal training loop snippet for the chosen framework that:
   - Instantiates `EnvClient` with the correct `base_url`.
   - Maps the framework's action format to the `Action` dataclass.
   - Maps the `Observation` output to the framework's expected input format.
   - Handles the async/sync boundary (use `.sync()` wrapper for sync frameworks).
   - Resets between episodes when `StepResult.done` is `True`.
4. Show how to pass `reward` from `StepResult` to the framework's reward signal.
5. Note any framework-specific caveats (batching, vectorized envs, seed handling).

## Usage

```
/integrate-rl [framework_name]
```
