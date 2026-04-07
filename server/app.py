"""
ClinicalBench server entry point.

This module satisfies the OpenEnv convention of having a `server/app.py`
at the repository root.  All implementation lives in `clinical_bench/server/`.
"""

import os


def main() -> None:
    """Start the ClinicalBench OpenEnv server."""
    import uvicorn
    from clinical_bench.server.app import app  # noqa: F401

    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(
        "clinical_bench.server.app:app",
        host="0.0.0.0",
        port=port,
        workers=1,
        timeout_keep_alive=75,
    )


if __name__ == "__main__":
    main()
