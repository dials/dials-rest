"""
A RESTful API to a (limited) subset of DIALS functionality.

Authorization is currently handled through simple [JSON Web
Tokens](https://jwt.io/).

## Usage Example: Python/Requests

Given an authentication token you can use this API from python as:

```python
import pathlib
import requests

AUTHENTICATION_TOKEN = pathlib.Path("/path/to/token").read_text().strip()
auth_header = {"Authorization": f"Bearer {AUTHENTICATION_TOKEN}"}
base_url = "https://example-dials-rest.com"

# e.g. creating data collection
response = requests.post(
    f"{base_url}/export_bitmaps",
    headers=auth_header,
    json={
        # ... body schema, see API below ...
    },
)
response.raise_for_status()  # Check if the call was successful
```
"""

import logging

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from . import __version__
from .routers import find_spots, image
from .settings import Settings

logging.basicConfig(level=logging.INFO)

settings = Settings()
app = FastAPI(
    title="DIALS REST API",
    description=__doc__,
    version=__version__,
)

app.include_router(find_spots.router)
app.include_router(image.router)

if settings.enable_metrics:
    from prometheus_fastapi_instrumentator import Instrumentator

    instrumentator = Instrumentator(
        excluded_handlers=["/metrics"],
    )
    instrumentator.instrument(app)
    instrumentator.expose(app)


@app.get("/", include_in_schema=False)
def get_root():
    return RedirectResponse("/docs")
