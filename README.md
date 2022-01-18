Convbump
=====

Tool for Conventional Commits

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

	$ poetry run poe format-code
or

	$ poetry shell
	$ poe format-code
