from pathlib import Path

from extract_metadata import Metadata


def write_desktop(metadata: Metadata, target: Path, icon_path: Path) -> None:
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
