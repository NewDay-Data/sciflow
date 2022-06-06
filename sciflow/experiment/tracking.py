# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/tracking.ipynb (unless otherwise specified).

__all__ = ['save_json', 'tracking_started', 'tracking_interrupted', 'tracking_failed', 'tracking_completed',
           'StepTracker']

# Cell


import datetime
from datetime import timedelta
import json
import socket
import time
import uuid
from pathlib import Path
import tempfile

import pandas as pd
import boto3
from botocore.exceptions import ClientError
import pandas as pd
from sacred import metrics_logger
from sacred.host_info import get_host_info
from sacred.serializer import flatten
from sacred.stdout_capturing import get_stdcapturer
from sacred.utils import IntervalTimer
from ..utils import prepare_env

from ..s3_utils import (
    delete_dir,
    list_bucket,
    objects_exist_in_dir,
    put_data,
    s3_join,
    load_json
)

# Cell


def save_json(s3_res, bucket_name, key, filename, obj):
    key = s3_join(key, filename)
    put_data(
        s3_res, bucket_name, key, json.dumps(flatten(obj), sort_keys=True, indent=2)
    )

# Cell


def tracking_started(s3_res, bucket_name, flow_base_key, flow_run_id):
    # Create run-entry
    # Write run.json
    # experiment = experiment_info - sacred.ingredient.experiment_info
    # Command = run_flow?
    # Config = params?
    # meta = startup metadata put in FlowTracker

    host_info = get_host_info()
    run_entry = {
        "experiment_id": flow_run_id,
        "experiment": {},
        "format": None,
        "command": None,
        "host": host_info,
        "all_hosts": {socket.gethostname(): host_info},
        "start_time": time.time(),
        "config": {},
        "meta": {},
        "status": "RUNNING",
        "resources": [],
        "artifacts": [],
        "captured_out": "",
        "info": {},
        "heartbeat": None,
    }

    runs_key = s3_join(flow_base_key, flow_run_id, "experiment", "runs")
    save_json(s3_res, bucket_name, runs_key, "run.json", run_entry)
    save_json(s3_res, bucket_name, runs_key, "flow_start_run.json", run_entry)
    print(f"Started tracking flow: {flow_run_id}")

# Cell


def _tracking_event(s3_res, bucket_name, flow_base_key, flow_run_id, event_status):
    run_entry_key = s3_join(flow_base_key, flow_run_id, "experiment", "runs")
    run_entry = load_json(s3_res, bucket_name, s3_join(run_entry_key, "run.json"))
    run_entry["status"] = event_status
    run_entry["stop_time"] = time.time()
    run_entry["elapsed_time"] = round(run_entry["stop_time"] - run_entry["start_time"], 2)
    save_json(s3_res, bucket_name, run_entry_key, "run.json", run_entry)

# Cell


def tracking_interrupted(s3_res, bucket_name, flow_base_key, flow_run_id):
    _tracking_event(s3_res, bucket_name, flow_base_key, flow_run_id, "INTERRUPTED")
    print(f"Flow tracking interrupted: {flow_run_id}")

# Cell


def tracking_failed(s3_res, bucket_name, flow_base_key, flow_run_id):
    _tracking_event(s3_res, bucket_name, flow_base_key, flow_run_id, "FAILED")
    print(f"Flow tracking failed: {flow_run_id}")

# Cell


def tracking_completed(s3_res, bucket_name, flow_base_key, flow_run_id):
    _tracking_event(s3_res, bucket_name, flow_base_key, flow_run_id, "COMPLETED")
    print(f"Flow tracking completed: {flow_run_id}")

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

        self.flow_start_run_entry = load_json(s3_res, bucket_name, s3_join(self.exp_base_key, "runs", "flow_start_run.json"))
        self.run_entry = self.flow_start_run_entry
        self.run_entry["all_hosts"][socket.gethostname()] = get_host_info()

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

    def add_artifact(self, artifact_path):
        name = Path(artifact_path).name
        self.save_file(self.artifacts_key, artifact_path, name)
        self.run_entry["artifacts"].append(name)
        save_json(
            self.s3_res, self.bucket_name, self.runs_key, "run.json", self.run_entry
        )
        save_json(
            self.s3_res, self.bucket_name, self.runs_key, f"step_{self.step_name}.json", self.run_entry
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
            self.s3_res, self.bucket_name, self.runs_key, f"step_{self.step_name}.json", self.run_entry
        )

    def complete_step_tracking(self):
        self.run_entry["captured_out"] = self.get_captured_out()
        self.run_entry["result"] = self.result
        save_json(
            self.s3_res, self.bucket_name, self.runs_key, "run.json", self.run_entry
        )
        self.run_entry["status"] = "COMPLETED"
        save_json(
            self.s3_res, self.bucket_name, self.runs_key, f"step_{self.step_name}.json", self.run_entry
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

        self.keys = (
            self.runs_key,
            self.metrics_key,
            self.artifacts_key,
            self.resource_key,
            self.source_key,
        )