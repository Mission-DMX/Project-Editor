import platform
from pathlib import Path

from extract_metadata import Metadata


def write_control(metadata: Metadata, target: Path) -> None:
    content = f"""Package: {metadata.package_name}
Version: {metadata.version}
Section: multimedia
Priority: optional
Architecture: {platform.machine()}
Maintainer: {metadata.maintainer}
Homepage: {metadata.homepage}
Depends: libsdl2-2.0-0 (>=2.0.0), libsdl2-image-2.0-0
Description: {metadata.description}
"""

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
