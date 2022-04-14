# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/to_sagemaker.ipynb (unless otherwise specified).

__all__ = ['nb_to_sagemaker_pipeline', 'is_train_step', 'is_processing_step', 'write_pipeline_to_files',
           'write_track_flow', 'write_params', 'write_script_processor', 'extract_step_vars', 'format_job_arguments',
           'format_hyperparams', 'format_arg', 'write_steps', 'write_track_capture', 'get_return_var_names',
           'format_args', 'generate_sagemaker_modules', 'generate_flows', 'sciflow_sagemaker']

# Cell


import os
import shutil
from pathlib import Path, PosixPath
from typing import Iterable

from fastcore.script import Param, call_parse
from nbdev.export import find_default_export, get_config, nbglob, read_nb

from .data_handler import extract_param_meta
from .packaging import determine_dependencies
from .params import params_as_dict
from .parse_module import FuncDetails, extract_steps
from .utils import lib_path

# Cell


def nb_to_sagemaker_pipeline(
    nb_path: Path,
    flow_path: Path,
    config,
    silent: bool = True,
    track_experiment: bool = True,
):
    nb = read_nb(nb_path)
    lib_name = get_config().get("lib_name")
    module_name = find_default_export(nb["cells"])
    if not module_name:
        return
    module_name = module_name
    path_sep_module_name = module_name.replace(".", "/")
    nb_name = os.path.basename(nb_path)
    exported_module = os.path.join(
        config.path("lib_path"), f"{path_sep_module_name}.py"
    )
    steps = extract_steps(exported_module)
    if len(steps) == 0:
        print("Skipping sagemaker conversion - no steps found")
        return
    params = params_as_dict(nb_path)
    if len(params) == 0:
        print(f"No params cell found for: {os.path.basename(nb_path)}")
    pipeline_class_name = f"{titleize(extract_module_only(module_name))}Pipeline"
    steps_param_meta, steps_vars = write_pipeline_to_files(
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
    generate_sagemaker_modules(
        flow_path,
        pipeline_class_name,
        lib_name,
        module_name,
        steps,
        params,
        steps_param_meta,
        steps_vars,
        track_experiment,
    )

# Cell


def is_train_step(step):
    return any(step.name.startswith(prefix) for prefix in ("fit", "train"))


def is_processing_step(step):
    return not is_train_step(step)

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

    # TODO - add to profiles or accept as params from papermill
    proc_image_uri = "368653567616.dkr.ecr.eu-west-1.amazonaws.com/sagemaker-training-custom:conda-env-training"
    proc_instance_type = "ml.t3.medium"
    train_image_uri = "368653567616.dkr.ecr.eu-west-1.amazonaws.com/sagemaker-training-custom:conda-env-training"
    train_instance_type = "ml.m5.large"

    with open(flow_path, "w") as flow_file:
        flow_file.write("#!/usr/bin/env python\n")
        flow_file.write("# coding=utf-8\n")
        flow_file.write("# SCIFLOW GENERATED FILE - EDIT COMPANION NOTEBOOK\n")

        flow_file.write("import os\n")
        flow_file.write("import sys\n")
        flow_file.write("from datetime import datetime\n")
        flow_file.write("from pathlib import Path\n")
        flow_file.write("\n")
        flow_file.write("import boto3\n")
        flow_file.write("import sagemaker\n")
        flow_file.write("from sagemaker.session import Session\n")
        flow_file.write("from sagemaker.workflow.pipeline import Pipeline\n")

        has_train_step = any([is_train_step(s) for s in steps])
        has_processing_step = sum([is_processing_step(s) for s in steps]) != len(steps)

        if has_train_step and has_processing_step:
            flow_file.write(
                "from sagemaker.workflow.steps import ProcessingStep, TrainingStep\n"
            )
        if has_processing_step:
            flow_file.write(
                "from sagemaker.processing import ScriptProcessor, ProcessingInput, ProcessingOutput\n"
            )
            flow_file.write("from sagemaker.workflow.pipeline import Pipeline\n")
        if has_train_step:
            flow_file.write("from sagemaker.inputs import TrainingInput\n")
            flow_file.write("from sagemaker.estimator import Estimator\n")

        has_sm_param = any((p.has_sagemaker_param for p in param_meta.values()))
        if has_sm_param:
            instance_types = [p.instance_type for p in param_meta.values()]
            sm_params_import = "from sagemaker.workflow.parameters import "
            if int in instance_types:
                sm_params_import += "ParameterInteger"
                if float in instance_types or str in instance_types:
                    sm_params_import += ", "
            if float in instance_types:
                sm_params_import += "ParameterFloat"
                if str in instance_types:
                    sm_params_import += ", "
            if str in instance_types:
                sm_params_import += "ParameterString"

            flow_file.write(sm_params_import + "\n")

        flow_file.write("from sciflow.s3_utils import upload_directory\n")
        flow_file.write("\n")
        flow_file.write(
            f"from {fq_module_name} import {', '.join([s.name for s in steps])}\n"
        )
        if len(params) > 0:
            flow_file.write(
                f"from {fq_module_name} import {', '.join(params.keys())}\n"
            )

        flow_file.write(f"\n\nclass {pipeline_class_name}():\n")
        ind = "    "
        write_params(flow_file, param_meta, ind)
        flow_file.write("\n")
        flow_file.write(f"{ind}steps = {[s.name for s in steps]}\n")
        flow_file.write("\n")
        steps_param_meta, steps_vars = write_steps(
            lib_name,
            module_name,
            fq_module_name,
            flow_file,
            steps,
            param_meta,
            ind,
            proc_image_uri,
            proc_instance_type,
            train_image_uri,
            train_instance_type,
            track_experiment,
        )
        flow_file.write("\n")

        flow_file.write(f"{ind}def get_pipeline(self) -> Pipeline:\n")
        flow_file.write(
            f"{ind}{ind}pipeline_steps = [getattr(self, step)() for step in self.steps]\n"
        )
        flow_file.write(f"{ind}{ind}pipeline = Pipeline(\n")
        flow_file.write(f"{ind}{ind}{ind}name=self.flow_name,\n")
        flow_file.write(f"{ind}{ind}{ind}parameters=[\n")
        for param_name in params.keys():
            flow_file.write(f"{ind}{ind}{ind}{ind}self.{param_name},\n")
        flow_file.write(f"{ind}{ind}{ind}],\n")
        flow_file.write(f"{ind}{ind}{ind}steps = pipeline_steps,\n")
        flow_file.write(f"{ind}{ind}{ind}sagemaker_session = self.sagemaker_session,\n")
        flow_file.write(f"{ind}{ind})\n")
        flow_file.write(f"{ind}{ind}return pipeline\n")
        flow_file.write("\n")

        flow_file.write(f"{ind}def init(self):\n")
        flow_file.write(f"{ind}{ind}self.bucket = os.environ['SCIFLOW_BUCKET']\n")
        flow_file.write(f"{ind}{ind}self.role = sagemaker.get_execution_role()\n")
        flow_file.write(f"{ind}{ind}self.region = 'eu-west-1'\n")
        flow_file.write(
            f"{ind}{ind}self.sagemaker_session = Session(default_bucket=self.bucket)\n\n"
        )
        flow_file.write(
            f"{ind}{ind}self.flow_name = \"{extract_module_only(module_name).replace('_', '-')}\"\n"
        )
        flow_file.write(
            f"{ind}{ind}run_timestamp = datetime.today().__str__().replace(':', '-').replace('.', '-').replace(' ', '-')[:-3]\n"
        )
        flow_file.write(f'{ind}{ind}self.flow_run_id = f"pipeline-{{run_timestamp}}"\n')
        flow_file.write(
            f'{ind}{ind}self.s3_prefix = f"{{self.flow_name}}/{{self.flow_run_id}}"\n'
        )
        flow_file.write(
            f'{ind}{ind}self.flow_s3_uri = f"s3://{{self.bucket}}/{{self.s3_prefix}}"\n'
        )
        flow_file.write(f'{ind}{ind}self.s3_client = boto3.client("s3")\n')

        proc_steps = [s for s in steps if is_processing_step(s)]
        lib_reqs_path = Path(lib_path(), "requirements.txt")
        if not lib_reqs_path.exists():
            determine_dependencies(generated_pip_file_name="requirements.txt")
        flow_reqs_path = Path(
            lib_path(), config.flows_path, "sagemaker", "requirements.txt"
        )
        if not flow_reqs_path.exists():
            shutil.copyfile(lib_reqs_path, flow_reqs_path)
        flow_file.write(
            f'{ind}{ind}self.s3_client.upload_file("requirements.txt", self.bucket, f"{{self.s3_prefix}}/requirements.txt")\n'
        )
        for proc_step in proc_steps:
            flow_file.write(
                f'{ind}{ind}self.s3_client.upload_file("{extract_module_only(module_name)}_{proc_step.name}.py", self.bucket, f"{{self.s3_prefix}}/code/{extract_module_only(module_name)}_{proc_step.name}.py")\n'
            )
        modules_dir = Path(lib_path(), config.lib_name)
        flow_file.write(
            f'{ind}{ind}self.lib_code_key = f"{{self.s3_prefix}}/code/{config.lib_name}"\n'
        )
        flow_file.write(
            f'{ind}{ind}upload_directory(self.s3_client, "{modules_dir}", self.bucket, self.lib_code_key)\n'
        )

        flow_file.write("\n")
        flow_file.write(f"{ind}def show(self):\n")
        flow_file.write(f"{ind}{ind}self.init()\n")
        flow_file.write(f"{ind}{ind}pipeline = self.get_pipeline()\n")
        flow_file.write(f"{ind}{ind}description = pipeline.describe()\n")
        flow_file.write(f'{ind}{ind}print("Sciflow generated pipeline is valid")\n')
        flow_file.write(
            f"{ind}{ind}print(f\"Pipeline name: {{description['PipelineName']}}\")\n"
        )
        flow_file.write(
            f"{ind}{ind}print(f\"Pipeline ARN: {{description['PipelineArn']}}\")\n"
        )
        flow_file.write("\n")

        flow_file.write(f"{ind}def run(self):\n")
        flow_file.write(f"{ind}{ind}self.init()\n")
        flow_file.write(f"{ind}{ind}pipeline = self.get_pipeline()\n")
        flow_file.write(f"{ind}{ind}pipeline.upsert(role_arn=self.role)\n")
        flow_file.write(f"{ind}{ind}execution = pipeline.start()\n")
        flow_file.write(
            f'{ind}{ind}print(f"Starting Sciflow generated pipeline: {{self.flow_run_id}}")\n'
        )
        flow_file.write(f"{ind}{ind}print(execution.describe())\n")
        flow_file.write(f"{ind}{ind}execution.wait()\n")
        flow_file.write("\n")

        flow_file.write('if __name__ == "__main__":\n')
        flow_file.write(f"{ind}if len(sys.argv) == 1:\n")
        flow_file.write(f"{ind}{ind}{pipeline_class_name}().show()\n")
        flow_file.write(f"{ind}else:\n")
        flow_file.write(f"{ind}{ind}if sys.argv[1] == 'show':\n")
        flow_file.write(f"{ind}{ind}{ind}{pipeline_class_name}().show()\n")
        flow_file.write(f"{ind}{ind}if sys.argv[1] == 'run':\n")
        flow_file.write(f"{ind}{ind}{ind}{pipeline_class_name}().run()\n")

        return steps_param_meta, steps_vars

# Cell


def write_track_flow(flow_file, track_experiment):
    pass

# Cell


def write_params(flow_file, param_meta, ind):
    for param in param_meta.keys():
        print(param, param_meta[param].instance_type)
        if param_meta[param].instance_type == int:
            flow_file.write(
                f"{ind}{param} = ParameterInteger(name='{param}', default_value={param})\n"
            )
        elif param_meta[param].instance_type == float:
            flow_file.write(
                f"{ind}{param} = ParameterFloat(name='{param}', default_value={param})\n"
            )
        elif param_meta[param].instance_type == str:
            flow_file.write(
                f"{ind}{param} = ParameterString(name='{param}', default_value={param})\n"
            )
        elif param_meta[param].instance_type == PosixPath:
            flow_file.write(
                f"{ind}{param} = ParameterString(name='{param}', default_value=str({param}))\n"
            )
        else:
            raise ValueError(
                f"Unsupported parameter type for sagemaker pipeline: {param_meta[param]}"
            )

# Cell


def write_script_processor(flow_file, ind, proc_image_uri, proc_instance_type):
    flow_file.write(f"{ind}{ind}script_processor = ScriptProcessor(\n")
    flow_file.write(f"{ind}{ind}{ind}command=['python3'],\n")
    flow_file.write(f'{ind}{ind}{ind}image_uri="{proc_image_uri}",\n')
    flow_file.write(f"{ind}{ind}{ind}role=self.role,\n")
    flow_file.write(f"{ind}{ind}{ind}instance_count=1,\n")
    flow_file.write(f'{ind}{ind}{ind}instance_type="{proc_instance_type}",\n')
    flow_file.write(f"{ind}{ind}{ind}sagemaker_session=self.sagemaker_session,\n")
    flow_file.write(f'{ind}{ind}{ind}env={{"AWS_DEFAULT_REGION": self.region,\n')
    flow_file.write(f'{ind}{ind}{ind}{ind}{ind}"SCIFLOW_BUCKET": self.bucket}}\n')
    flow_file.write(f"{ind}{ind})\n")

# Cell


def extract_step_vars(step, param_names, processing_flow_scope, train_flow_scope):
    if len(step.args) == 0:
        result = {}
    else:
        args = [x.strip() for x in step.args.split(",")]
        step_input = [a for a in args if a in param_names]
        step_proc_vars = [a for a in args if a in processing_flow_scope]
        step_train_vars = [a for a in args if a in train_flow_scope]
        unscoped_vars = set(args).difference(
            set(step_input + step_proc_vars + step_train_vars)
        )
        if len(unscoped_vars) > 0:
            raise ValueError(
                f'Step: {step.name} depends on variable(s), "{unscoped_vars}", which are not in the flow scope'
            )
        result = {
            "step_input": step_input,
            "step_proc_vars": step_proc_vars,
            "step_train_vars": step_train_vars,
        }
    return result

# Cell


def format_job_arguments(param_meta):
    job_arg_values = [
        f"str(self.{p}.__int__())"
        if param_meta[p].instance_type == int
        else f"str(self.{p}.__float__())"
        if param_meta[p].instance_type == float
        else f"self.{p}.__str__()"
        if param_meta[p].instance_type == str
        else f"str(self.{p})"
        for p in param_meta.keys()
    ]
    stitched_args = list(zip([f"--{p}" for p in param_meta.keys()], job_arg_values))
    flattened = [item for sublist in stitched_args for item in sublist]
    return flattened

# Cell


def format_hyperparams(param_meta):
    job_arg_values = [
        f"str(self.{p}.__int__())"
        if param_meta[p].instance_type == int
        else f"str(self.{p}.__float__())"
        if param_meta[p].instance_type == float
        else f"self.{p}.__str__()"
        if param_meta[p].instance_type == str
        else f"str(self.{p})"
        for p in param_meta.keys()
    ]
    return dict(zip(param_meta.keys(), job_arg_values))

# Cell


def format_arg(arg, param_meta):
    if arg in param_meta and not param_meta[arg].has_metaflow_param:
        result = arg
    else:
        result = "self." + arg
    return result


def write_steps(
    lib_name,
    module_name,
    fq_module_name,
    flow_file,
    steps,
    param_meta,
    ind,
    proc_image_uri,
    proc_instance_type,
    train_image_uri,
    train_instance_type,
    track_experiment,
):
    steps_param_meta = {}
    steps_vars = {}
    param_names = list(param_meta.keys())
    proc_flow_scope = []
    train_flow_scope = []
    outputs = {}

    module_local_name = extract_module_only(module_name)

    for i, step in enumerate(steps):
        return_vars = get_return_var_names(step)

        step_vars = extract_step_vars(
            step, param_names, proc_flow_scope, train_flow_scope
        )
        steps_vars[step.name] = step_vars

        flow_file.write(f"{ind}def {step.name}(self):\n")
        if step.docstring:
            flow_file.write(f"{indent_multiline(step.docstring, 2)}\n")

        # Processing step
        if is_processing_step(step):
            write_script_processor(flow_file, ind, proc_image_uri, proc_instance_type)

            flow_file.write("\n")
            flow_file.write(f"{ind}{ind}{step.name}_step = ProcessingStep(\n")
            flow_file.write(f'{ind}{ind}{ind}name = "{step.name}",\n')
            flow_file.write(f"{ind}{ind}{ind}processor = script_processor,\n")
            flow_file.write(
                f'{ind}{ind}{ind}code = f"{{self.flow_s3_uri}}/code/{module_local_name}_{step.name}.py",\n'
            )
            job_arg_pairs = [
                ("--lib_name", f'"{lib_name}"'),
                ("--remote_key", "self.lib_code_key"),
            ]
            flow_file.write(f"{ind}{ind}{ind}inputs = [\n")
            flow_file.write(
                f'{ind}{ind}{ind}{ind}ProcessingInput(source=f"{{self.flow_s3_uri}}/requirements.txt", destination="/opt/ml/processing/requirements"),\n'
            )

            if len(step_vars) > 0:
                step_param_meta = {k: param_meta[k] for k in step_vars["step_input"]}
                steps_param_meta[step.name] = step_param_meta
                if len(step_param_meta) > 0:
                    # Job Args
                    job_args = format_job_arguments(step_param_meta)
                    job_arg_pairs.extend(zip(job_args[::2], job_args[1::2]))

                # ProcInputs
                if (
                    len(step_vars["step_proc_vars"]) > 0
                    or len(step_vars["step_train_vars"]) > 0
                ):
                    flow_file.write(
                        "\n".join(
                            [
                                f'{ind}{ind}{ind}{ind}ProcessingInput(source=self.{outputs[cv]}, destination="/opt/ml/processing/input/{cv}"),\n'
                                for cv in step_vars["step_train_vars"]
                                + step_vars["step_proc_vars"]
                            ]
                        )
                    )
            flow_file.write(f"{ind}{ind}{ind}],\n")

            if len(return_vars) > 0:
                # ProcOutputs
                proc_outs = {
                    (
                        v,
                        f'{step.name}_step.properties.ProcessingOutputConfig.Outputs["{v}"].S3Output.S3Uri',
                    )
                    for v in return_vars
                }
                outputs.update(proc_outs)

                if len(proc_outs) > 0:
                    flow_file.write(f"{ind}{ind}{ind}outputs = [\n")
                    flow_file.write(
                        "\n".join(
                            [
                                f'{ind}{ind}{ind}{ind}ProcessingOutput(output_name="{v}", source="/opt/ml/processing/output/{v}"),'
                                for v in [x[0] for x in proc_outs]
                            ]
                        )
                        + "\n"
                    )
                    flow_file.write(f"{ind}{ind}{ind}],\n")

            flow_file.write(f"{ind}{ind}{ind}job_arguments=[\n")
            for job_arg_pair in job_arg_pairs:
                flow_file.write(
                    f'{ind}{ind}{ind}{ind}"{job_arg_pair[0]}", {job_arg_pair[1]},\n'
                )
            flow_file.write(f"{ind}{ind}{ind}],\n")

            flow_file.write(f"{ind}{ind})\n")
            proc_flow_scope.extend(return_vars)
        elif is_train_step(step):
            if len(step_vars) > 0:
                train_outs = {
                    (v, f"{step.name}_step.properties.ModelArtifacts.S3ModelArtifacts")
                    for v in return_vars
                }
                outputs.update(train_outs)
                train_flow_scope.extend(return_vars)

                flow_file.write(f"{ind}{ind}metrics_regex = None\n")
                flow_file.write(f"{ind}{ind}if 'metric_names' in self.__dict__:\n")
                flow_file.write(
                    f'{ind}{ind}{ind}metrics = self.metric_names.split(",")\n',
                )
                flow_file.write(
                    f'{ind}{ind}{ind}metrics_regex = [{{"Name": m, "Regex": f"{{m}}=(.*?);"}} for m in metrics]\n'
                )
                flow_file.write(f"\n")
                flow_file.write(f"{ind}{ind}estimator = Estimator(\n")
                flow_file.write(
                    f'{ind}{ind}{ind}image_uri = "368653567616.dkr.ecr.eu-west-1.amazonaws.com/sagemaker-training-custom:conda-env-training",\n'
                )
                flow_file.write(
                    f'{ind}{ind}{ind}entry_point="{module_local_name}_{step.name}.py",\n'
                )
                flow_file.write(f'{ind}{ind}{ind}source_dir=".",\n')
                # Repeated code - refactor
                step_param_meta = {k: param_meta[k] for k in step_vars["step_input"]}
                steps_param_meta[step.name] = step_param_meta
                hyper_params = {
                    "lib_name": f'"{lib_name}"',
                    "remote_key": "self.lib_code_key",
                }
                if len(step_vars["step_input"]) > 0:
                    hyper_params.update(format_hyperparams(step_param_meta))
                flow_file.write(f"{ind}{ind}{ind}hyperparameters={{\n")
                for key, val in hyper_params.items():
                    flow_file.write(f'{ind}{ind}{ind}{ind}"{key}": {val},\n')
                flow_file.write(f"{ind}{ind}{ind}}},\n")
                flow_file.write(f'{ind}{ind}{ind}instance_type="ml.m5.xlarge",\n')
                flow_file.write(f"{ind}{ind}{ind}instance_count=1,\n")
                flow_file.write(f"{ind}{ind}{ind}output_path=self.flow_s3_uri,\n")
                flow_file.write(f'{ind}{ind}{ind}base_job_name="{step.name}",\n')
                flow_file.write(
                    f'{ind}{ind}{ind}code_location = f"{{self.flow_s3_uri}}/code",\n'
                )
                flow_file.write(
                    f"{ind}{ind}{ind}sagemaker_session = self.sagemaker_session,\n"
                )
                flow_file.write(f"{ind}{ind}{ind}role = self.role,\n")
                flow_file.write(f"{ind}{ind}{ind}metric_definitions=metrics_regex,\n")
                flow_file.write(f"{ind}{ind}{ind}enable_sagemaker_metrics=True,\n")
                flow_file.write(
                    f"{ind}{ind}{ind}environment={{'AWS_DEFAULT_REGION': self.region,\n"
                )
                flow_file.write(
                    f"{ind}{ind}{ind}{ind}{ind}'SCIFLOW_BUCKET': self.bucket}}\n"
                )
                flow_file.write(f"{ind}{ind})\n")
                flow_file.write("\n")
                flow_file.write(f"{ind}{ind}{step.name}_step = TrainingStep(\n")
                flow_file.write(f'{ind}{ind}{ind}name="{step.name}",\n')
                flow_file.write(f"{ind}{ind}{ind}estimator=estimator,\n")
                if (
                    "step_proc_vars" in step_vars
                    and len(step_vars["step_proc_vars"]) > 0
                ):
                    flow_file.write(f"{ind}{ind}{ind}inputs={{\n")
                    for training_input in step_vars["step_proc_vars"]:
                        flow_file.write(
                            f'{ind}{ind}{ind}{ind}"{training_input}": TrainingInput(\n'
                        )
                        # TODO store content type mapping
                        flow_file.write(
                            f'{ind}{ind}{ind}{ind}{ind}s3_data=self.{outputs[training_input]}, content_type="text/csv"\n'
                        )
                    flow_file.write(f"{ind}{ind}{ind}{ind})\n")
                    flow_file.write(f"{ind}{ind}{ind}}}\n")
                flow_file.write(f"{ind}{ind})\n")

        flow_file.write(f"{ind}{ind}self.{step.name}_step = {step.name}_step\n")
        flow_file.write(f"{ind}{ind}return {step.name}_step\n")
        flow_file.write("\n")

    return steps_param_meta, steps_vars

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


def get_return_var_names(step):
    results_index = step.code.find("results =")
    if results_index == -1:
        return []
    return [
        l.split(":")[1].strip(", \}")
        for l in step.code[results_index:].split("\n")
        if l.strip().find(":") > -1
    ]

# Cell


def format_args(params):
    result = []
    for key, val in params.items():
        # TODO simplify
        if val.instance_type == int:
            result.append(f"int({key})")
        elif val.instance_type == float:
            result.append(f"float({key})")
        else:
            result.append(key)
    return ", ".join(result)

# Cell


def generate_sagemaker_modules(
    flow_path,
    pipeline_class_name,
    lib_name,
    module_name,
    steps,
    params,
    steps_param_meta,
    steps_vars,
    track_experiment,
):
    # Read in module file as lines.
    ind = "    "
    module_path = Path(lib_path(), lib_name, f"{module_name.replace('.', '/')}.py")

    # Pass these in instead of replacting..
    fq_module_name = f"{lib_name}.{module_name}"
    extract_param_meta(fq_module_name, params)
    # TODO needs to be step specific
    # pass these in

    with open(module_path) as module_file:
        module_lines = module_file.readlines()
    lib_refs = []
    lines = []
    for line in module_lines:
        if line.startswith("from .."):
            lib_refs.append(line)
        else:
            lines.append(line)
    lib_refs = [l.replace("..", f"{lib_name}.") for l in lib_refs]

    for step in steps:
        sm_module_path = Path(str(flow_path).replace(".py", f"_{step.name}.py"))
        with open(sm_module_path, "w") as sm_module_file:
            sm_module_file.write("".join(lines))
            sm_module_file.write("\n\n# SCIFLOW->SAGEMAKER ADAPTER FROM THIS POINT\n")
            sm_module_file.write("import boto3\n")
            sm_module_file.write("import os\n")
            sm_module_file.write("import sys\n")
            sm_module_file.write("import pandas as pd\n")
            sm_module_file.write("import pickle\n")
            sm_module_file.write("from pathlib import Path\n")
            sm_module_file.write("import argparse\n")
            sm_module_file.write("import subprocess\n")
            sm_module_file.write("\n")
            write_preamble(step, sm_module_file, ind)
            sm_module_file.write("\n")
            sm_module_file.write("\n")
            if step.name in steps_param_meta and len(steps_param_meta[step.name]) > 0:
                step_args = list(steps_param_meta[step.name].keys())
                sm_module_file.write(
                    f"def main(lib_name, remote_key, {', '.join(step_args)}):\n"
                )
            else:
                sm_module_file.write(f"def main(lib_name, remote_key):\n")
            if is_processing_step(step):
                sm_module_file.write(
                    f'{ind}has_additional_dependencies = Path("/opt/ml/processing/requirements/requirements.txt").exists()\n'
                )
                sm_module_file.write(f"{ind}if has_additional_dependencies:\n")
                sm_module_file.write(
                    f"{ind}{ind}print('Installing additional dependencies from requirements.txt')\n"
                )
                sm_module_file.write(
                    f'{ind}{ind}subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "/opt/ml/processing/requirements/requirements.txt"])\n'
                )
                sm_module_file.write(
                    f'{ind}{ind}print("Installed additional dependencies")\n'
                )

            if (
                is_processing_step(step)
                and "step_train_vars" in steps_vars[step.name]
                and len(steps_vars[step.name]["step_train_vars"]) > 0
            ):
                sm_module_file.write(f"\n")
                sm_module_file.write(f"{ind}import tarfile\n")
                sm_module_file.write(
                    f'{ind}model_path = f"/opt/ml/processing/input/model/model.tar.gz"\n'
                )
                sm_module_file.write(f"{ind}with tarfile.open(model_path) as tar:\n")
                sm_module_file.write(f'{ind}{ind}tar.extractall(path=".")\n')
                sm_module_file.write(f"\n")

            sm_module_file.write(f"{ind}add_lib_to_pythonpath(lib_name, remote_key)\n")
            sm_module_file.write("".join([f"{ind}{lr}" for lr in lib_refs]))

            if is_processing_step(step):
                if (
                    "step_train_vars" in steps_vars[step.name]
                    and len(steps_vars[step.name]["step_train_vars"]) > 0
                ):
                    for step_train_var in steps_vars[step.name]["step_train_vars"]:
                        sm_module_file.write(
                            f'{ind}{step_train_var} = load_result(".", "{step_train_var}")\n'
                        )
                if (
                    "step_proc_vars" in steps_vars[step.name]
                    and len(steps_vars[step.name]["step_proc_vars"]) > 0
                ):
                    for step_proc_var in steps_vars[step.name]["step_proc_vars"]:
                        sm_module_file.write(
                            f'{ind}{step_proc_var} = load_result("/opt/ml/processing/input/{step_proc_var}", "{step_proc_var}")\n'
                        )
            elif is_train_step(step):
                if (
                    "step_proc_vars" in steps_vars[step.name]
                    and len(steps_vars[step.name]["step_proc_vars"]) > 0
                ):
                    for step_proc_var in steps_vars[step.name]["step_proc_vars"]:
                        sm_module_file.write(
                            f'{ind}{step_proc_var} = load_result("/opt/ml/input/data/{step_proc_var}", "{step_proc_var}")\n'
                        )

            args = ["lib_name", "remote_key"]

            step_func_args = []
            if len(steps_vars[step.name]) > 0:
                step_vars = (
                    steps_vars[step.name]["step_proc_vars"]
                    + steps_vars[step.name]["step_train_vars"]
                )
                # load result for each step var
                step_func_args.extend(step_vars)
            if step.name in steps_param_meta and len(steps_param_meta[step.name]) > 0:
                step_params = (
                    format_args(steps_param_meta[step.name]).replace(" ", "").split(",")
                )
                args.extend(step_args)
                step_func_args.extend(step_params)
            if len(step_func_args) > 0:
                step_func_args = ",".join(
                    [
                        f"{a.replace('int', '').replace('float', '').strip('()')}={a}"
                        for a in step_func_args
                    ]
                )
                sm_module_file.write(f"{ind}results = {step.name}({step_func_args})\n")
            else:
                sm_module_file.write(f"{ind}results = {step.name}()\n")
            if is_processing_step(step):
                sm_module_file.write(
                    f'{ind}save_results("/opt/ml/processing/output", results)\n'
                )
            elif is_train_step(step):
                sm_module_file.write(f'{ind}save_results("/opt/ml/model", results)\n')

            sm_module_file.write(f"\n")
            sm_module_file.write(f"def parse_args():\n")
            sm_module_file.write(
                f"{ind}parser = argparse.ArgumentParser(description=__doc__)\n"
            )
            sm_module_file.write(
                f"{ind}parser.formatter_class = argparse.RawDescriptionHelpFormatter\n"
            )

            for arg in args:
                sm_module_file.write(
                    f'{ind}parser.add_argument(f"--{arg}", required=True)\n'
                )
            sm_module_file.write(f"{ind}return parser.parse_args()")
            sm_module_file.write(f"\n")
            sm_module_file.write("\n")
            sm_module_file.write(f'if __name__ == "__main__":\n')
            sm_module_file.write(f"{ind}args = parse_args()\n")
            sm_module_file.write(f"{ind}main(**vars(args))\n")
            # write to flow path/step
        print(f"Created sagemaker module: {sm_module_path.name}")

# Cell


def generate_flows(config, track_experiment=True):
    nb_paths = nbglob(recursive=True)
    for nb_path in nb_paths:
        nb_to_sagemaker_pipeline(
            nb_path,
            get_flow_path(nb_path, flow_provider="sagemaker"),
            config,
            silent=False,
            track_experiment=False,
        )

# Cell


@call_parse
def sciflow_sagemaker(track: Param("Track flows as sacred experiments", bool) = True):
    generate_flows(get_config(), track)