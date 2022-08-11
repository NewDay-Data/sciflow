# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/utils.ipynb (unless otherwise specified).

__all__ = ['run_shell_cmd', 'indent_multiline', 'titleize', 'chunks', 'lib_path', 'load_nb', 'load_nb_module',
           'prepare_env', 'odbc_connect', 'query', 'get_module_name', 'get_flow_path']

# Cell

import _ast
import ast
import os
import subprocess
from pathlib import Path

import nbformat
import pandas as pd
import pyodbc
from nbdev.export import find_default_export, get_config, read_nb
from nbqa.find_root import find_project_root

# Cell


def run_shell_cmd(script: str):
    pipe = subprocess.Popen(
        "%s" % script, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True
    )
    output = pipe.communicate()[0]
    return pipe, output.decode("utf-8").strip()

# Cell


def indent_multiline(multiline_text, indent=1):
    lines = multiline_text.strip().split("\n")
    spaces = "".join(["    " for _ in range(indent)])
    for i in range(len(lines)):
        prefix = spaces if i > 0 else spaces + '"""'
        lines[i] = prefix + lines[i]
    return "\n".join(lines) + '"""'

# Cell


def titleize(name):
    return name.title().replace("_", "")

# Cell


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]

# Cell


def lib_path(*lib_relative_path):
    lib_root_path = find_project_root(srcs=(str(Path(".").resolve()),))
    return Path(os.path.join(lib_root_path, *lib_relative_path))

# Cell


def load_nb(nb_path):
    nb = read_nb(nb_path)
    default_export = find_default_export(nb["cells"])
    if default_export is None:
        raise ValueError(f"{nb_path.name} does not contain an associated nbdev module")

    module_name = default_export.replace(".", "/")
    module_path = os.path.join(get_config().path("lib_path"), f"{module_name}.py")
    return nb, module_path

# Cell


def load_nb_module(nb_path):
    nb, module_path = load_nb(nb_path)
    with open(module_path, "r") as module_file:
        lines = module_file.readlines()
    module_code = "\n".join(lines)
    return nb, module_code

# Cell


def prepare_env(env_file_path: str = None):
    if env_file_path is None:
        env_file_path = os.path.expanduser("~/.sciflow/env")
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

# Cell


def get_module_name(nb_path):
    nb = read_nb(nb_path)
    module_name = find_default_export(nb["cells"])
    return module_name

# Cell


def get_flow_path(nb_path, config=None, flow_provider="metaflow"):
    module_name = get_module_name(nb_path)
    if module_name is None:
        return None
    if config is None:
        config = get_config()
    flows_dir = Path(config.path("flows_path"), flow_provider)
    if not flows_dir.exists():
        flows_dir.mkdir()

    return Path(flows_dir, f"{module_name.split('.')[-1]}.py")