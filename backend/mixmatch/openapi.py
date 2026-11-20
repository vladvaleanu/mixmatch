"""Scrie schema OpenAPI pe stdout, fără să pornească serverul. Folosit de `make types`."""

import json

from mixmatch.main import app

if __name__ == "__main__":
    print(json.dumps(app.openapi(), indent=2, ensure_ascii=False))
