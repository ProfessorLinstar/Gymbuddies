# Gymbuddies

## Setup
To setup a Python environment for this repository, make sure you have `make`, `python`, and the `virtualenv` Python module installed (e.g. via `python -m pip install virtualenv`). Then, call `make` in the root directory of this repository. This will automatically enter a virtual environment at `./venv` and install the required packages from `requirements.txt`. It will also call `pip install -e .` to allow the testing programs to import modules from the `gymbuddies` package.

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
