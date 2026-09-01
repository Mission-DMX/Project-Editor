"""Building Debian (.deb) packages for MissionDMX Editor.

This module orchestrates the complete build process of a DEB package:
It sets up the directory structure, generates control and desktop files,
copies resources, and invokes dpkg-deb to create the final package.
"""

import shutil
import subprocess
from pathlib import Path

from build_control import write_control
from build_desktop import write_desktop
from extract_metadata import load_metadata

BIN = Path("bin/debpkg")
FILE = Path(__file__).parent


def main() -> None:
    """Build a Debian (.deb) package from the PySide6 distribution bundle.

    Performs the following steps:
    1. Loads project metadata from pyproject.toml.
    2. Creates the directory structure for the DEB package.
    3. Generates the DEBIAN/control and .desktop files.
    4. Copies icon, MIME type definition, and application binaries.
    5. Invokes dpkg-deb to build the package.
    6. Renames the package and creates hardlinks for latest/named versions.
    """
    meta = load_metadata()

    shutil.rmtree(BIN, ignore_errors=True)

    (BIN / "DEBIAN").mkdir(parents=True)
    (BIN / "opt/MissionDMX").mkdir(parents=True, exist_ok=True)

    write_control(meta, BIN / "DEBIAN/control")
    shutil.copy(FILE / "debrules.mk", BIN / "DEBIAN/rules")
    icon_path = Path("usr/share/icons/mdmx-editor.png")

    write_desktop(meta, BIN / "usr/share/applications/mission-dmx.desktop", icon_path)

    (BIN / icon_path).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy("submodules/resources/logo.png", BIN / icon_path)

    mime_path = BIN / "usr/share/mime/packages/missiondmx.xml"
    mime_path.mkdir(parents=True, exist_ok=True)
    shutil.copy(FILE / "missiondmx.xml", mime_path)

    (BIN / "usr/local/share/missionDMX").mkdir(parents=True, mode=777, exist_ok=True)
    (BIN / "var/cache/missionDMX").mkdir(parents=True, mode=777, exist_ok=True)

    shutil.copytree(
        "bin/MissionDMX-Editor.dist",
        BIN / "opt/MissionDMX",
        dirs_exist_ok=True,
    )

    subprocess.run(["/usr/bin/dpkg-deb", "--root-owner-group", "--build", str(BIN)], check=True)  # noqa: S603

    package = Path(f"bin/{meta.package_name}.deb")

    shutil.move(
        "bin/debpkg.deb",
        package,
    )

    latest = Path("bin/mission-dmx-editor-latest.deb")
    latest.hardlink_to(package)
    version_deb = Path(f"bin/{meta.package_name}-v{meta.version}.deb")
    version_deb.hardlink_to(package)


if __name__ == "__main__":
    main()
