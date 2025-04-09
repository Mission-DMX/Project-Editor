# Project-Editor
This software is responsible for creating and editing project files for the DMX console

Binäre Abhängigkeiten:
* libsdl2-dev

## CI Tests
This software is checked using continious integration. Having the following in your `pre-commit` hook
may help you passing those tests:
```
isort $(git rev-parse --show-toplevel)/src
pylint --fail-under=9 $(git diff --name-only --cached | grep '.py') || exit 1
```
