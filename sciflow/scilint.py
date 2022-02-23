# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/scilint.ipynb (unless otherwise specified).

__all__ = ['run_nbqa_cmd', 'sciflow_tidy', 'get_function_defs', 'count_func_calls', 'calc_tpf', 'tpf', 'something',
           'nb_cell_code', 'ifp', 'mcr', 'tcl']

# Cell

import ast
import os
from collections import Counter
from pathlib import Path

import nbformat
from fastcore.script import call_parse
from nbdev.export import read_nb
from nbqa.__main__ import _get_configs, _main
from nbqa.cmdline import CLIArgs
from nbqa.find_root import find_project_root
from .utils import load_nb_module

# Cell


def run_nbqa_cmd(cmd):
    print(f"Running {cmd}")
    project_root: Path = find_project_root(tuple([str(Path(".").resolve())]))
    args = CLIArgs.parse_args([cmd, str(project_root)])
    configs = _get_configs(args, project_root)
    output_code = _main(args, configs)
    return output_code

# Cell


@call_parse
def sciflow_tidy():
    "Run notebook formatting and tidy utilities. \
    These tools should be configured to run automatically without intervention."
    tidy_tools = ["black", "isort", "autoflake"]
    [run_nbqa_cmd(c) for c in tidy_tools]

# Cell


def get_function_defs(code):
    func_names = []
    for stmt in ast.walk(ast.parse(code)):
        if isinstance(stmt, ast.FunctionDef) and not stmt.name.startswith("_"):
            func_names.append(stmt.name)
    return func_names

# Cell


def count_func_calls(code, func_defs):
    func_calls = Counter({k: 0 for k in func_defs})
    for stmt in ast.walk(ast.parse(code)):
        if isinstance(stmt, ast.Call):
            func_name = stmt.func.id if "id" in stmt.func.__dict__ else stmt.func.attr
            if func_name in func_defs:
                if func_name in func_calls:
                    func_calls[func_name] += 1
    return func_calls

# Cell


def calc_tpf(num_tests, num_funcs):
    return 0 if num_funcs == 0 else num_tests / num_funcs

# Cell


def tpf(nb_path):
    nb, module_code = load_nb_module(nb_path)
    pnb = nbformat.from_dict(nb)
    nb_cell_code = "\n".join(
        [c["source"].replace("%", "#") for c in pnb.cells if c["cell_type"] == "code"]
    )
    func_defs = get_function_defs(module_code)
    func_calls = count_func_calls(nb_cell_code, func_defs)
    num_funcs = len(func_calls.keys())
    num_tests = sum(func_calls.values())
    print(num_tests, num_funcs)
    return calc_tpf(num_tests, num_funcs)

# Cell
nb_cell_code = """
def something():
    pass; pass
#load_ext autoreload
#autoreload 2
# export


import numpy as np
import pandas as pd
from .utils import lib_path, odbc_connect, query
pd.set_option("display.max_colwidth", 800)
# export
"""

# Cell


def ifp(nb_path):
    nb = read_nb(nb_path)
    nb_cell_code = "\n".join(
        [c["source"].replace("%", "#") for c in nb.cells if c["cell_type"] == "code"]
    )
    stmts_in_func = 0
    stmts_outside_func = 0
    for stmt in ast.walk(ast.parse(nb_cell_code)):
        if isinstance(stmt, ast.FunctionDef) and not stmt.name.startswith("_"):
            for body_item in stmt.body:
                stmts_in_func += 1
        else:
            stmts_outside_func += 1
    return (
        0
        if stmts_outside_func + stmts_in_func == 0
        else stmts_in_func / (stmts_outside_func + stmts_in_func)
    )

# Cell


def mcr(nb_path):
    nb = read_nb(nb_path)
    md_cells = [c for c in nb.cells if c["cell_type"] == "markdown"]
    code_cells = [c for c in nb.cells if c["cell_type"] == "code"]
    num_code_cells = len(code_cells)
    num_md_cells = len(md_cells)
    return 0 if num_code_cells == 0 else num_md_cells / num_code_cells

# Cell


def tcl(nb_path):
    nb = read_nb(nb_path)
    return sum([len(c["source"]) for c in nb.cells if c["cell_type"] == "code"])