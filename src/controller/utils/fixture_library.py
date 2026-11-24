"""Download and ensure availability of the OFL fixture library."""

from __future__ import annotations

import os
import zipfile
from logging import getLogger

import requests

logger = getLogger(__name__)

_OFL_DOWNLOAD_URL = "https://open-fixture-library.org/download.ofl"


def ensure_fixture_library(cache_path: str) -> str:
    """Ensure the OFL fixture library exists under ``cache_path`` and return the fixtures directory.

    If the ``fixtures/`` directory inside ``cache_path`` already exists, it is left untouched. Otherwise
    the library zip is downloaded from the Open Fixture Library and extracted into place.

    Args:
        cache_path: Base directory that should contain a ``fixtures/`` sub-directory.

    Returns:
        Absolute path to the fixtures directory. If the download fails the returned path still points to
        the expected location (which may not exist); callers can check for that case themselves.

    """
    if not os.path.exists(cache_path):
        os.makedirs(cache_path, exist_ok=True)
    fixtures_path = os.path.join(cache_path, "fixtures/")
    if os.path.exists(fixtures_path):
        return fixtures_path

    logger.info("Downloading fixture library. Please wait")
    zip_path = os.path.join(cache_path, "fixtures.zip")
    r = requests.get(_OFL_DOWNLOAD_URL, allow_redirects=True, timeout=30)
    if r.status_code != 200:
        logger.error("Failed to download fixture library (HTTP %d)", r.status_code)
        return fixtures_path

    with open(zip_path, "wb") as file:
        file.write(r.content)
    with zipfile.ZipFile(zip_path) as zip_ref:
        zip_ref.extractall(fixtures_path)
    logger.info("Fixture lib downloaded and installed.")
    return fixtures_path
