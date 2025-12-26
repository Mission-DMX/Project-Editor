# Project-Editor
This software is responsible for creating and editing project files for the DMX console

Binäre Abhängigkeiten:
* libsdl2-dev

The following tools need to be in PATH for the editor to work properly:
 * `pactl` (Pulse Audio control)
 * `swaymsg` (In order to let the editor direct its windows)

## Dev
For dev use pdm as package manager:
```
pip install pdm
pdm install --dev
```
## CI Tests
This software is checked using continious integration. Having the following in your `pre-commit` hook
may help you passing those tests:
```
isort $(git rev-parse --show-toplevel)/src
pylint --fail-under=9 $(git diff --name-only --cached | grep '.py') || exit 1
```

## Installation
The following directories must exist and be writable by the executing user:
 * `/usr/local/share/missionDMX` This directory contains global assets collected by the user to be reusable across
   different show files.
 * `/var/cache/missionDMX` This directory contains downloaded fixture definitions