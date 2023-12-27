# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/init.ipynb.

# %% auto 0
__all__ = ['env_file_blank', 'write_env_file', 'read_env_file', 'edit_pythonpath', 'write_edited_pythonpath', 'sciflow_init']

# %% ../nbs/init.ipynb 4
# | export

import os
from pathlib import Path

from fastcore.script import Param, call_parse

from .utils import prepare_env

# %% ../nbs/init.ipynb 7
# | export

env_file_blank = """export USER=
export SCIFLOW_BUCKET=
"""

# %% ../nbs/init.ipynb 9
# | export


def write_env_file(sciflow_dir: Path = None):
    if sciflow_dir is None:
        sciflow_dir = Path("~/.sciflow").expanduser()
    env_path = Path(sciflow_dir, "env").resolve()
    if not env_path.exists():
        if not sciflow_dir.exists():
            os.mkdir(sciflow_dir)
        with open(env_path, "w") as env_file:
            env_file.write(env_file_blank)
        print(f"Wrote new SciFlow environment file to: {env_path}")
    else:
        print(f"Skipping SciFlow environment file creation - already exists")

# %% ../nbs/init.ipynb 12
# | export


def read_env_file(sciflow_dir: Path = None):
    if sciflow_dir is None:
        sciflow_dir = Path("~/.sciflow").expanduser()
    env_path = Path(sciflow_dir, "env").resolve()
    try:
        with open(env_path, "r") as env_file:
            lines = env_file.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(
            "The Sciflow environment file is missing - have you run sciflow_init?"
        )
    return lines

# %% ../nbs/init.ipynb 16
# | export


def edit_pythonpath(env_lines, dir_to_add: Path):
    dir_str = str(dir_to_add.resolve())
    existing_ppath = [p for p in env_lines if p.find("PYTHONPATH") > -1]

    if len(existing_ppath) == 0:
        new_line = f"export PYTHONPATH=$PYTHONPATH:{dir_str}\n"
        env_lines.append(new_line)
        new_text = "".join(env_lines)
    elif len(existing_ppath) == 1:
        prev_line = existing_ppath[0]
        if prev_line.find(dir_str) == -1:
            new_line = existing_ppath[0].replace(
                "$PYTHONPATH:", f"$PYTHONPATH:{dir_str}:"
            )
            new_text = "".join(env_lines).replace(prev_line, new_line)
        else:
            new_text = "".join(env_lines)
    else:
        raise ValueError(
            "Env file is malformed - only 1 PYTHONPATH entry should be present"
        )
    return new_text

# %% ../nbs/init.ipynb 21
# | export


def write_edited_pythonpath(project_root: Path, sciflow_dir: Path = None):
    if sciflow_dir is None:
        sciflow_dir = Path("~/.sciflow").expanduser()
    env_path = Path(sciflow_dir, "env").resolve()
    env_lines = read_env_file(sciflow_dir)
    new_text = edit_pythonpath(env_lines, project_root)
    with open(env_path, "w") as env_file:
        env_file.write(new_text)

# %% ../nbs/init.ipynb 27
# | export


@call_parse
def sciflow_init(
    project_root: Param("The root directory of the project", Path) = None,
    sciflow_dir: Param("The sciflow env directory", Path) = None,
):
    if project_root is None:
        project_root = Path(".").resolve()
    # TODO - Get latest templates files from web - if has internet connection

    # Create sciflow env file if it doesn't exist
    write_env_file(sciflow_dir)

    # Add project root to PYTHONPATH environment variable
    write_edited_pythonpath(project_root, sciflow_dir)

    prepare_env()
