# Gymbuddies

TODO:
 - type hints
 - DATABASE_URL in virtual environment

## Setup
To setup a Python environment for this repository, make sure you have `make`, `python`, and the `virtualenv` Python module installed (e.g. via `python -m pip install virtualenv`). Then, call `make` in the root directory of this repository. This will automatically enter a virtual environment at `./venv` and install the required packages from `requirements.txt`, and it will modify the `activate` script to change the `PYTHONPATH` and `DATABASE_URL` environment variables while the virtual environment is activated. It will also call `pip install -e .` to allow the testing programs to import modules from the `gymbuddies` package.

**NOTE:** For security's sake, the DATABASE_URL is not provided in the repository. You must modify the line `export DATABASE_URL=""` to have the actual external database URL provided by Render. This URL will use `postgres:` as its database type, but `sqlalchemy` only recognizes the prefix `postgresql:`, so you will have to make this change in the Render URL.

The virtual environment can be deactivated with `deactivate`, or reactivated with `. venv/bin/activate`. It may be useful to also change your `PYTHONPATH` upon entering the virtual environment; this can be done by editing `venv/bin/activate`. Append the lines
```sh
...
_OLD_PYTHONPATH="$PYTHONPATH"
export PYTHONPATH="$VIRTUAL_ENV/lib/python3.10/site-packages"
```
to the end of `venv/bin/activate` (excluding the ellipses), and at the beginning of the `deactivate()` function, insert the lines
```sh
deactivate () {
  if [ -n "${_OLD_PYTHONPATH:-}" ] ; then
    PYTHONPATH="${_OLD_PYTHONPATH:-}"
    export PYTHONPATH
    unset _OLD_PYTHONPATH
  fi
  ...
}
```


## Local Deployment
To deploy the web application on your local machine, `cd` into the `gymbuddies` directory and call `flask run`. You can specify the debug option to enable automatic updates when editing the source code, e.g. with `flask --debug run`.

## Linters and Formatters
For this project we'll be using pylint as our linter and yapf as our formatter. These tools should work automatically in your IDE's with the provided `.style.yapf` and `.pylintrc` in the project repository.


## Codebase
### Database API
The database schema (i.e. tables and columns), data classes, and enumerations for particular columns are given in `database/db.py`. The file `db.py` also provides a `session_decorator` decorator that gives any function access to a "session" connected to the database. The required signature and behavior of such functions is detailed in the function documentation of `session_decorator`.
