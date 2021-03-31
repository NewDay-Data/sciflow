# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/parse_module.ipynb (unless otherwise specified).

__all__ = ['extract_step_code', 'FuncLister', 'FuncDetails', 'parse_step', 'extract_steps', 'extract_dag']

# Cell

import ast
import os
from dataclasses import asdict, dataclass
from pathlib import Path

import networkx as nx
import pandas as pd
from nbdev.export import Config

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
        self.returns = node.returns
        self.generic_visit(node)


@dataclass
class FuncDetails:
    name: str
    docstring: str
    args: str
    has_return: bool
    code: str

# Cell


def parse_step(step_code: str):
    tree = ast.parse(step_code)
    lister = FuncLister()
    lister.visit(tree)
    return FuncDetails(
        lister.name,
        lister.docstring,
        ",".join(lister.arg_names),
        lister.returns is not None,
        step_code,
    )

# Cell


def extract_steps(module_path: Path):
    step_code = extract_step_code(module_path)
    steps = [parse_step(step_code[k]) for k in step_code.keys()]
    return steps

# Cell


def extract_dag(test_module: Path):
    steps = extract_steps(test_module)

    node_ids = list(range(len(steps)))
    numbered_steps = zip(node_ids, [asdict(step) for step in steps])

    dag = nx.Graph()
    dag.add_nodes_from(numbered_steps)
    dag.add_edges_from(list(zip(node_ids, node_ids[1:])))
    return dag