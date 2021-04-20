# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/metaflow.ipynb (unless otherwise specified).

__all__ = ['titleize', 'rename_steps_for_metaflow', 'indent_multiline', 'nb_to_metaflow', 'extract_module_only',
           'write_module_to_file', 'write_observers', 'config', 'ex', 'obs', 'write_track_flow', 'write_params',
           'format_arg', 'write_steps', 'write_track_capture', 'get_module_name', 'generate_flows', 'sciflow_generate',
           'check_flows', 'prep_mf_env', 'run_shell_cmd', 'check_flow', 'sciflow_check_flows', 'sciflow_run_flows']

# Cell


import os
import subprocess
from pathlib import Path, PosixPath
from typing import Iterable

from fastcore.script import call_parse
from nbdev.export import Config, find_default_export, nbglob, read_nb
from .data_handler import extract_param_meta
from .params import params_as_dict
from .parse_module import FuncDetails, extract_steps

# Cell


def titleize(name):
    return name.title().replace("_", "")

# Cell


def rename_steps_for_metaflow(steps):
    for i, step in enumerate(steps):
        if i == 0:
            step.name = "start"

# Cell


def indent_multiline(multiline_text, indent=1):
    lines = multiline_text.strip().split("\n")
    spaces = "".join(["    " for _ in range(indent)])
    for i in range(len(lines)):
        prefix = spaces if i > 0 else spaces + '"""'
        lines[i] = prefix + lines[i]
    return "\n".join(lines) + '"""'

# Cell


def nb_to_metaflow(nb_path: Path, flow_path: Path, silent=True, track_experiment=True):
    nb = read_nb(nb_path)
    lib_name = Config().lib_name
    module_name = find_default_export(nb["cells"])
    if not module_name:
        return
    module_name = module_name
    path_sep_module_name = module_name.replace(".", "/")
    nb_name = os.path.basename(nb_path)
    exported_module = os.path.join(
        Config().path("lib_path"), f"{path_sep_module_name}.py"
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
    if not silent:
        print(
            f"Converted {nb_name} to {flow_class_name} in: {os.path.basename(flow_path)}"
        )

# Cell


def extract_module_only(package_module_name):
    module_name = package_module_name
    if "." in module_name:
        package_name, module_name = module_name.split(".")
    return module_name

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

        if track_experiment:
            flow_file.write("from sacred import Experiment\n")
            flow_file.write("from sciflow.lake_observer import AWSLakeObserver\n")
            flow_file.write("import time")
            write_observers(flow_file, module_name, Config().bucket, Config().lib_name)

        flow_file.write(f"\n\nclass {flow_class_name}(FlowSpec):\n")
        single_indent = "    "
        write_params(flow_file, param_meta, single_indent)
        flow_file.write(f"{single_indent}artifacts = []\n")
        flow_file.write(f"{single_indent}metrics = []\n")
        flow_file.write("\n")
        write_steps(flow_file, steps, orig_step_names, param_meta, single_indent)
        write_track_flow(flow_file, track_experiment)
        flow_file.write("\n")

        flow_file.write('if __name__ == "__main__":\n')
        flow_file.write(f"{single_indent}{flow_class_name}()")

# Cell


def write_observers(flow_file, module_name, bucket_name, project):
    experiment_name = extract_module_only(module_name)
    sacred_setup = f"""

ex = Experiment("{experiment_name}")
# TODO inject observers
obs = AWSLakeObserver(
    bucket_name="{bucket_name}",
    experiment_dir="experiments/{project}/{experiment_name}",
    region="eu-west-1",
)
ex.observers.append(obs)

@ex.config
def config():
    flow_run_id = None
    artifacts = []
    metrics = []
    """
    flow_file.write(sacred_setup)

# Cell


def write_track_flow(flow_file, track_experiment):
    track_flow = """
    @step
    def end(self):
        flow_info = {
            "flow_name": current.flow_name,
            "run id": current.run_id,
            "origin run id": current.origin_run_id,
            "pathspec": current.pathspec,
            "namespace": current.namespace,
            "username": current.username,
            "flow parameters": str(current.parameter_names),
            "run_time_mins": (time.time() - self.start_time) / 60.0
        }

        run = ex.run(config_updates={'flow_run_id': current.run_id,
                                    'artifacts': self.artifacts,
                                    'metrics': self.metrics},
                     meta_info = flow_info)

    @ex.main
    def track_flow(artifacts, metrics, _run):
        for artifact in artifacts:
            _run.add_artifact(artifact)
        for metric_name, metric_value, step in metrics:
            _run.log_scalar(metric_name, metric_value, step)
    """
    if not track_experiment:
        track_flow = """
    @step
    def end(self):
        pass
    """
    flow_file.write(track_flow)

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


def format_arg(arg, param_meta, returned_params):
    result = arg
    if (
        arg in param_meta and param_meta[arg].has_metaflow_param
    ) or arg in returned_params:
        result = "self." + arg
    return result


def write_steps(flow_file, steps, orig_step_names, param_meta, single_indent):
    returned_params = []
    for i, step in enumerate(steps):
        flow_file.write(f"{single_indent}@step\n")
        flow_file.write(f"{single_indent}def {step.name}(self):\n")
        if step.docstring:
            flow_file.write(f"{indent_multiline(step.docstring, 2)}\n")
        # Check for padded step
        if i < len(orig_step_names):
            flow_step_args = ""
            if len(step.args) > 0:
                flow_step_args = ", ".join(
                    [
                        format_arg(a, param_meta, returned_params)
                        for a in step.args.split(",")
                    ]
                )
            if not step.has_return:
                flow_file.write(
                    f"{single_indent}{single_indent}{orig_step_names[i]}({flow_step_args})\n"
                )
            else:
                if (
                    step.return_stmt in returned_params
                    or step.return_stmt in param_meta
                ):
                    raise ValueError(
                        f"[{os.path.basename(flow_file.name)}] step return variable {step.return_stmt} shadows a parameter name - parameters must be unique"
                    )
                returned_params.append(step.return_stmt)
                flow_file.write(
                    f"{single_indent}{single_indent}results = {orig_step_names[i]}({flow_step_args})\n"
                )
                write_track_capture(flow_file)
        if i == 0:
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

# Cell


def get_module_name(nb_path):
    nb = read_nb(nb_path)
    module_name = find_default_export(nb["cells"])
    return module_name

# Cell


def generate_flows(config: Config):
    flows_dir = config.path("flows_path")
    nb_paths = nbglob(recursive=True)
    for nb_path in nb_paths:
        flow_module_name = os.path.basename(nb_path).replace("ipynb", "py")
        nb_to_metaflow(
            nb_path, Path(os.path.join(flows_dir, flow_module_name)), silent=False
        )

# Cell


@call_parse
def sciflow_generate():
    generate_flows(Config())

# Cell


def check_flows(config, flow_command="show"):
    flow_results = {}
    flows_dir = config.path("flows_path")
    for flow_path in os.listdir(flows_dir):
        flow_name = os.path.basename(flow_path)
        if flow_path.endswith(".py"):
            ret_code, output = check_flow(
                flows_dir, flow_path, flow_command=flow_command
            )
            flow_results[flow_name] = ret_code, output
            if ret_code == 0:
                print(f"Flow: {flow_name} verified")
            else:
                print(f"Flow: {flow_name} verification failed\nDetails:\n{output}")

# Cell


def prep_mf_env():
    if "USER" not in os.environ:
        try:
            os.environ["USER"] = os.environ["GIT_COMMITTER_NAME"]
        except KeyError:
            raise EnvironmentError(
                "Metaflow requires a known user for tracked execution. Add USER or GIT_COMMITTER_NAME to Jupyter environment variables"
            )

# Cell


def run_shell_cmd(script):
    pipe = subprocess.Popen(
        "%s" % script, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True
    )
    output = pipe.communicate()[0]
    return pipe, output.decode("utf-8").strip()

# Cell


def check_flow(flows_dir, flow_module, flow_command="show"):
    prep_mf_env()
    script = f"python '{os.path.join(flows_dir, flow_module)}' {flow_command}"
    pipe, output = run_shell_cmd(script)
    return pipe.returncode, output

# Cell


@call_parse
def sciflow_check_flows():
    check_flows(Config())

# Cell


@call_parse
def sciflow_run_flows():
    check_flows(Config(), "--no-pylint run")