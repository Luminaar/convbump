# ConvBump

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Latest Version](https://img.shields.io/pypi/v/convbump.svg)](https://pypi.org/project/convbump/)
[![BSD License](https://img.shields.io/pypi/l/convbump.svg)](https://github.com/playpauseandstop/convbump/blob/master/LICENSE)

A simple tool that reads Git history and returns the next version and changelog
based on conventional commits.


## Attribution
This project is forked from [Badabump created by Igor Davydenko](https://github.com/playpauseandstop/badabump).

## Notice
This project is a heavily modified fork that solves our specific needs. We
discourage anyone from using it and we will offer no support to anyone. Checkout
[Badabump](https://github.com/playpauseandstop/badabump) for a more general
tool.

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
Configuration in `pyproject.toml` will be used in Teamcity. You can run your
tests the same way as Teamcity to catch any errors

	$ pytest -c pyproject.toml

### Code formatting
The application is formatted using [black](https://black.readthedocs.io/en/stable/) and [isort](https://pycqa.github.io/isort/).
You can either run black and isort manually or use prepared [Poe](https://github.com/nat-n/poethepoet) task to format the whole project.

	$ poetry run poe format_code
or

	$ poetry shell
	$ poe format_code
