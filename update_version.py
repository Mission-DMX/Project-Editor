# coding=utf-8
"""Update Version in GitHub action"""
import sys

import tomlkit

# Load pyproject.toml
with open('pyproject.toml', 'r', encoding="UTF-8") as f:
    data = tomlkit.load(f)

# Get current version and split into parts
version = data['project']['version']
major, minor, patch = map(int, version.split('.'))

if len(sys.argv[1]) > 1 and sys.argv[1] == "info":
    print(f'{major}.{minor}.{patch}')
else:
    new_version = f'{major}.{minor}.{patch + 1}'

    # Update the version in the TOML file
    data['project']['version'] = new_version
    with open('pyproject.toml', 'w', encoding="UTF-8") as f:
        tomlkit.dump(data, f)

    print(f'v{new_version}')
