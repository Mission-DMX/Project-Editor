import os
import zipfile
from logging import getLogger

import requests

logger = getLogger(__name__)

def ensure_standard_fixture_library_exists(prefix="/var/cache/missionDMX") -> tuple[bool, str]:
    """This function ensures that the standard library fixture library exists.

    This method will attempt to download the library if it is missing.

    :return: True if the standard library fixture library exists or was successfully downloaded, otherwise False.
    """
    if not os.path.exists(prefix):
        os.mkdir(prefix)
    fixtures_path = os.path.join(prefix, "fixtures/")
    if not os.path.exists(fixtures_path):
        zip_path = os.path.join(prefix, "fixtures.zip")
        logger.info("Downloading fixture library. Please wait")
        url = "https://open-fixture-library.org/download.ofl"
        r = requests.get(url, allow_redirects=True, timeout=5)
        if r.status_code != 200:
            logger.error("Failed to download fixture library")
            return False, None

        with open(zip_path, "wb") as file:
            file.write(r.content)
        with zipfile.ZipFile(zip_path) as zip_ref:
            zip_ref.extractall(fixtures_path)
        logger.info("Fixture lib downloaded and installed.")
    return True, fixtures_path