Convbump
=====
[![Python versions](https://img.shields.io/pypi/pyversions/convbump)](https://pypi.org/project/convbump/)
[![Latest Version](https://img.shields.io/pypi/v/convbump.svg)](https://pypi.org/project/convbump/)
[![BSD License](https://img.shields.io/pypi/l/convbump.svg)](https://github.com/playpauseandstop/convbump/blob/master/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

`convbump` is a simple tool to work with conventional commits.

Use the `version` command to find the next version in your repository
based on the conventional commits.

Use the `changelog` command to generate a nicely formatted changelog
(Github markdown compatible).

## Requirements
`convbump` does not have any external dependencies.

`convbump` uses a pure Python library to access the Git repository and so does not
require a `git` executable.

## Development
The application is written in Python and uses
[Poetry](https://python-poetry.org/docs/) to configure the package and manage
its dependencies.

Make sure you have [Poetry CLI installed](https://python-poetry.org/docs/#installation).
Then you can run

    $ poetry install

which will install the project dependencies (including `dev` dependencies) into a
Python virtual environment managed by Poetry (alternatively, you can activate
your own virtual environment beforehand and Poetry will use that).

### Run tests with pytest

    $ poetry run pytest

or

	$ poetry shell
	$ pytest

`pytest` will take configuration from `pytest.ini` file first (if present), then
from `pyproject.toml`. Add any local configuration to `pytest.ini`.
Configuration in `pyproject.toml` will be used in CI. You can run your
tests the same way as CI to catch any errors

	$ pytest -c pyproject.toml

### Code formatting
The application is formatted using [black](https://black.readthedocs.io/en/stable/) and [isort](https://pycqa.github.io/isort/).  
You can either run black and isort manually or use prepared [Poe](https://github.com/nat-n/poethepoet) task to format the whole project.

	$ poetry run poe format-code
or

	$ poetry shell
	$ poe format-code
