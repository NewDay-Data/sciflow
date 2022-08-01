# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/to_metaflow.ipynb (unless otherwise specified).

__all__ = ['rename_steps_for_metaflow', 'nb_to_metaflow', 'write_module_to_file', 'write_params', 'format_arg',
           'write_steps', 'write_track_capture', 'write_track_internal_helper', 'write_cli_wrapper', 'generate_flows',
           'sciflow_metaflow']

# Cell


import os
import shutil
from pathlib import Path, PosixPath
from typing import Iterable

import numpy as np
from fastcore.script import Param, call_parse
from nbdev.export import find_default_export, get_config, nbglob, read_nb

from .data_handler import extract_param_meta
from .params import params_as_dict
from .parse_module import FuncDetails, extract_module_only, extract_steps
from .utils import get_flow_path, indent_multiline, prepare_env, titleize

# Cell


def rename_steps_for_metaflow(steps):
    for i, step in enumerate(steps):
        if i == 0:
            step.name = "start"
        elif i == len(steps) - 1:
            step.name = "end"

# Cell


def nb_to_metaflow(nb_path: Path, flow_path: Path, silent=True, track_experiment=True):
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
        track_experiment,
    )
    if track_experiment:
        write_cli_wrapper(
            flow_path, extract_module_only(module_name), [s.name for s in steps]
        )
    if not silent:
        print(
            f"Converted {nb_name} to {flow_class_name} in: {os.path.basename(flow_path)}"
        )

# Cell


def write_module_to_file(
    flow_path: Path,
    flow_class_name: str,
    lib_name: str,
    module_name: str,
    orig_step_names: Iterable[str],
    steps: Iterable[FuncDetails],
    params: dict,
    track_experiment: bool,
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
        if has_mf_param or track_experiment:
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
        if track_experiment:
            flow_file.write(f"from sciflow.experiment.tracking import StepTracker\n")
            flow_file.write(f"import sys\n")
            flow_file.write(f"import tempfile\n")

        flow_file.write(f"\n\nclass {flow_class_name}(FlowSpec):\n")
        ind = "    "
        write_params(flow_file, param_meta, ind, track_experiment)
        flow_file.write("\n")
        write_steps(
            flow_file,
            steps,
            orig_step_names,
            param_meta,
            ind,
            track_experiment,
        )
        flow_file.write("\n")

        flow_file.write('if __name__ == "__main__":\n')
        flow_file.write(f"{ind}{flow_class_name}()")

# Cell


def write_params(flow_file, param_meta, ind, track_experiment):
    for param in param_meta.keys():
        if param_meta[param].is_scalar:
            flow_file.write(f"{ind}{param} = Parameter('{param}', default={param})\n")
        elif param_meta[param].is_json_type:
            flow_file.write(
                f"{ind}{param} = Parameter('{param}', default=json.dumps({param}), type=JSONType)\n"
            )
        elif param_meta[param].instance_type == PosixPath:
            flow_file.write(
                f"{ind}{param} = Parameter('{param}', default=str({param}))\n"
            )
    if track_experiment:
        flow_file.write(f"{ind}bucket_name = Parameter('bucket_name', required=True)\n")
        flow_file.write(
            f"{ind}flow_base_key = Parameter('flow_base_key', required=True)\n"
        )
        flow_file.write(f"{ind}flow_run_id = Parameter('flow_run_id', required=True)\n")

# Cell


def format_arg(arg, param_meta):
    if arg in param_meta and not param_meta[arg].has_metaflow_param:
        result = arg
    else:
        result = "self." + arg
    return result


def write_steps(flow_file, steps, orig_step_names, param_meta, ind, track_experiment):
    for i, step in enumerate(steps):
        if track_experiment:
            # Check for padded step
            if i < len(orig_step_names):
                flow_step_args = ""
                if len(step.args) > 0:
                    flow_step_args = ", ".join(
                        [format_arg(a, param_meta) for a in step.args.split(",")]
                    )

                step_func_call_text = f"{orig_step_names[i]}({flow_step_args})"

                write_track_internal_helper(
                    flow_file,
                    ind,
                    param_meta,
                    steps,
                    orig_step_names[i],
                    step_func_call_text.replace("self.tracker", "tracker"),
                    i,
                )
        else:
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
                    flow_file.write(
                        f"{ind}{ind}{orig_step_names[i]}({flow_step_args})\n"
                    )
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

# Cell


def write_track_capture(flow_file, ind, num_indents):
    base_ind = "".join(np.repeat(ind, num_indents))
    flow_file.write(f"{base_ind}for key in results.keys():\n")
    flow_file.write(f"{base_ind}{ind}if key in self.__dict__:\n")
    flow_file.write(
        f"{base_ind}{ind}{ind}self.__dict__[key] = self.__dict__[key] + results[key]\n"
    )
    flow_file.write(f"{base_ind}{ind}else:\n")
    flow_file.write(f"{base_ind}{ind}{ind}self.__dict__[key] = results[key]\n")

# Cell


def write_track_internal_helper(
    flow_file, ind, param_meta, steps, orig_step_name, step_func_call_text, i
):
    step = steps[i]
    flow_file.write(f"{ind}def _{step.name}(self):\n")
    if step.docstring:
        flow_file.write(f"{indent_multiline(step.docstring, 2)}\n")
    flow_file.write(f"{ind}{ind}tracker = None\n")
    flow_file.write(f"{ind}{ind}try:\n")
    flow_file.write(
        f'{ind}{ind}{ind}tracker = StepTracker(self.bucket_name, self.flow_base_key, self.flow_run_id, "{orig_step_name}")\n'
    )
    flow_file.write(f"{ind}{ind}{ind}with tempfile.TemporaryDirectory() as temp_dir:\n")
    flow_file.write(
        f"{ind}{ind}{ind}{ind}with tracker.capture_out() as tracker._output_file:\n"
    )
    flow_file.write(f"{ind}{ind}{ind}{ind}{ind}tracker.start_heartbeat(10.0)\n")

    if not step.has_return:
        flow_file.write(f"{ind}{ind}{ind}{ind}{ind}{step_func_call_text}\n")
    else:
        if step.return_stmt in param_meta:
            raise ValueError(
                f"[{os.path.basename(flow_file.name)}] step return variable {step.return_stmt} shadows a parameter name - parameters must be unique"
            )
        flow_file.write(f"{ind}{ind}{ind}{ind}{ind}results = {step_func_call_text}\n")
        write_track_capture(flow_file, ind, 5)

    flow_file.write(f"{ind}{ind}{ind}{ind}{ind}tracker.completed()\n")
    flow_file.write(f"{ind}{ind}except BaseException:\n")
    flow_file.write(f"{ind}{ind}{ind}if tracker:\n")
    flow_file.write(
        f"{ind}{ind}{ind}{ind}exc_type, exc_value, trace = sys.exc_info()\n"
    )
    flow_file.write(
        f'{ind}{ind}{ind}{ind}except_info = {{"exc_type": exc_type, "exc_value": exc_value, "trace": trace}}\n'
    )
    flow_file.write(
        f'{ind}{ind}{ind}{ind}tracker.completed(status="FAILED", except_info=except_info)\n'
    )
    flow_file.write(f"{ind}{ind}{ind}raise\n\n")
    flow_file.write(f"{ind}@step\n")
    flow_file.write(f"{ind}def {step.name}(self):\n")
    flow_file.write(f"{ind}{ind}self._{step.name}()\n")
    if i < len(steps) - 1:
        next_step = steps[i + 1].name
        flow_file.write(f"{ind}{ind}self.next(self.{next_step})\n")
    flow_file.write(f"\n")

# Cell


def write_cli_wrapper(flow_path, flow_base_key, steps):
    shutil.copyfile(
        flow_path, str(flow_path).replace(flow_base_key, f"_sciflow_{flow_base_key}")
    )
    ind = "    "
    with open(flow_path, "w") as wrapper_file:
        wrapper_file.write("#!/usr/bin/env python\n")
        wrapper_file.write("# coding=utf-8\n")
        wrapper_file.write("import os\n")
        wrapper_file.write("from datetime import datetime\n")
        wrapper_file.write(
            "from sciflow.experiment.tracking import FlowTracker, StepTracker\n"
        )
        wrapper_file.write("from sciflow.run_flow import run_shell_cmd\n")
        wrapper_file.write("import sys\n")
        wrapper_file.write("import tempfile\n")
        wrapper_file.write("\n")
        wrapper_file.write("\n")
        wrapper_file.write('if __name__ == "__main__":\n')
        wrapper_file.write(f'{ind}wrapped_module = "_sciflow_{flow_path.name}"\n')
        wrapper_file.write(f"{ind}if len(sys.argv) == 1:\n")
        wrapper_file.write(f'{ind}{ind}cmd = f"python {{wrapped_module}} show"\n')
        wrapper_file.write(f"{ind}{ind}pipe, output = run_shell_cmd(cmd)\n")
        wrapper_file.write(f"{ind}{ind}print(output)\n")
        wrapper_file.write(f"{ind}else:\n")
        wrapper_file.write(
            f'{ind}{ind}if "show" in sys.argv or "help" in sys.argv[1]:\n'
        )
        wrapper_file.write(f'{ind}{ind}{ind}full_cmd = " ".join(sys.argv)\n')
        wrapper_file.write(
            f'{ind}{ind}{ind}cmd = f"python {{full_cmd.replace(sys.argv[0], wrapped_module)}}"\n'
        )
        wrapper_file.write(f"{ind}{ind}{ind}pipe, output = run_shell_cmd(cmd)\n")
        wrapper_file.write(f"{ind}{ind}{ind}print(output)\n")
        wrapper_file.write(f'{ind}{ind}elif "run" in sys.argv[1]:\n')
        wrapper_file.write(
            f"{ind}{ind}{ind}bucket_name = os.environ['SCIFLOW_BUCKET']\n"
        )
        wrapper_file.write(
            f"{ind}{ind}{ind}run_timestamp = datetime.today().__str__().replace(':', '-').replace('.', '-').replace(' ', '-')[:-3]\n"
        )
        wrapper_file.write(f'{ind}{ind}{ind}flow_base_key = "{flow_base_key}"\n')
        wrapper_file.write(f'{ind}{ind}{ind}flow_run_id = f"flow-{{run_timestamp}}"\n')
        wrapper_file.write(f"{ind}{ind}{ind}steps = {steps}\n\n")
        wrapper_file.write(
            f"{ind}{ind}{ind}flow_tracker = FlowTracker(os.environ['SCIFLOW_BUCKET'], flow_base_key, flow_run_id, steps)\n"
        )
        wrapper_file.write(f"{ind}{ind}{ind}flow_tracker.start()\n")
        wrapper_file.write(f"{ind}{ind}{ind}\n")
        wrapper_file.write(f"{ind}{ind}{ind}try:\n")
        wrapper_file.write(f'{ind}{ind}{ind}{ind}sys.argv[1] = "--no-pylint run"\n')
        wrapper_file.write(f'{ind}{ind}{ind}{ind}full_cmd = " ".join(sys.argv)\n')
        wrapper_file.write(
            f'{ind}{ind}{ind}{ind}full_cmd += f" --bucket_name {{bucket_name}} --flow_base_key {{flow_base_key}} --flow_run_id {{flow_run_id}}"\n'
        )
        wrapper_file.write(
            f'{ind}{ind}{ind}{ind}cmd = f"python {{full_cmd.replace(sys.argv[0], wrapped_module)}}"\n'
        )
        wrapper_file.write(f"{ind}{ind}{ind}{ind}pipe, output = run_shell_cmd(cmd)\n")
        wrapper_file.write(f"{ind}{ind}{ind}{ind}print(output)\n")
        wrapper_file.write(f"{ind}{ind}{ind}except (KeyboardInterrupt):\n")
        wrapper_file.write(f"{ind}{ind}{ind}{ind}flow_tracker.interrupted()\n")
        wrapper_file.write(
            f'{ind}{ind}{ind}{ind}print(f"Flow interrupted by user: {{flow_run_id}}")\n'
        )
        wrapper_file.write(f"{ind}{ind}{ind}except BaseException:\n")
        wrapper_file.write(
            f"{ind}{ind}{ind}{ind}exc_type, exc_value, trace = sys.exc_info()\n"
        )
        wrapper_file.write(
            f'{ind}{ind}{ind}{ind}except_info = {{"exc_type": exc_type, "exc_value": exc_value, "trace": trace}}\n'
        )
        wrapper_file.write(f"{ind}{ind}{ind}{ind}flow_tracker.failed(except_info)\n")
        wrapper_file.write(
            f'{ind}{ind}{ind}{ind}print(f"Flow failed: {{flow_run_id}}")\n'
        )
        wrapper_file.write(f"{ind}{ind}{ind}flow_tracker.completed()\n")

# Cell


def generate_flows(config=None, track_experiment=True):
    nb_paths = nbglob(recursive=True)
    for nb_path in nb_paths:
        nb_to_metaflow(
            nb_path,
            get_flow_path(nb_path, config=config),
            track_experiment=track_experiment,
            silent=False,
        )

# Cell


@call_parse
def sciflow_metaflow(track: Param("Track flows as experiments", default=True)):
    print(f"Converting flows to metaflow (experiment tracking = {track})")
    generate_flows(get_config(), track)