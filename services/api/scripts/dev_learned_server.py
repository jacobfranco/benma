"""Run the normal API with resident learned inference in the pinned local dev environment.

Invoke with benchmark/pronunciation_v2/.venv/bin/python. The frozen inference
environment takes precedence; append the existing API dependencies without
installing or modifying either historical environment. No model/provider startup
occurs until the normal analysis endpoint receives a recording.
"""

import os
import site
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services/api"
sys.path.insert(0, str(API / "src"))
site.addsitedir(str(API / ".venv/lib/python3.12/site-packages"))
os.chdir(API)


def main() -> None:
    import uvicorn

    from benma_api.config import Settings

    settings = Settings()
    if settings.environment != "development" or not settings.enable_dev_learned_tone:
        raise SystemExit(
            "Requires BENMA_ENVIRONMENT=development BENMA_ENABLE_DEV_LEARNED_TONE=true"
        )
    # One long-lived process. Reloads/restarts necessarily pay the cold-load cost.
    uvicorn.run("benma_api.app:app", host="0.0.0.0", port=8000, workers=1)


if __name__ == "__main__":
    main()
