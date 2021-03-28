# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/params.ipynb (unless otherwise specified).

__all__ = ['find_params_cell', 'extract_params', 'DEFAULT_PARAMS_CELL', 'add_missing_params_cell',
           'extract_params_to_file', 'list_mod_files', 'extract_as_files', 'extract_params_as_dict', 'params_as_dict']

# Cell

from io import StringIO
from pathlib import Path
from typing import Iterable

import nbformat
from nbdev.export import Config, find_default_export, nbglob, read_nb
from nbformat.notebooknode import NotebookNode

# Cell


def find_params_cell(nb: NotebookNode):
    params_cell = [c for c in nb["cells"] if c["metadata"] == {"tags": ["parameters"]}]
    return params_cell

# Cell


def extract_params(nb: NotebookNode):
    params_cell = find_params_cell(nb)
    return params_cell[0]["source"] if len(params_cell) > 0 else None

# Cell

DEFAULT_PARAMS_CELL = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {"tags": ["parameters"]},
    "outputs": [],
    "source": "# parameters\n",
}

# Cell


def add_missing_params_cell(nb_path: Path, persist: bool = True):
    nb = read_nb(nb_path)
    if len(find_params_cell(nb)) > 0:
        print(f"Skipping {nb_path} already has parameters cell")
        return
    nb["cells"].insert(0, nbformat.from_dict(DEFAULT_PARAMS_CELL))
    if persist:
        nbformat.write(nb, nb_path)
    return nb

# Cell


def extract_params_to_file(nb_path: Path, params_file_path: Path):
    params_code = extract_params(read_nb(Path(test_nb)))
    with open(params_file_path, "w") as params_file:
        params_file.writelines(params_code)

# Cell


def list_mod_files(files):
    modules = []
    for f in files:
        fname = Path(f)
        nb = read_nb(fname)
        default = find_default_export(nb["cells"])
        if default is not None:
            default = os.path.sep.join(default.split("."))
            modules.append(default)
    return modules

# Cell


def extract_as_files(suffix="_params.py"):
    nbs = nbglob(recursive=True)
    param_files = list_mod_files(nbs)
    params_files = [
        Path(os.path.join(Config().path("lib_path"), pf + suffix)) for pf in param_files
    ]
    for nb_path, pf_path in zip(nbs, params_files):
        extract_params_to_file(nb_path, pf_path)

# Internal Cell


def _lines_to_dict(lines: Iterable[str]):
    result = {}
    for line in lines:
        if line.startswith("#") or not "=" in line:
            continue
        (key, val) = line.split("=")
        result[key.strip()] = val.strip('\n "')
    return result

# Cell


def extract_params_as_dict(params_file_path: Path):
    params = {}
    with open(params_file_path, "r") as params_file:
        params = _lines_to_dict(params_file.readlines())
    return params

# Cell


def params_as_dict(nb_path: Path):
    params_code = extract_params(read_nb(nb_path))
    params = _lines_to_dict(StringIO(params_code).readlines())
    return params