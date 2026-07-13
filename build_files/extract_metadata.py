import tomllib
from pathlib import Path

from pydantic import BaseModel


class Metadata(BaseModel):
    package_name: str
    version: str
    display_name: str
    description: str
    maintainer: str
    homepage: str


def load_metadata() -> Metadata:
    with Path("pyproject.toml").open("rb") as f:
        pyproject = tomllib.load(f)

    project = pyproject["project"]

    return Metadata(
        package_name=project["name"].replace(" ", "_").lower(),
        version=project["version"],
        display_name=project["name"],
        description=project["description"],
        maintainer=project["authors"][0]["name"] + " <" + project["authors"][0]["email"] + ">",
        homepage=project["urls"]["homepage"],
    )
