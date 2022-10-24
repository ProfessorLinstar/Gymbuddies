# Gymbuddies

## Setup
To setup a Python environment for this repository, make sure you have `make`, `python`, and the `virtualenv` Python module installed (e.g. via `python -m pip install virtualenv`). Then, call `make` in the root directory of this repository. (Note: For MacOS users, make sure that the PYTHON variable in makefile is set to python3. This is because python in MacOS defaults to python2 and will cause make to fail). This will automatically enter a virtual environment at `./venv` and install the required packages from `requirements.txt`, and it will modify the `activate` script to change the `PYTHONPATH` and `DATABASE_URL` environment variables while the virtual environment is activated. It will also call `pip install -e .` to allow the testing programs to import modules from the `gymbuddies` package. Once the make installation is complete, you can use `. venv/bin/activate` to enter the project virtual environment.

**NOTE:** For security's sake, the DATABASE_URL is not provided in the repository. You must modify the line `DATABASE_URL=""` in `venv/bin/activate` to have the actual external database URL provided by Render. To find this URL, login to the Gymbuddies Render account and click on the Gymbuddies Postgres database in the dashboard. Use the "External Database URL" provided in the "Connections section." This URL will use `postgres:` as its database type, but `sqlalchemy` only recognizes the prefix `postgresql:`, so you will have to make this change in the Render URL.


#### Local Deployment
To deploy the web application on your local machine, call `flask --app gymbuddies run` in the root directory of the repository. You can specify the debug option to enable automatic updates when editing the source code, e.g. with `flask --app gymbuddies --debug run`. When importing certain modules, you may encounter the error "attempted relative import with no known parent package" (e.g. calling `import debug` within the `gymbuddies/database` directory). To prevent this issue from occurring, specify the required parent package in the import (e.g. rather than `import debug`, use `from database import debug` or `import databse.debug`).


## Codebase
#### Project Structure
The current structure of the main project directory is as follows:
```
gymbuddies                           --- Flask application root directory
├── __init__.py                      --- Provides Flask application initialization function
├── auth.py                          --- Authentication routing
├── master.py                        --- Master debugging page routing
├── database                         --- 
│   ├── db.py                        --- Database schema and data structures
│   ├── debug.py                     --- Database debugging and diagnostics tools
│   ├── initialize.py                --- Database creation script
│   ├── request.py                   --- Requests API
│   ├── schedule.py                  --- Scheduling API
│   └── user.py                      --- Users API
├── static                           --- 
│   └── styles.css                   --- 
└── templates                        --- 
    ├── index.html                   --- 
    ├── layout.html                  --- Basic skeleton page template
    ├── login.html                   --- 
    └── master.html                  --- Master debugging page template
```
The root directory of the repository contains various python configuration and environment setup files.


#### Database API
The database schema (i.e. tables and columns), data classes, and enumerations for particular columns are given in `database/db.py`. The file `db.py` also provides a `session_decorator` decorator that gives any function access to a "session" connected to the database. The required signature and behavior of such functions is detailed in the function documentation of `session_decorator`.


#### Formatting
Note: remember to configure your IDE settings such that you are indenting with 4 spaces, and not tabs.

For this project we'll be using pylint as our linter and yapf as our formatter. If you have these tools installed, then they should work automatically in your IDE's with the provided `.style.yapf` and `.pylintrc` in the project repository.
