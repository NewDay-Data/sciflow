# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/tracking.ipynb (unless otherwise specified).

__all__ = ['save_json', 'FlowTracker', 'StepTracker']

# Cell


import datetime
import json
import sys
import tempfile
import time
import traceback as tb
import uuid
from pathlib import Path

import boto3
import pandas as pd
from sacred import metrics_logger
from sacred.host_info import get_host_info
from sacred.serializer import flatten
from sacred.stdout_capturing import get_stdcapturer
from sacred.utils import IntervalTimer

from ..s3_utils import list_bucket, load_json, put_data, s3_join
from ..utils import prepare_env

# Cell
# TODO replace the sacred flatten function and mvoe to s3_utils - needs a jsonpickle serialiser


def save_json(s3_res, bucket_name, key, filename, obj):
    key = s3_join(key, filename)
    put_data(
        s3_res, bucket_name, key, json.dumps(flatten(obj), sort_keys=True, indent=2)
    )

# Cell


class FlowTracker:
    def __init__(
        self, bucket_name, flow_base_key, flow_run_id, steps, region="eu-west-1"
    ):
        self.bucket_name = bucket_name
        self.flow_base_key = flow_base_key
        self.flow_run_id = flow_run_id
        self.steps = steps

        if region is not None:
            self.region = region
            self.s3_res = boto3.resource("s3", region_name=region)
        else:
            session = boto3.session.Session()
            if session.region_name is not None:
                self.region = session.region_name
                self.s3 = boto3.resource("s3")
            else:
                raise ValueError(
                    "You must either pass in an AWS region name, or have a "
                    "region name specified in your AWS config file"
                )

        self.run_entry_key = s3_join(flow_base_key, flow_run_id, "experiment", "runs")
        self.runs_table_key = s3_join(flow_base_key, "experiments", "runs", flow_run_id)

    def start(self, params=None):
        host_info = get_host_info()
        run_entry = {
            "experiment_id": flow_run_id,
            "experiment": {},
            "format": None,
            "command": None,
            "host": host_info,
            "start_time": time.time(),
            "config": params,
            "meta": {},
            "status": "RUNNING",
            "resources": [],
            "artifacts": [],
            "captured_out": "",
            "info": {},
            "heartbeat": None,
            "steps": steps,
        }

        save_json(s3_res, bucket_name, self.run_entry_key, "run.json", run_entry)
        save_json(
            s3_res, bucket_name, self.run_entry_key, "flow_start_run.json", run_entry
        )
        save_json(s3_res, bucket_name, self.runs_table_key, "run.json", run_entry)
        print(f"Started tracking flow: {flow_run_id}")

    def interrupted(self):
        self._tracking_event("INTERRUPTED")
        print(f"Flow tracking interrupted: {flow_run_id}")

    def failed(self, except_info):
        self._tracking_event("FAILED", except_info)
        print(f"Flow tracking failed: {flow_run_id}")

    def completed(self):
        self._tracking_event("COMPLETED")
        print(f"Flow tracking completed: {flow_run_id}")

    def _tracking_event(self, event_status, except_info=None):
        run_entry = load_json(
            self.s3_res, self.bucket_name, s3_join(self.run_entry_key, "run.json")
        )
        run_entry["status"] = event_status
        run_entry["stop_time"] = time.time()
        run_entry["elapsed_time"] = round(
            run_entry["stop_time"] - run_entry["start_time"], 2
        )
        if except_info is not None:
            run_entry["fail_trace"] = tb.format_exception(
                except_info["exc_type"], except_info["exc_value"], except_info["trace"]
            )

        run_entry = self._merge_step_entries(run_entry)
        save_json(s3_res, bucket_name, self.run_entry_key, "run.json", run_entry)
        save_json(s3_res, bucket_name, self.runs_table_key, "run.json", run_entry)

    def _merge_step_entries(self, run_entry):
        all_hosts = {}
        captured_out = ""
        step_entries = {}
        for step in steps:
            step_entry = load_json(
                self.s3_res,
                self.bucket_name,
                s3_join(self.run_entry_key, f"step_{step}.json"),
            )
            all_hosts[step] = step_entry["host"]
            step_out = (
                "" if step_entry["captured_out"] is None else step_entry["captured_out"]
            )
            captured_out += f"******BEGIN step: {step}******\n"
            captured_out += step_out
            captured_out += f"******END step: {step}******\n"
            step_entries[step] = step_entry
        run_entry["all_hosts"] = all_hosts
        run_entry["captured_out"] = captured_out
        run_entry["steps"] = steps
        run_entry["step_entries"] = step_entries
        return run_entry

# Cell


class StepTracker(SciflowTracker):
    def __init__(
        self,
        bucket_name,
        flow_base_key,
        flow_run_id,
        step_name,
        capture_mode="sys",
        region="eu-west-1",
    ):
        self.bucket_name = bucket_name
        self.flow_base_key = flow_base_key
        self.flow_run_id = flow_run_id
        self.exp_base_key = s3_join(flow_base_key, flow_run_id, "experiment")
        self.step_name = step_name
        self.capture_mode = capture_mode
        self._stop_heartbeat_event = None
        self._heartbeat = None
        self._output_file = None
        self._metrics = metrics_logger.MetricsLogger()
        self.captured_out = None
        self.saved_metrics = {}
        self.info = {}
        self.result = None
        self.start_time = time.time()

        self.flow_start_run_entry = load_json(
            s3_res,
            bucket_name,
            s3_join(self.exp_base_key, "runs", "flow_start_run.json"),
        )
        self.run_entry = self.flow_start_run_entry

        if region is not None:
            self.region = region
            self.s3_res = boto3.resource("s3", region_name=region)
        else:
            session = boto3.session.Session()
            if session.region_name is not None:
                self.region = session.region_name
                self.s3_res = boto3.resource("s3")
            else:
                raise ValueError(
                    "You must either pass in an AWS region name, or have a "
                    "region name specified in your AWS config file"
                )

        self.init_keys()

    def start_heartbeat(self, beat_interval=10.0):
        print("Starting Heartbeat")
        self._stop_heartbeat_event, self._heartbeat = IntervalTimer.create(
            self._emit_heartbeat, beat_interval
        )
        self._heartbeat.start()

    def stop_heartbeat(self):
        print("Stopping Heartbeat")
        if self._heartbeat is not None:
            self._stop_heartbeat_event.set()
            self._heartbeat.join(timeout=2)

    def capture_out(self):
        # TODO figure out why only "sys" seems to work in Sagemaker? - tee is installed
        _, capture_stdout = get_stdcapturer(self.capture_mode)
        return capture_stdout()

    def get_captured_out(self):
        if self._output_file.closed:
            return
        text = self._output_file.get()
        if isinstance(text, bytes):
            text = text.decode("utf-8", "replace")
        if self.captured_out:
            text = self.captured_out + text
        self.captured_out = text

    def log_metric(self, metric_name, metric_value, metric_step):
        if metric_name not in self.saved_metrics:
            self.saved_metrics[metric_name] = {
                "values": [],
                "steps": [],
                "timestamps": [],
            }

        self.saved_metrics[metric_name]["values"].append(metric_value)
        self.saved_metrics[metric_name]["steps"].append(metric_step)
        self.saved_metrics[metric_name]["timestamps"].append(
            datetime.datetime.utcnow().isoformat()
        )
        save_json(
            self.s3_res,
            self.bucket_name,
            self.metrics_key,
            "metrics.json",
            self.saved_metrics,
        )
        save_json(
            self.s3_res,
            self.bucket_name,
            self.metrics_table_key,
            "metrics.json",
            self.saved_metrics,
        )

    def add_artifact(self, artifact_path):
        name = Path(artifact_path).name
        self.save_file(self.artifacts_key, artifact_path, name)
        self.save_file(self.artifacts_table_key, artifact_path, name)
        self.run_entry["artifacts"].append(name)
        save_json(
            self.s3_res, self.bucket_name, self.runs_key, "run.json", self.run_entry
        )
        save_json(
            self.s3_res,
            self.bucket_name,
            self.runs_key,
            f"step_{self.step_name}.json",
            self.run_entry,
        )

    def _emit_heartbeat(self):
        beat_time = datetime.datetime.utcnow().isoformat()
        self.run_entry["heartbeat"] = beat_time
        print(f"Emitted heartbeat at: {beat_time}")
        self.run_entry["captured_out"] = self.get_captured_out()
        self.run_entry["result"] = self.result
        save_json(
            self.s3_res, self.bucket_name, self.runs_key, "run.json", self.run_entry
        )
        save_json(
            self.s3_res,
            self.bucket_name,
            self.runs_key,
            f"step_{self.step_name}.json",
            self.run_entry,
        )

    def completed(self, status="COMPLETED", except_info=None):
        self.stop_heartbeat()
        self.get_captured_out()
        self.run_entry["captured_out"] = self.captured_out
        self.run_entry["result"] = self.result
        save_json(
            self.s3_res, self.bucket_name, self.runs_key, "run.json", self.run_entry
        )
        self.run_entry["status"] = status
        self.run_entry["stop_time"] = time.time()
        self.run_entry["elapsed_time"] = round(
            self.run_entry["stop_time"] - self.start_time, 2
        )
        self.run_entry["host"] = get_host_info()
        if except_info is not None:
            self.run_entry["fail_trace"] = tb.format_exception(
                except_info["exc_type"], except_info["exc_value"], except_info["trace"]
            )
        save_json(
            self.s3_res,
            self.bucket_name,
            self.runs_key,
            f"step_{self.step_name}.json",
            self.run_entry,
        )

    def save_file(self, file_save_dir, filename, target_name=None):
        target_name = target_name or os.path.basename(filename)
        key = s3_join(file_save_dir, target_name)
        put_data(self.s3_res, self.bucket_name, key, open(filename, "rb"))

    def init_keys(self):
        self.runs_key = s3_join(self.exp_base_key, "runs")
        self.metrics_key = s3_join(self.exp_base_key, "metrics")
        self.artifacts_key = s3_join(self.exp_base_key, "artifacts")
        self.resource_key = s3_join(self.exp_base_key, "resources")
        self.source_key = s3_join(self.exp_base_key, "sources")
        self.metrics_table_key = s3_join(
            self.flow_base_key, "experiments", "metrics", flow_run_id
        )
        self.artifacts_table_key = s3_join(
            self.flow_base_key, "experiments", "artifacts", flow_run_id
        )

        self.keys = (
            self.runs_key,
            self.metrics_key,
            self.artifacts_key,
            self.resource_key,
            self.source_key,
        )