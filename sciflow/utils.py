# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/utils.ipynb (unless otherwise specified).

__all__ = ['lib_path', 'prepare_env', 'odbc_connect', 'query']

# Cell

import os
from pathlib import Path

import pandas as pd
import pyodbc
from nbqa.find_root import find_project_root

# Cell


def lib_path(*lib_relative_path):
    lib_root_path = find_project_root(srcs=(str(Path(".").resolve()),))
    return Path(os.path.join(lib_root_path, *lib_relative_path))

# Cell


def prepare_env(env_file_path: str = None):
    if env_file_path is None:
        env_file_path = os.path.expanduser("~/.sciflow/env")
    # TODO create this for user
    if not os.path.exists(env_file_path):
        raise EnvironmentError(
            f"You need to create a Sciflow environment vars file at: {env_file_path}"
        )
    with (open(env_file_path, "r")) as env_file:
        for line in env_file.readlines():
            key, value = line.strip().split("=", 1)
            os.environ[key.replace("export ", "")] = value

# Cell


def odbc_connect(env_file_path: str = None):
    required_vars = ("ODBC_DRIVER", "ODBC_HOST", "ODBC_PORT", "ODBC_USER", "ODBC_PWD")
    if not all([v in os.environ for v in required_vars]):
        prepare_env(env_file_path)
    connection = pyodbc.connect(
        """Driver={};
           ConnectionType=Direct;
           HOST={};
           PORT={};
           AuthenticationType=Plain;
           UID={};
           PWD={};
           SSL=1;
           TrustedCerts={}""".format(
            os.environ["ODBC_DRIVER"],
            os.environ["ODBC_HOST"],
            os.environ["ODBC_PORT"],
            os.environ["ODBC_USER"],
            os.environ["ODBC_PWD"],
            os.environ["SSL_CERTS"],
        ),
        autocommit=True,
    )
    return connection

# Cell


def query(conn, sql):
    with conn.cursor() as cursor:
        df = pd.read_sql(sql, conn)
    return df