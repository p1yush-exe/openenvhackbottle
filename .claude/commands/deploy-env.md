# Deploy OpenEnv Environment to Hugging Face Spaces

Package and deploy an OpenEnv environment as a Hugging Face Space (Docker SDK).

## Steps

1. Read `Dockerfile` in the current environment project. If missing, generate one that:
   - Uses `python:3.11-slim` as the base image.
   - Installs dependencies via `pip install -e .`
   - Exposes port `7860` (required by HF Spaces).
   - Sets `CMD ["uvicorn", "src.<env>.server:app", "--host", "0.0.0.0", "--port", "7860"]`.
2. Read `README.md` at the repo root. Add or update a `---` YAML frontmatter block with:
   ```yaml
   title: <env_name>
   sdk: docker
   app_port: 7860
   ```
3. Verify `pyproject.toml` lists all runtime dependencies so the Docker build is hermetic.
4. Remind the user to push to a Hugging Face Space repo:
   ```bash
   git remote add space https://huggingface.co/spaces/<username>/<space-name>
   git push space main
   ```
5. After deployment, the `base_url` for `EnvClient` will be:
   `https://<username>-<space-name>.hf.space`

## Usage

```
/deploy-env [env_name]
```
