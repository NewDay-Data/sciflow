# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/converters/to_metaflow.ipynb.

# %% auto 0
__all__ = ['rename_steps_for_metaflow', 'nb_to_metaflow', 'write_module_to_file', 'write_params', 'format_arg', 'write_steps',
           'write_track_capture', 'generate_flows', 'sciflow_metaflow']

# %% ../../nbs/converters/to_metaflow.ipynb 4
# | export


import os
import shutil
from pathlib import Path, PosixPath
from typing import Iterable

import numpy as np
from execnb.nbio import read_nb
from fastcore.script import Param, bool_arg, call_parse
from nbdev.config import get_config
from nbdev.doclinks import nbglob

from ..params import extract_param_meta, params_as_dict, ParamMeta
from ..parse_module import FuncDetails, extract_module_only, extract_steps
from sciflow.utils import (
    find_default_export,
    get_flow_path,
    indent_multiline,
    prepare_env,
    titleize,
)

# %% ../../nbs/converters/to_metaflow.ipynb 8
# | export


def rename_steps_for_metaflow(steps):
    for i, step in enumerate(steps):
        if i == 0:
            step.name = "start"
        elif i == len(steps) - 1:
            step.name = "end"

# %% ../../nbs/converters/to_metaflow.ipynb 16
# | export


def nb_to_metaflow(nb_path: Path, flow_path: Path, silent=True):
    nb = read_nb(nb_path)
    lib_name = get_config().get("lib_name")
    module_name = find_default_export(nb["cells"])
    if not module_name:
        return
    module_name = module_name
    path_sep_module_name = module_name.replace(".", "/")
    nb_name = os.path.basename(nb_path)
    exported_module = os.path.join(
        get_config().path("lib_path"), f"{path_sep_module_name}.py"
    )
    steps = extract_steps(exported_module)
    if len(steps) == 0:
        return
    orig_step_names = [step.name for step in steps]
    if len(steps) == 1:
        steps.append(FuncDetails("end", None, None, False, "", "pass"))
    params = params_as_dict(nb_path)
    if len(params) == 0:
        print(f"No params cell found for: {os.path.basename(nb_path)}")
    flow_class_name = f"{titleize(extract_module_only(module_name))}Flow"
    rename_steps_for_metaflow(steps)
    write_module_to_file(
        flow_path,
        flow_class_name,
        lib_name,
        module_name,
        orig_step_names,
        steps,
        params,
    )
    if not silent:
        print(
            f"Converted {nb_name} to {flow_class_name} in: {os.path.basename(flow_path)}"
        )

# %% ../../nbs/converters/to_metaflow.ipynb 18
# | export


def write_module_to_file(
    flow_path: Path,
    flow_class_name: str,
    lib_name: str,
    module_name: str,
    orig_step_names: Iterable[str],
    steps: Iterable[FuncDetails],
    params: dict,
):
    if not os.path.exists(flow_path.parent):
        os.mkdir(flow_path.parent)
    fq_module_name = f"{lib_name}.{module_name}"
    param_meta = extract_param_meta(fq_module_name, params)
    with open(flow_path, "w") as flow_file:
        flow_file.write("#!/usr/bin/env python\n")
        flow_file.write("# coding=utf-8\n")
        flow_file.write("# SCIFLOW GENERATED FILE - EDIT COMPANION NOTEBOOK\n")
        has_mf_param = any((p.has_metaflow_param for p in param_meta.values()))
        has_json_param = any((p.is_json_type for p in param_meta.values()))
        mf_params_import = "from metaflow import FlowSpec, step, current"
        if has_mf_param:
            mf_params_import += ", Parameter"
        if has_json_param:
            mf_params_import += ", JSONType"
            flow_file.write("import json\n")
        flow_file.write(mf_params_import + "\n")
        flow_file.write(f"from {fq_module_name} import {', '.join(orig_step_names)}\n")
        if len(params) > 0:
            flow_file.write(
                f"from {fq_module_name} import {', '.join(params.keys())}\n"
            )

        flow_file.write(f"\n\nclass {flow_class_name}(FlowSpec):\n")
        ind = "    "
        write_params(flow_file, param_meta, ind)
        flow_file.write("\n")
        write_steps(flow_file, steps, orig_step_names, param_meta, ind)
        flow_file.write("\n")

        flow_file.write('if __name__ == "__main__":\n')
        flow_file.write(f"{ind}{flow_class_name}()")

# %% ../../nbs/converters/to_metaflow.ipynb 20
# | export


def write_params(flow_file, param_metas, ind):
    for param in param_metas.keys():
        if param_metas[param].is_scalar:
            flow_file.write(f"{ind}{param} = Parameter('{param}', default={param})\n")
        elif param_metas[param].is_json_type:
            flow_file.write(
                f"{ind}{param} = Parameter('{param}', default=json.dumps({param}), type=JSONType)\n"
            )
        elif param_metas[param].instance_type == PosixPath:
            flow_file.write(
                f"{ind}{param} = Parameter('{param}', default=str({param}))\n"
            )

# %% ../../nbs/converters/to_metaflow.ipynb 25
# | export


def format_arg(arg, param_meta):
    if arg in param_meta and not param_meta[arg].has_metaflow_param:
        result = arg
    else:
        result = "self." + arg
    return result

# %% ../../nbs/converters/to_metaflow.ipynb 28
# | export


def write_steps(flow_file, steps, orig_step_names, param_meta, ind):
    for i, step in enumerate(steps):
        flow_file.write(f"{ind}@step\n")
        flow_file.write(f"{ind}def {step.name}(self):\n")
        if step.docstring:
            flow_file.write(f"{indent_multiline(step.docstring, 2)}\n")

        if i < len(orig_step_names):
            flow_step_args = ""
            if len(step.args) > 0:
                flow_step_args = ", ".join(
                    [format_arg(a, param_meta) for a in step.args.split(",")]
                )
            if not step.has_return:
                flow_file.write(f"{ind}{ind}{orig_step_names[i]}({flow_step_args})\n")
            else:
                if step.return_stmt in param_meta:
                    raise ValueError(
                        f"[{os.path.basename(flow_file.name)}] step return variable {step.return_stmt} shadows a parameter name - parameters must be unique"
                    )
                flow_file.write(
                    f"{ind}{ind}results = {orig_step_names[i]}({flow_step_args})\n"
                )
                write_track_capture(flow_file, ind, 2)
        else:
            flow_file.write(f"{ind}{ind}pass\n")
            flow_file.write("\n")
        if i < len(steps) - 1:
            next_step = steps[i + 1].name
            flow_file.write(f"{ind}{ind}self.next(self.{next_step})\n")
        flow_file.write("\n")

# %% ../../nbs/converters/to_metaflow.ipynb 30
# | export


def write_track_capture(flow_file, ind, num_indents):
    base_ind = "".join(np.repeat(ind, num_indents))
    flow_file.write(f"{base_ind}for key in results.keys():\n")
    flow_file.write(f"{base_ind}{ind}if key in self.__dict__:\n")
    flow_file.write(
        f"{base_ind}{ind}{ind}self.__dict__[key] = self.__dict__[key] + results[key]\n"
    )
    flow_file.write(f"{base_ind}{ind}else:\n")
    flow_file.write(f"{base_ind}{ind}{ind}self.__dict__[key] = results[key]\n")

# %% ../../nbs/converters/to_metaflow.ipynb 49
# | export


def generate_flows(config=None, clear_dir=True):
    if clear_dir:
        metaflows_dir = Path(get_config().path("flows_path"), "metaflow")
        [f.unlink() for f in metaflows_dir.iterdir() if not f.is_dir()]
    nb_paths = nbglob()
    for nb_path in nb_paths:
        nb_to_metaflow(
            nb_path,
            get_flow_path(nb_path, config=config),
            silent=False,
        )

# %% ../../nbs/converters/to_metaflow.ipynb 53
# | export


@call_parse
def sciflow_metaflow():
    generate_flows(config=get_config())
