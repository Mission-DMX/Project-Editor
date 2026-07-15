"""Generation of the .desktop file for Linux desktop integration.

This module creates a Desktop Entry Specification file that registers
the application in the Linux desktop environment.
"""

from pathlib import Path

from extract_metadata import Metadata


def write_desktop(metadata: Metadata, target: Path, icon_path: Path) -> None:
    """Creates a .desktop file for Linux desktop integration.
    Args:
        metadata: The project metadata.
        target: The file path where the .desktop file will be written.
        icon_path: The relative path to the application icon within the package.
    """
    content = f"""[Desktop Entry]
Version={metadata.version}
Type=Application
Name={metadata.display_name}
GenericName=Light Console Show File Editor
Comment={metadata.description}
Icon={icon_path}
Categories=Graphics
MimeType=application/x-mdmx-showfile
Terminal=false
Exec=/opt/MissionDMX/editor %f
StartupNotify=true
"""

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
