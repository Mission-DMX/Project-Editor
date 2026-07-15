"""Metadata extraction from pyproject.toml.

This module provides the Metadata class and the load_metadata function
to read project information such as name, version, and maintainer from
the pyproject.toml and make it available for build scripts.
"""

import tomllib
from pathlib import Path

from pydantic import BaseModel


class Metadata(BaseModel):
    """Represents the project metadata extracted from pyproject.toml.

    Attributes:
        package_name: The package name (lowercased, spaces replaced with hyphens).
        version: The project version.
        display_name: The human-readable display name of the project.
        description: A short description of the project.
        maintainer: The project maintainer with email address.
        homepage: The homepage URL of the project.
    """

    package_name: str
    version: str
    display_name: str
    description: str
    maintainer: str
    homepage: str


def load_metadata() -> Metadata:
    """Loads project metadata from the pyproject.toml file.

    Reads the pyproject.toml in the project root directory and extracts
    the relevant fields from the [project] section to create a Metadata object.

    Returns:
        Metadata: An object containing the extracted project metadata.

    Raises:
        FileNotFoundError: If the pyproject.toml is not found.
        KeyError: If expected fields are missing in the pyproject.toml.
    """
    with Path("pyproject.toml").open("rb") as f:
        pyproject = tomllib.load(f)

    project = pyproject["project"]

    return Metadata(
        package_name=project["name"].replace(" ", "-").lower(),
        version=project["version"],
        display_name=project["name"],
        description=project["description"],
        maintainer=project["authors"][0]["name"] + " <" + project["authors"][0]["email"] + ">",
        homepage=project["urls"]["homepage"],
    )
