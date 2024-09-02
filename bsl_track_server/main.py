"""
Copyright (C) 2024 Jath Palasubramaniam
Licensed under the Affero General Public License version 3
"""

from typing import Annotated

from fastapi import FastAPI, Depends

from bsl_track_server.logging import get_logger
from bsl_track_server.config import Settings, get_settings
from bsl_track_server import bsl

logger = get_logger()

app = FastAPI()
app.include_router(bsl.router)

@app.get("/")
def root(settings: Annotated[Settings, Depends(get_settings)]):
    """
    Return basic service information
    """

    return {
        "service": settings.service_name,
        "version": settings.service_version
    }