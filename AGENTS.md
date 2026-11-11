# Repository Guidelines

## Project Structure & Module Organization

This repository is a Google Earth Engine experimentation lab. Work lives under `src/lab/`:

- `base/` contains reusable analysis code (`repository_ee.py`), classification notebooks, and benchmark notes.
- `tutorial/` groups exploratory notebooks by topic, such as `class-tutorial/` and `fire-view/`.
- `assets/` is reserved for local supporting resources.

Keep reusable Earth Engine operations in Python modules and use notebooks for experiments, visualization, and narrative analysis. Do not commit generated caches or notebook checkpoints; existing `__pycache__` and `.ipynb_checkpoints` entries are legacy artifacts, not examples to follow.

## Build, Test, and Development Commands

No build system or dependency manifest is currently defined. Use an isolated Python environment and install the notebook stack needed by the work, typically Earth Engine, geemap, and Jupyter.

```bash
jupyter lab src/lab
python -m compileall src/lab/base/repository_ee.py
git diff --check
```

`jupyter lab` opens the experiments locally. `compileall` performs a basic syntax check on the shared module. `git diff --check` detects whitespace errors before submission. Authenticate Earth Engine through `ee.Authenticate()` and initialize it with the appropriate Google Cloud project.

## Coding Style & Naming Conventions

Use four-space indentation, type hints, and concise docstrings for Python. Follow PEP 8: `snake_case` for functions and variables, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants. Keep Earth Engine computations server-side; call `getInfo()` only for small inspection results. Name notebooks descriptively with lowercase kebab-case, and add version suffixes only when comparing deliberate iterations, for example `classification-v2.ipynb`.

## Testing Guidelines

There is no automated test suite or coverage requirement yet. Before opening a pull request, restart and run changed notebooks from top to bottom, verify Earth Engine authentication and asset access, and syntax-check edited Python modules. If tests are introduced, place them in `tests/` and name files `test_<module>.py`.

## Commit & Pull Request Guidelines

History uses short, imperative-style commit subjects, such as `add init lab ee repository`. Keep each commit focused and describe the observable change. Pull requests should summarize the purpose, list changed notebooks or modules, document required Earth Engine projects/assets, and report validation performed. Include screenshots for material map or chart changes and link the relevant issue when one exists. Never commit credentials, service-account keys, or private asset exports.
