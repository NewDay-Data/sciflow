# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/packaging.ipynb.

# %% auto 0
__all__ = ['reqs_lines_to_sep_str', 'reqs_file_to_sep_str', 'determine_dependencies', 'update_requirements',
           'create_conda_meta_file', 'sciflow_update_reqs', 'delete_multiple_element', 'read_deploy_vars',
           'write_art_conda_envs_to_file', 'sciflow_prepare']

# %% ../nbs/packaging.ipynb 3
# | export

import os
import subprocess
import sys
from configparser import ConfigParser
from pathlib import Path
from typing import List
from urllib.parse import urlparse

import yaml
from fastcore.script import call_parse
from nbdev.export import get_config
from .utils import run_py_module

# %% ../nbs/packaging.ipynb 9
# | export


def reqs_lines_to_sep_str(req_lines: List[str], sep: str = " "):
    return " ".join(
        [
            l.replace(" ", "").strip()
            for l in req_lines
            if not l.startswith("#") and len(l.strip()) > 0
        ]
    )

# %% ../nbs/packaging.ipynb 12
# | export


def reqs_file_to_sep_str(pip_reqs_path: Path) -> str:
    with open(pip_reqs_path, "r") as pip_reqs_file:
        lines = pip_reqs_file.readlines()
    return reqs_lines_to_sep_str(lines)

# %% ../nbs/packaging.ipynb 15
# | export


def determine_dependencies(
    out_dir: Path = None, generated_pip_file_name: str = "requirements-generated.txt"
):
    try:
        import pigar
    except:
        print("Pigar dependency is not installed - not able to determine dependencies")
        return
    lib_path = get_config().path("lib_path")
    if out_dir is None:
        out_dir = lib_path.resolve().parent

    command = "pigar"
    args = ["generate", "-f", str(Path(out_dir, generated_pip_file_name))]

    run_py_module(command, args)

    return reqs_file_to_sep_str(os.path.join(out_dir, generated_pip_file_name))

# %% ../nbs/packaging.ipynb 21
# | export


def update_requirements(
    project_dir: Path = None, output_filename: str = "settings.ini"
):
    if project_dir is None:
        lib_path = get_config().path("lib_path")
        project_dir = lib_path.resolve().parent

    config = ConfigParser(delimiters=["="])
    settings_path = os.path.join(project_dir, "settings.ini")
    config.read(settings_path)

    os.path.join(project_dir, "requirements-generated.txt")
    reqs_str = determine_dependencies(out_dir=project_dir)

    out_path = os.path.join(project_dir, output_filename)
    config.set("DEFAULT", "requirements", reqs_str)

    with open(out_path, "w") as configfile:
        config.write(configfile)

# %% ../nbs/packaging.ipynb 27
# | export


def create_conda_meta_file(project_dir: Path = None, out_file: str = "meta.yaml"):
    if project_dir is None:
        lib_path = get_config().path("lib_path")
        project_dir = lib_path.resolve().parent

    meta_data = {
        "package": {
            "name": get_config().get("lib_name"),
            "version": get_config().get("version"),
        },
        "source": {"path": str(get_config().path("lib_path").resolve().parent)},
        "requirements": {
            "host": ["pip", "python", "setuptools"],
            "run": determine_dependencies(out_dir=project_dir).split(" "),
        },
    }
    with open(os.path.join(project_dir, out_file), "w") as conda_build_file:
        yaml.dump(meta_data, conda_build_file)

# %% ../nbs/packaging.ipynb 30
# | export


@call_parse
def sciflow_update_reqs():
    create_conda_meta_file()
    update_requirements()
    print("Updated library requirements for conda & nbdev")

# %% ../nbs/packaging.ipynb 33
# | export


def delete_multiple_element(list_object, indices):
    indices = sorted(indices, reverse=True)
    for idx in indices:
        if idx < len(list_object):
            list_object.pop(idx)

# %% ../nbs/packaging.ipynb 34
# | export


def read_deploy_vars():
    with open(os.path.join(Path.home(), ".condarc"), "r") as conda_rc_file:
        conda_rc = yaml.load(conda_rc_file, Loader=yaml.FullLoader)
        conda_url = conda_rc["channels"][0]
    deployment = {
        "conda_url": conda_url,
        "artifactory_user": urlparse(conda_url).netloc.split(":")[0],
        "artifactory_token": urlparse(conda_url).netloc.split(":")[1].split("@")[0],
        "artifactory_url": urlparse(conda_url).netloc.split(":")[1].split("@")[1],
        "artifactory_conda_channel": "conda-local",
        "lib_name": get_config().get("lib_name"),
        "version": get_config().get("version"),
        "build_number": 0,
    }
    return deployment

# %% ../nbs/packaging.ipynb 36
# | export


def write_art_conda_envs_to_file():
    dep_vars = read_deploy_vars()

    with open(os.path.join(Path.home(), ".profile"), "r") as profile_file:
        existing_lines = profile_file.readlines()
        to_remove = []
        for i, line in enumerate(existing_lines):
            if (
                line.strip().startswith("export ARTIFACTORY_")
                or line.strip().startswith("export LIB_NAME")
                or line.strip().startswith("export VERSION")
                or line.strip().startswith("export BUILD_NUMBER")
            ):
                to_remove.append(i)
            if not line.endswith("\n"):
                existing_lines[i] = line + "\n"
        delete_multiple_element(existing_lines, to_remove)

    with open(os.path.join(Path.home(), ".profile"), "w") as profile_file:
        new_lines = [
            "export ARTIFACTORY_USER={artifactory_user}\n".format(**dep_vars),
            "export ARTIFACTORY_PASSWORD={artifactory_token}\n".format(**dep_vars),
            "export ARTIFACTORY_URL={artifactory_url}\n".format(**dep_vars),
            "export ARTIFACTORY_CONDA_CHANNEL={artifactory_conda_channel}\n".format(
                **dep_vars
            ),
            "export LIB_NAME={lib_name}\n".format(**dep_vars),
            "export VERSION={version}\n".format(**dep_vars),
            "export BUILD_NUMBER={build_number}\n".format(**dep_vars),
        ]
        existing_lines.extend(new_lines)
        profile_file.writelines(existing_lines)
    return existing_lines

# %% ../nbs/packaging.ipynb 39
# | export


@call_parse
def sciflow_prepare():
    dep_vars = read_deploy_vars()

    for dep_key in dep_vars.keys():
        os.environ[dep_key.upper()] = str(dep_vars[dep_key])
