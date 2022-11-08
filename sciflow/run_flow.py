# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/run_flow.ipynb (unless otherwise specified).

__all__ = ['check_is_init', 'make_shell_cmd', 'check_call_flow', 'check_call_flows', 'flow_task', 'run_flow_async',
           'run_flows_async', 'iter_param_grid', 'sample_grid_space', 'search_batches', 'search_flow_grid',
           'extract_results', 'sciflow_check_metaflows', 'sciflow_check_sagemaker_flows', 'sciflow_run_metaflows',
           'sciflow_run_sagemaker_flows']

# Cell


import asyncio
import multiprocessing
import os
import sys
from itertools import product
from pathlib import Path
from typing import Any, Dict, Iterable

import pandas as pd
from fastcore.script import call_parse
from nbdev.export import find_default_export, get_config, read_nb

from .utils import chunks, get_flow_path, prepare_env, run_shell_cmd

# Cell


def check_is_init():
    root_path = str(get_config().path("root_path"))

    if root_path not in sys.path:
        print(f"PYTHONPATH={sys.path}")
        raise ValueError("Project is not in path; have you run sciflow_init?")

# Cell


def make_shell_cmd(
    flow_nb_path, flow_provider="metaflow", flow_command="show", params=None
):
    prepare_env()
    if flow_nb_path.suffix == ".ipynb":
        flow_path = get_flow_path(flow_nb_path, flow_provider=flow_provider)
    else:
        flow_path = flow_nb_path
    if params:
        args = " ".join([f"--{k} {v}" for k, v in params.items()])

        flow_command = f"{flow_command} {args}"

    return f"python '{flow_path}' {flow_command}"

# Cell


def check_call_flow(
    flow_nb_path, flow_provider="metaflow", flow_command="show", params=None
):
    check_is_init()

    cmd = make_shell_cmd(flow_nb_path, flow_provider, flow_command, params)
    pipe, output = run_shell_cmd(cmd)
    return pipe.returncode, output

# Cell


def check_call_flows(
    config,
    flow_provider="metaflow",
    flow_command="show",
    ignore_suffix=None,
    exit_on_error=True,
):
    flow_results = {}
    flows_dir = Path(config.path("flows_path"), flow_provider)

    if ignore_suffix:
        flow_file_names = [
            p for p in os.listdir(flows_dir) if not p.endswith(ignore_suffix)
        ]
    else:
        flow_file_names = os.listdir(flows_dir)
    ret_codes = []
    exit_code = 0
    for flow_file_name in flow_file_names:
        flow_name = os.path.basename(flow_file_name)
        if flow_file_name.startswith("_sciflow"):
            continue
        if flow_file_name.endswith(".py"):
            ret_code, output = check_call_flow(
                Path(flows_dir, flow_file_name), flow_command=flow_command
            )
            flow_results[flow_name] = ret_code, output
            if ret_code == 0:
                print(f"Flow: {flow_name} {flow_command} verified")
            else:
                print(
                    f"Flow: {flow_name} {flow_command} verification failed\nDetails:\n{output}"
                )
            ret_codes.append(ret_code)
    if any([rc != 0 for rc in ret_codes]):
        exit_code = 1
        try:
            # Exit with an error code if running from a non interactive Python environment.
            get_ipython().__class__.__name__
        except NameError:
            if exit_on_error:
                return sys.exit(exit_code)
    return exit_code

# Cell


async def flow_task(
    flow_nb_path, flow_provider="metaflow", flow_command="run", params=None
):
    cmd = make_shell_cmd(flow_nb_path, flow_provider, flow_command, params)

    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()

    # print(f"[{cmd!r} exited with {proc.returncode}]")
    err = ""
    out = ""
    if stderr:
        err = f'[stderr]\n{stderr.decode("utf-8").strip()}'
    if stdout:
        out = f'[stdout]\n{stdout.decode("utf-8").strip()}'

    return proc.returncode, err + out

# Cell


def run_flow_async(
    flow_nb_path, flow_provider="metaflow", flow_command="run", params=None
):
    loop = asyncio.get_event_loop()
    task = loop.create_task(
        flow_task(flow_nb_path, flow_provider, flow_command, params)
    )
    return task

# Cell


async def run_flows_async(
    config,
    flow_provider="metaflow",
    flow_command="run",
    params=None,
    ignore_suffix=None,
    exit_on_error=True,
):
    flow_tasks = {}
    flows_dir = Path(config.path("flows_path"), flow_provider)

    if ignore_suffix:
        flow_file_names = [
            p for p in os.listdir(flows_dir) if not p.endswith(ignore_suffix)
        ]
    else:
        flow_file_names = os.listdir(flows_dir)
    ret_codes = []
    exit_code = 0
    loop = asyncio.get_event_loop()

    for flow_file_name in flow_file_names:
        flow_name = os.path.basename(flow_file_name)
        if flow_file_name.startswith("_sciflow"):
            continue
        if flow_file_name.endswith(".py"):
            task = loop.create_task(
                flow_task(
                    Path(flows_dir, flow_file_name), flow_provider, flow_command, params
                )
            )
            flow_tasks[flow_name] = task

    for flow_name, task in flow_tasks.items():
        await task
        ret_code = task.result()[0]
        if ret_code == 0:
            print(f"Flow: {flow_name} {flow_command} verified")
        else:
            print(
                f"Flow: {flow_name} {flow_command} verification failed\nDetails:\n{output}"
            )
        ret_codes.append(ret_code)
    if any([rc != 0 for rc in ret_codes]):
        exit_code = 1
        try:
            # Exit with an error code if running from a non interactive Python environment.
            get_ipython().__class__.__name__
        except NameError:
            if exit_on_error:
                return sys.exit(exit_code)
    return exit_code

# Cell


def iter_param_grid(param_grid):
    # https://github.com/scikit-learn/scikit-learn/blob/main/sklearn/model_selection/_search.py
    for p in [param_grid]:
        # Always sort the keys of a dictionary, for reproducibility
        items = sorted(p.items())
        if not items:
            yield {}
        else:
            keys, values = zip(*items)
            for v in product(*values):
                params = dict(zip(keys, v))
                yield params

# Cell


def sample_grid_space(param_grid: Dict[str, Iterable[Any]], num_samples: int):
    samples = []
    for i, sample in enumerate(iter_param_grid(param_grid)):
        samples.append(sample)
    if num_samples < len(samples):
        samples = pd.Series(samples).sample(num_samples).tolist()
    return samples

# Cell


async def search_batches(flow_nb_path, flow_provider, task_batches):
    futures = []
    loop = asyncio.get_event_loop()
    for task_batch in task_batches:
        tasks = [
            (
                loop.create_task(
                    flow_task(
                        flow_nb_path,
                        flow_provider,
                        flow_command="run",
                        params=param_spec,
                    )
                )
            )
            for param_spec in task_batch
        ]
        futures.append(await asyncio.wait(tasks))
    return futures

# Cell


def search_flow_grid(
    flow_nb_path,
    param_grid,
    flow_provider="metaflow",
    total_tasks=None,
    n_conc_tasks=None,
    local_mode=True,
):
    if total_tasks is None:
        total_tasks = len(list(iter_param_grid(param_grid)))

    if local_mode and n_conc_tasks is None:
        n_conc_tasks = int((multiprocessing.cpu_count() / 2) - 1)

    sample_space = sample_grid_space(param_grid, total_tasks)
    task_batches = list(chunks(sample_space, n_conc_tasks))
    futures = search_batches(flow_nb_path, flow_provider, task_batches)
    return futures

# Cell


def extract_results(future_tasks):
    completed_tasks = [
        item for sublist in [list(ft[0]) for ft in future_tasks] for item in sublist
    ]
    results = [t.result() for t in completed_tasks]
    return results

# Cell


@call_parse
def sciflow_check_metaflows():
    check_call_flows(get_config())

# Cell


@call_parse
def sciflow_check_sagemaker_flows():
    check_call_flows(get_config(), flow_provider="sagemaker")

# Cell


@call_parse
def sciflow_run_metaflows():
    check_call_flows(get_config(), flow_command="run")

# Cell


@call_parse
def sciflow_run_sagemaker_flows():
    check_call_flows(get_config(), flow_command="run", flow_provider="sagemaker")