# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/parse_module.ipynb (unless otherwise specified).

__all__ = ['extract_step_code', 'FuncLister', 'FuncDetails', 'pp', 'extract_return_stmt', 'parse_step',
           'extract_return_var_names', 'extract_steps', 'extract_dag']

# Cell

import ast
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import networkx as nx
import pandas as pd
from nbdev.export import get_config

# Cell


def extract_step_code(
    module_path: Path,
    export_comments=("# cell", "# internal cell", "# comes from"),
    remove_comment_lines=True,
):
    with open(module_path, "r") as module_file:
        lines = module_file.readlines()
    lines = pd.Series(lines)
    step_code = {}
    active_step = None
    for l in lines.tolist():
        if l.lower().startswith("# step"):
            active_step = l.split(":")[1].strip()
        elif l.lower().startswith(export_comments):
            active_step = None
        if l.startswith("#") and remove_comment_lines:
            continue
        if active_step:
            if not active_step in step_code:
                step_code[active_step] = []
            step_code[active_step].append(l)
    for key in step_code.keys():
        step_code[key] = "".join(step_code[key])
    return step_code

# Cell


class FuncLister(ast.NodeVisitor):
    has_return = False

    def visit_Return(self, node):
        self.has_return = True

    def visit_FunctionDef(self, node):
        self.name = node.name
        self.docstring = ast.get_docstring(node)
        self.args = node.args.args
        self.arg_names = [a.arg for a in node.args.args]
        self.generic_visit(node)


import pprint

pp = pprint.PrettyPrinter(indent=4, width=120, compact=True)


@dataclass
class FuncDetails:
    name: str
    docstring: str
    args: str
    has_return: bool
    return_stmt: str
    code: str

    def __repr__(self):
        return pp.pformat(
            f"FuncDetails(name={self.name},args={self.args},has_return={self.has_return}):\n{self.code.strip()}"
        )

# Cell


def extract_return_stmt(func_name, code):
    return_stmt = [
        l.strip().split("return")[1].strip()
        for l in code.splitlines()
        if l.strip().startswith("return")
    ]
    if len(return_stmt) == 0:
        return
    return_stmt = return_stmt[0]
    is_named_variable = bool(re.search("^[a-zA-Z]+[a-zA-Z0-9_]*$", return_stmt))
    if not is_named_variable:
        raise NotImplementedError(
            f"Inline return statements are not supported. Assign the return value of {func_name} to a variable before returning."
        )
    return return_stmt

# Cell


def parse_step(step_code: str):
    tree = ast.parse(step_code)
    lister = FuncLister()
    lister.visit(tree)
    if "name" not in lister.__dict__:
        raise (
            ValueError("Step must have a single valid function; check step definition")
        )
    return FuncDetails(
        lister.name,
        lister.docstring,
        ",".join(lister.arg_names),
        lister.has_return,
        extract_return_stmt(lister.name, step_code),
        step_code,
    )

# Cell


def extract_return_var_names(step):
    results_index = step.code.find(f"{step.return_stmt} =")
    if results_index == -1:
        return []

    keys = []
    for l in step.code[results_index:].split("\n"):
        if l.strip().find(":") > -1:
            key_prefix = l.split(":")[0]
            key = key_prefix[key_prefix.find("{") + 1 :]
            keys.append(key.strip(' ",'))
    return keys

# Cell


def extract_steps(module_path: Path):
    step_code = extract_step_code(module_path)
    steps = [parse_step(step_code[k]) for k in step_code.keys()]
    return steps

# Cell


def _convert_return_stmt(numbered_step):
    number, step = numbered_step
    step["return_stmt"] = "" if not step["return_stmt"] else step["return_stmt"]
    return number, step

# Cell


def extract_dag(test_module: Path):
    steps = extract_steps(test_module)

    node_ids = list(range(len(steps)))
    numbered_steps = zip(node_ids, [asdict(step) for step in steps])

    dag = nx.Graph()
    dag.add_nodes_from([_convert_return_stmt(s) for s in numbered_steps])
    dag.add_edges_from(list(zip(node_ids, node_ids[1:])))
    return dag