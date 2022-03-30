# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/to_sagemaker.ipynb (unless otherwise specified).

__all__ = ['nb_to_sagemaker_pipeline', 'is_train_step', 'is_processing_step', 'write_pipeline_to_files',
           'write_observers', 'write_track_flow', 'write_params', 'upload_directory', 'download_directory',
           'extract_step_vars', 'format_job_arguments', 'format_arg', 'write_steps', 'create_sm_dag',
           'write_track_capture', 'get_return_var_names']

# Cell


import os
from pathlib import Path
from typing import Iterable

from nbdev.export import find_default_export, get_config, read_nb

from .data_handler import extract_param_meta
from .params import params_as_dict
from .parse_module import FuncDetails, extract_steps
from .utils import lib_path

# Cell


def nb_to_sagemaker_pipeline(
    nb_path: Path, flow_path: Path, silent=True, track_experiment=True
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
        get_config().path("lib_path"), f"{path_sep_module_name}.py"
    )
    steps = extract_steps(exported_module)
    if len(steps) == 0:
        print("Skipping sagemaker conversion - not steps found")
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
    with open(flow_path, "w") as flow_file:
        flow_file.write("#!/usr/bin/env python\n")
        flow_file.write("# coding=utf-8\n")
        flow_file.write("# SCIFLOW GENERATED FILE - EDIT COMPANION NOTEBOOK\n")

        flow_file.write("import os\n")
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
        single_indent = "    "
        write_params(flow_file, param_meta, single_indent)
        flow_file.write("\n")
        flow_file.write(f"{single_indent}steps = {[s.name for s in steps]}\n")
        flow_file.write("\n")
        write_steps(
            module_name,
            fq_module_name,
            flow_file,
            steps,
            param_meta,
            single_indent,
            track_experiment,
        )
        flow_file.write("\n")

        flow_file.write(f"{single_indent}def get_pipeline(self) -> Pipeline:\n")
        flow_file.write(f"{single_indent}{single_indent}pipeline_steps = [getattr(self, step)() for step in self.steps]\n")
        flow_file.write(f"{single_indent}{single_indent}pipeline = Pipeline(\n")
        flow_file.write(f"{single_indent}{single_indent}{single_indent}name=self.flow_name,\n")
        flow_file.write(f"{single_indent}{single_indent}{single_indent}parameters=[\n")
        # Loop params
        for param_name in params.keys():
            flow_file.write(f"{single_indent}{single_indent}{single_indent}{single_indent}self.{param_name},\n")
        flow_file.write(f"{single_indent}{single_indent}{single_indent}],\n")
        flow_file.write(f"{single_indent}{single_indent}{single_indent}steps = pipeline_steps,\n")
        flow_file.write(f"{single_indent}{single_indent}{single_indent}sagemaker_session = self.sagemaker_session,\n")
        flow_file.write(f"{single_indent}{single_indent})\n")
        flow_file.write(f"{single_indent}{single_indent}return pipeline\n")
        flow_file.write("\n")

        flow_file.write(f"{single_indent}def run(self):\n")
        flow_file.write(f"{single_indent}{single_indent}self.bucket = os.environ['SCIFLOW_BUCKET']\n")
        flow_file.write(f"{single_indent}{single_indent}self.role = sagemaker.get_execution_role()\n")
        flow_file.write(f"{single_indent}{single_indent}self.region = 'eu-west-1'\n")
        flow_file.write(f"{single_indent}{single_indent}self.sagemaker_session = Session(default_bucket=self.bucket)\n\n")
        flow_file.write(f"{single_indent}{single_indent}self.flow_name = \"{extract_module_only(module_name).replace('_', '-')}\"\n")
        flow_file.write(f"{single_indent}{single_indent}run_timestamp = datetime.today().__str__().replace(':', '-').replace('.', '-').replace(' ', '-')[:-3]\n")
        flow_file.write(f"{single_indent}{single_indent}self.flow_run_id = f\"pipeline-{{run_timestamp}}\"\n")
        flow_file.write(f"{single_indent}{single_indent}self.s3_prefix = f\"{{self.flow_name}}/{{self.flow_run_id}}\"\n")
        flow_file.write(f"{single_indent}{single_indent}self.flow_s3_uri = f\"s3://{{self.bucket}}/{{self.s3_prefix}}\"\n")
        flow_file.write(f"{single_indent}{single_indent}self.s3_client = boto3.client(\"s3\")\n")

        proc_steps = [s for s in steps if is_processing_step(s)]

        for proc_step in proc_steps:
            flow_file.write(f"{single_indent}{single_indent}self.s3_client.upload_file(\"test_clustering_{proc_step.name}.py\", self.bucket, f\"{{self.s3_prefix}}/code/test_clustering_{proc_step.name}.py\")\n")

        modules_dir = Path(lib_path(), get_config().lib_name)
        flow_file.write(f"{single_indent}{single_indent}upload_directory(self.s3_client, \"{modules_dir}\", self.bucket, f\"{{self.s3_prefix}}/code/{get_config().lib_name}\")\n")
        flow_file.write("\n")
        flow_file.write(f"{single_indent}{single_indent}pipeline = self.get_pipeline()\n")
        flow_file.write(f"{single_indent}{single_indent}pipeline.upsert(role_arn=self.role)\n")
        flow_file.write(f"{single_indent}{single_indent}execution = pipeline.start()\n")
        flow_file.write(f"{single_indent}{single_indent}execution.wait()\n")
        flow_file.write("\n")

        flow_file.write('if __name__ == "__main__":\n')
        flow_file.write(f"{single_indent}{pipeline_class_name}().run()")

# Cell


def write_observers(lib_name, flow_file, module_name, bucket_name, project):
    pass

# Cell


def write_track_flow(flow_file, track_experiment):
    pass

# Cell


def write_params(flow_file, param_meta, single_indent):
    for param in param_meta.keys():
        if param_meta[param].instance_type == int:
            flow_file.write(
                f"{single_indent}{param} = ParameterInteger(name='{param}', default_value={param})\n"
            )
        elif param_meta[param].instance_type == float:
            flow_file.write(
                f"{single_indent}{param} = ParameterFloat(name='{param}', default_value={param})\n"
            )
        elif param_meta[param].instance_type == str:
            flow_file.write(
                f"{single_indent}{param} = ParameterString(name='{param}', default_value={param})\n"
            )

# Cell


def upload_directory(s3_res, path, bucketname, prefix):
    for root, dirs, files in os.walk(path):
        # Ignore non-python source files and IPython checkpoint files
        for file in [
            f
            for f in files
            if f.split(".")[-1] == "py" and root.find("ipynb_checkpoints") == -1
        ]:
            pass
            # print(os.path.join(root, file), bucketname, f"{prefix}{file}", file.find('ipynb_checkpoints'))
            s3_res.upload_file(os.path.join(root, file), bucketname, f"{prefix}{file}")

# Cell


def download_directory(bucketname, remote_key, local_dir):
    from pathlib import Path

    import boto3

    s3 = boto3.client("s3")
    if not Path(local_dir).exists():
        Path(local_dir).mkdir()
    all_files = [
        obj.key
        for obj in boto3.resource("s3")
        .Bucket(bucketname)
        .objects.filter(Prefix=remote_key)
    ]
    for file in all_files:
        file_name = file.split("/")[-1]
        s3.download_file(bucketname, file, f"{local_dir}/{file_name}")

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


def format_arg(arg, param_meta):
    if arg in param_meta and not param_meta[arg].has_metaflow_param:
        result = arg
    else:
        result = "self." + arg
    return result


def write_steps(
    module_name, fq_module_name, flow_file, steps, param_meta, single_indent, track_experiment
):
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

        flow_file.write(f"{single_indent}def {step.name}(self):\n")
        if step.docstring:
            flow_file.write(f"{indent_multiline(step.docstring, 2)}\n")
        # Processing step
        if is_processing_step(step):
            write_script_processor(flow_file, single_indent)

            flow_file.write("\n")
            flow_file.write(
                f"{single_indent}{single_indent}{step.name}_step = ProcessingStep(\n"
            )
            flow_file.write(
                f'{single_indent}{single_indent}{single_indent}name = "{step.name}",\n'
            )
            flow_file.write(
                f"{single_indent}{single_indent}{single_indent}processor = script_processor,\n"
            )
            flow_file.write(
                f"{single_indent}{single_indent}{single_indent}code = f\"{{self.flow_s3_uri}}/code/{module_local_name}_{step.name}.py\",\n"
            )
            if len(step_vars) > 0:
                step_param_meta = {k: param_meta[k] for k in step_vars["step_input"]}
                if len(step_param_meta) > 0:
                    # Job Args
                    job_args = format_job_arguments(step_param_meta)
                    flow_file.write(
                        f"{single_indent}{single_indent}{single_indent}job_arguments=[\n"
                    )
                    job_arg_pairs = zip(job_args[::2], job_args[1::2])
                    for job_arg_pair in job_arg_pairs:
                        flow_file.write(
                            f'{single_indent}{single_indent}{single_indent}{single_indent}"{job_arg_pair[0]}", {job_arg_pair[1]},\n'
                        )
                    flow_file.write(
                        f"{single_indent}{single_indent}{single_indent}],\n"
                    )

                # ProcInputs
                if (
                    len(step_vars["step_proc_vars"]) > 0
                    or len(step_vars["step_train_vars"]) > 0
                ):
                    flow_file.write(
                        f"{single_indent}{single_indent}{single_indent}inputs = [\n"
                    )
                    flow_file.write(
                        "\n".join(
                            [
                                f'{single_indent}{single_indent}{single_indent}{single_indent}ProcessingInput(source=self.{outputs[cv]}, destination="/opt/ml/processing/{cv}"),\n'
                                for cv in step_vars["step_train_vars"]
                                + step_vars["step_proc_vars"]
                            ]
                        )
                    )
                    flow_file.write(
                        f"{single_indent}{single_indent}{single_indent}],\n"
                    )

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
                    flow_file.write(
                        f"{single_indent}{single_indent}{single_indent}outputs = [\n"
                    )
                    flow_file.write(
                        "\n".join(
                            [
                                f'{single_indent}{single_indent}{single_indent}{single_indent}ProcessingOutput(output_name="{v}", source="/opt/ml/processing/{v}"),'
                                for v in [x[0] for x in proc_outs]
                            ]
                        )
                        + "\n"
                    )
                    flow_file.write(f"{single_indent}{single_indent}{single_indent}]\n")

            flow_file.write(f"{single_indent}{single_indent})\n")
            proc_flow_scope.extend(return_vars)
        elif is_train_step(step):
            if len(step_vars) > 0:
                # if len(step.args) > 0:
                #    print(f"Step Args: {step.args}")
                # if len(step_vars['step_input']) > 0:
                #    print(f"Hyperparameters: {step_vars['step_input']}")
                # print(f"Args that are params: {input_vars}")
                # print(f"Args that are in flow scope: {created_vars}")
                #
                # if len(step_vars['step_proc_vars']) > 0:
                #    print(f"TrainingInputs: {[outputs[cv] for cv in step_vars['step_proc_vars']]}")
                train_outs = {
                    (v, f"{step.name}_step.properties.ModelArtifacts.S3ModelArtifacts")
                    for v in return_vars
                }
                outputs.update(train_outs)
                train_flow_scope.extend(return_vars)

                flow_file.write(f"{single_indent}{single_indent}metrics_regex = None\n")
                flow_file.write(f"{single_indent}{single_indent}if 'metric_names' in self.__dict__:\n")
                flow_file.write(
                    f"{single_indent}{single_indent}{single_indent}metrics = self.metric_names.split(\",\")\n",
                )
                flow_file.write(
                    f'{single_indent}{single_indent}{single_indent}metrics_regex = [{{"Name": m, "Regex": f"{{m}}=(.*?);"}} for m in metrics]\n'
                )
                flow_file.write(f"\n")
                flow_file.write(
                    f"{single_indent}{single_indent}estimator = Estimator(\n"
                )
                flow_file.write(
                    f'{single_indent}{single_indent}{single_indent}image_uri = "141502667606.dkr.ecr.eu-west-1.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3",\n'
                )
                flow_file.write(
                    f'{single_indent}{single_indent}{single_indent}entry_point="{module_local_name}_{step.name}.py",\n'
                )
                flow_file.write(
                    f'{single_indent}{single_indent}{single_indent}hyperparameters={{"workers": str(self.workers.__int__())}},\n'
                )
                flow_file.write(
                    f'{single_indent}{single_indent}{single_indent}instance_type="ml.m5.xlarge",\n'
                )
                flow_file.write(
                    f"{single_indent}{single_indent}{single_indent}instance_count=1,\n"
                )
                flow_file.write(
                    f"{single_indent}{single_indent}{single_indent}output_path=self.flow_s3_uri,\n"
                )
                flow_file.write(
                    f"{single_indent}{single_indent}{single_indent}base_job_name=\"{step.name}\",\n"
                )
                flow_file.write(f"{single_indent}{single_indent}{single_indent}code_location = f\"{{self.flow_s3_uri}}/code\",\n")
                flow_file.write(
                    f"{single_indent}{single_indent}{single_indent}sagemaker_session = self.sagemaker_session,\n"
                )
                flow_file.write(
                    f"{single_indent}{single_indent}{single_indent}role = self.role,\n"
                )
                flow_file.write(
                    f"{single_indent}{single_indent}{single_indent}metric_definitions=metrics_regex,\n"
                )
                flow_file.write(
                    f"{single_indent}{single_indent}{single_indent}enable_sagemaker_metrics=True,\n"
                )
                flow_file.write(
                    f"{single_indent}{single_indent}{single_indent}environment={{'AWS_DEFAULT_REGION': self.region,\n"
                )
                flow_file.write(
                    f"{single_indent}{single_indent}{single_indent}{single_indent}{single_indent}'SCIFLOW_BUCKET': self.bucket}}\n"
                )

                flow_file.write(f"{single_indent}{single_indent})\n")
                flow_file.write("\n")
                flow_file.write("\n")
                flow_file.write(
                    f"{single_indent}{single_indent}{step.name}_step = TrainingStep(\n"
                )
                flow_file.write(
                    f'{single_indent}{single_indent}{single_indent}name="{step.name}",\n'
                )
                flow_file.write(
                    f"{single_indent}{single_indent}{single_indent}estimator=estimator,\n"
                )
                flow_file.write(
                    f"{single_indent}{single_indent}{single_indent}inputs={{\n"
                )
                flow_file.write(
                    f'{single_indent}{single_indent}{single_indent}{single_indent}"documents": TrainingInput(\n'
                )
                flow_file.write(
                    f"{single_indent}{single_indent}{single_indent}{single_indent}{single_indent}s3_data=self.preprocess_step.properties.ProcessingOutputConfig.Outputs[\n"
                )
                flow_file.write(
                    f'{single_indent}{single_indent}{single_indent}{single_indent}{single_indent}{single_indent}"documents"\n'
                )
                flow_file.write(
                    f"{single_indent}{single_indent}{single_indent}{single_indent}{single_indent}].S3Output.S3Uri,\n"
                )
                flow_file.write(
                    f'{single_indent}{single_indent}{single_indent}{single_indent}{single_indent}content_type="text/csv",\n'
                )
                flow_file.write(
                    f"{single_indent}{single_indent}{single_indent}{single_indent})\n"
                )
                flow_file.write(f"{single_indent}{single_indent}{single_indent}}}\n")
                flow_file.write(f"{single_indent}{single_indent})\n")

        flow_file.write(
            f"{single_indent}{single_indent}self.{step.name}_step = {step.name}_step\n"
        )
        flow_file.write(f"{single_indent}{single_indent}return {step.name}_step\n")
        flow_file.write("\n")

# Cell


def create_sm_dag(steps, param_meta):
    param_names = list(param_meta.keys())
    proc_flow_scope = []
    train_flow_scope = []
    outputs = {}
    for step in steps:
        return_vars = get_return_var_names(step)
        step_vars = extract_step_vars(
            step, param_names, proc_flow_scope, train_flow_scope
        )
        if is_processing_step(step):
            print(f"Step: {step.name}")
            # if len(step.args) > 0:
            #    print(f"Step Args: {step.args}")
            if len(step_vars) > 0:
                if len(step_vars["step_input"]) > 0:
                    step_param_meta = {
                        k: param_meta[k] for k in step_vars["step_input"]
                    }
                    print(f"job_arguments={format_job_arguments(step_param_meta)}")
                # print(f"Args that are in flow scope: {created_vars}")
                if (
                    len(step_vars["step_proc_vars"]) > 0
                    or len(step_vars["step_train_vars"]) > 0
                ):
                    print(
                        f"ProcessingInputs: {[outputs[cv] for cv in step_vars['step_train_vars'] + step_vars['step_proc_vars']]}"
                    )
                proc_outs = {
                    (
                        v,
                        f'step_{step.name}.properties.ProcessingOutputConfig.Outputs["{v}"].S3Output.S3Uri',
                    )
                    for v in return_vars
                }
                outputs.update(proc_outs)
                if len(proc_outs) > 0:
                    print(f"ProcessingOutputs: {proc_outs}")
                print(f"Processing Flow scope extended by: {return_vars}")
                proc_flow_scope.extend(return_vars)
        elif is_train_step(step):
            print(f"Step: {step.name}")
            if len(step_vars) > 0:
                # if len(step.args) > 0:
                #    print(f"Step Args: {step.args}")
                if len(step_vars["step_input"]) > 0:
                    print(f"Hyperparameters: {step_vars['step_input']}")
                # print(f"Args that are params: {input_vars}")
                # print(f"Args that are in flow scope: {created_vars}")
                if len(step_vars["step_proc_vars"]) > 0:
                    print(
                        f"TrainingInputs: {[outputs[cv] for cv in step_vars['step_proc_vars']]}"
                    )
                train_outs = {
                    (v, f"step_{step.name}.properties.ModelArtifacts.S3ModelArtifacts")
                    for v in return_vars
                }
                outputs.update(train_outs)
                print(f"Training Flow scope extended by: {return_vars}")
                train_flow_scope.extend(return_vars)
        print("\n")

    # ProcessingInput comes from params or from preceding ste

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