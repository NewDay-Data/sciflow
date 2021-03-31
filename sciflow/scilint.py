# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/scilint.ipynb (unless otherwise specified).

__all__ = ['run_nbqa_cmd', 'sciflow_tidy']

# Cell

from pathlib import Path

from fastcore.script import call_parse
from nbqa.__main__ import _get_configs, _run_on_one_root_dir
from nbqa.cmdline import CLIArgs
from nbqa.find_root import find_project_root

# Cell


def run_nbqa_cmd(cmd):
    print(f"Running {cmd}")
    project_root: Path = find_project_root(tuple([str(Path(".").resolve())]))
    args = CLIArgs.parse_args([cmd, str(project_root)])
    configs = _get_configs(args, project_root)
    output_code = _run_on_one_root_dir(args, configs, project_root)
    return output_code

# Cell


@call_parse
def sciflow_tidy():
    "Run notebook formatting and tidy utilities. \
    These tools should be configured to run automatically without intervention."
    tidy_tools = ["black", "isort", "autoflake"]
    [run_nbqa_cmd(c) for c in tidy_tools]