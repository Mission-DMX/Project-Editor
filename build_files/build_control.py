"""Generation of the DEBIAN/control file for Debian packages.

This module writes the control block of a Debian package,
including package name, version, architecture, dependencies, and description.
"""

import platform
from pathlib import Path

from extract_metadata import Metadata

HOST_ARCH = {
    "x86_64": "amd64",
    "aarch64": "arm64",
    "armv7l": "armhf",
}.get(platform.machine(), platform.machine())
"""Mapping of host architecture to dpkg architecture identifiers.

For unknown architectures, the raw value from platform.machine() is used.
"""


def write_control(metadata: Metadata, target: Path) -> None:
    """Writes a DEBIAN/control file for the Debian package.

    Generates the control block with package name, version, architecture,
    maintainer, dependencies, and description, then writes it to the target file.

    Args:
        metadata: The project metadata.
        target: The file path where the control file will be written.
    """
    content = f"""Package: {metadata.package_name}
Version: {metadata.version}
Section: multimedia
Priority: optional
Architecture: {HOST_ARCH}
Maintainer: {metadata.maintainer}
Homepage: {metadata.homepage}
Depends: libsdl2-2.0-0 (>=2.0.0), libsdl2-image-2.0-0
Description: {metadata.description}
"""

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
