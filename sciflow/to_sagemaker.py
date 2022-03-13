# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/to_sagemaker.ipynb (unless otherwise specified).

__all__ = ['nb_to_sagemaker_pipeline', 'write_pipeline_to_files', 'write_observers', 'write_track_flow', 'write_params',
           'format_arg', 'write_steps', 'write_track_capture']

# Cell


import os
from pathlib import Path
from typing import Any, Dict, Iterable

from nbdev.export import find_default_export, get_config, read_nb

from .data_handler import extract_param_meta
from .params import params_as_dict
from .parse_module import FuncDetails, extract_steps
from .utils import prepare_env

# Cell


def nb_to_sagemaker_pipeline(nb_path: Path, flow_path: Path, silent=True, track_experiment=True):
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
        print('Skipping sagemaker conversion - not steps found')
        return
    params = params_as_dict(nb_path)
    if len(params) == 0:
        print(f"No params cell found for: {os.path.basename(nb_path)}")
    pipeline_class_name = f"{titleize(extract_module_only(module_name))}Pipeline"
    write_pipeline_to_files(
        flow_path,
        pipeline_class_name,
        lib_name,
        module_name,
        steps,
        params,
        track_experiment,
    )
    if not silent:
        print(
            f"Converted {nb_name} to {pipeline_class_name} in: {os.path.basename(flow_path)}"
        )

# Cell


def write_pipeline_to_files(
    flow_path: Path,
    pipeline_class_name: str,
    lib_name: str,
    module_name: str,
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
        flow_file.write("import os\n")

        flow_file.write("import sagemaker\n")
        flow_file.write("from sagemaker.session import Session\n")
        flow_file.write("from sagemaker.workflow.pipeline import Pipeline\n")

        has_train_step = any([s.name.startswith(n) for n in['fit', 'train'] for s in steps])
        has_processing_step = sum([s.name.startswith(n) for n in['fit', 'train'] for s in steps]) != len(steps)

        if has_train_step and has_processing_step:
            flow_file.write("from sagemaker.workflow.steps import ProcessingStep, TrainingStep\n")
        if has_processing_step:
            flow_file.write("from sagemaker.processing import ScriptProcessor, ProcessingInput, ProcessingOutput\n")
            flow_file.write("from sagemaker.workflow.pipeline import Pipeline\n")
        if has_train_step:
            flow_file.write("from sagemaker.inputs import TrainingInput\n")
            flow_file.write("from sagemaker.estimator import Estimator\n")

        has_sm_param = any((p.has_sagemaker_param for p in param_meta.values()))
        if has_sm_param:
            instance_types = [p.instance_type for p in param_meta.values()]
            sm_params_import = "from sagemaker.workflow.parameters import "
            if int in instance_types:
                sm_params_import += ", ParameterInteger"
            if float in instance_types:
                sm_params_import += ", ParameterFloat"
            if str in instance_types:
                sm_params_import += ", ParameterString"

            flow_file.write(sm_params_import + "\n")

        flow_file.write(f"from {fq_module_name} import {', '.join([s.name for s in steps])}\n")
        if len(params) > 0:
            flow_file.write(
                f"from {fq_module_name} import {', '.join(params.keys())}\n"
            )

        if track_experiment:
            flow_file.write("from sacred import Experiment\n")
            flow_file.write(
                "from sciflow.experiment.lake_observer import AWSLakeObserver\n"
            )
            flow_file.write("import time")
            write_observers(
                lib_name,
                flow_file,
                module_name,
                os.environ["SCIFLOW_BUCKET"],
                get_config().get("lib_name"),
            )

        flow_file.write(f"\n\nclass {pipeline_class_name}():\n")
        single_indent = "    "
        write_params(flow_file, param_meta, single_indent)
        if track_experiment:
            flow_file.write(f"{single_indent}artifacts = []\n")
            flow_file.write(f"{single_indent}metrics = []\n")
        flow_file.write("\n")
        write_steps(
            flow_file,
            steps,
            param_meta,
            single_indent,
            track_experiment,
        )
        write_track_flow(flow_file, track_experiment)
        flow_file.write("\n")

        flow_file.write('if __name__ == "__main__":\n')
        flow_file.write(f"{single_indent}{pipeline_class_name}()")

# Cell


def write_observers(lib_name, flow_file, module_name, bucket_name, project):
    pass

# Cell


def write_track_flow(flow_file, track_experiment):
    pass

# Cell


def write_params(flow_file, param_meta, single_indent):
    for param in param_meta.keys():
        if param_meta[param].is_scalar:
            flow_file.write(
                f"{single_indent}{param} = Parameter('{param}', default={param})\n"
            )
        elif param_meta[param].is_json_type:
            flow_file.write(
                f"{single_indent}{param} = Parameter('{param}', default=json.dumps({param}), type=JSONType)\n"
            )
        elif param_meta[param].instance_type == PosixPath:
            flow_file.write(
                f"{single_indent}{param} = Parameter('{param}', default=str({param}))\n"
            )

# Cell


def format_arg(arg, param_meta):
    if arg in param_meta and not param_meta[arg].has_metaflow_param:
        result = arg
    else:
        result = "self." + arg
    return result


def write_steps(
    flow_file, steps, param_meta, single_indent, track_experiment
):
    step_names = [s.name for s in steps]
    for i, step in enumerate(steps):
        flow_file.write(f"{single_indent}@step\n")
        flow_file.write(f"{single_indent}def {step.name}(self):\n")
        if step.docstring:
            flow_file.write(f"{indent_multiline(step.docstring, 2)}\n")
        # Check for padded step
        if i < len(step_names):
            flow_step_args = ""
            if len(step.args) > 0:
                flow_step_args = ", ".join(
                    [format_arg(a, param_meta) for a in step.args.split(",")]
                )
            if not step.has_return:
                flow_file.write(
                    f"{single_indent}{single_indent}{step_names[i]}({flow_step_args})\n"
                )
            else:
                if step.return_stmt in param_meta:
                    raise ValueError(
                        f"[{os.path.basename(flow_file.name)}] step return variable {step.return_stmt} shadows a parameter name - parameters must be unique"
                    )
                flow_file.write(
                    f"{single_indent}{single_indent}results = {step_names[i]}({flow_step_args})\n"
                )
                write_track_capture(flow_file)
        if i == 0 and track_experiment:
            flow_file.write(
                f"{single_indent}{single_indent}self.start_time = time.time()\n"
            )
        if i < len(steps):
            next_step = "end" if i == len(steps) - 1 else steps[i + 1].name
            flow_file.write(
                f"{single_indent}{single_indent}self.next(self.{next_step})\n"
            )
        flow_file.write("\n")

# Cell


def write_track_capture(flow_file):
    flow_file.write(
        f"""
        for key in results.keys():
            if key in self.__dict__:
                self.__dict__[key] = self.__dict__[key] + results[key]
            else:
                self.__dict__[key] = results[key]

"""
    )