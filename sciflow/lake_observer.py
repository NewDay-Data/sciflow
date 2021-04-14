# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/lake_observer.ipynb (unless otherwise specified).

__all__ = ['DEFAULT_S3_PRIORITY', 'AWSLakeObserver', 'lake_option']

# Cell
import json
import os
import os.path
import re

import boto3
import pandas as pd
from sacred.commandline_options import cli_option
from sacred.dependencies import get_digest
from sacred.observers.base import RunObserver
from sacred.serializer import flatten
from text_discovery.s3_utils import (delete_dir, is_valid_bucket,
                                     list_s3_subdirs, objects_exist_in_dir,
                                     s3_join)

# Cell
DEFAULT_S3_PRIORITY = 20

# Cell
class AWSLakeObserver(RunObserver):
    VERSION = "AWSLakeObserver-0.1.0"

    def __init__(
        self, bucket_name, experiment_dir, priority=DEFAULT_S3_PRIORITY, region=None,
    ):
        """Constructor for a AWSLakeObserver object.

        Run when the object is first created,
        before it's used within an experiment.

        Parameters
        ----------
        bucket_name
            The name of the bucket you want to store results in.
            Doesn't need to contain `s3://`, but needs to be a valid bucket name
        experiment_dir
            The relative path inside your bucket where you want this experiment to store results
        priority
            The priority to assign to this observer if
            multiple observers are present
        region
            The AWS region in which you want to create and access
            buckets. Needs to be either set here or configured in your AWS
        """
        if not is_valid_bucket(bucket_name):
            raise ValueError(
                "Your chosen bucket name doesn't follow AWS bucket naming rules"
            )
        self.experiment_dir = experiment_dir
        self.bucket_name = bucket_name
        self.priority = priority
        self.resource_dir = None
        self.source_dir = None
        self.runs_dir = None
        self.metrics_dir = None
        self.artifacts_dir = None
        self.run_entry = None
        self.config = None
        self.info = None
        self.experiment_id = None
        self.cout = ""
        self.cout_write_cursor = 0
        self.saved_metrics = {}
        if region is not None:
            self.region = region
            self.s3 = boto3.resource("s3", region_name=region)
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

    def put_data(self, key, binary_data):
        self.s3.Object(self.bucket_name, key).put(Body=binary_data)

    def save_json(self, table_dir, obj, filename):
        key = s3_join(table_dir, filename)
        self.put_data(key, json.dumps(flatten(obj), sort_keys=True, indent=2))

    def save_file(self, file_save_dir, filename, target_name=None):
        target_name = target_name or os.path.basename(filename)
        key = s3_join(file_save_dir, target_name)
        self.put_data(key, open(filename, "rb"))

    def save_sources(self, ex_info):
        base_dir = ex_info["base_dir"]
        source_info = []
        for s, m in ex_info["sources"]:
            abspath = os.path.join(base_dir, s)
            store_path, md5sum = self.find_or_save(abspath, self.source_dir)
            source_info.append([s, os.path.relpath(store_path, self.experiment_dir)])
        return source_info

    def find_or_save(self, filename, store_dir):
        source_name, ext = os.path.splitext(os.path.basename(filename))
        md5sum = get_digest(filename)
        store_name = source_name + "_" + md5sum + ext
        store_path = s3_join(store_dir, store_name)
        if len(list_s3_subdirs(self.s3, self.bucket_name, prefix=store_path)) == 0:
            self.save_file(self.source_dir, filename, store_path)
        return store_path, md5sum

    def _determine_run_dir(self, _id):
        if _id is None:
            path_subdirs = list_s3_subdirs(
                self.s3, self.bucket_name, s3_join(self.experiment_dir, "runs")
            )
            if not path_subdirs:
                max_run_id = 0
            else:
                integer_directories = [int(d) for d in path_subdirs if d.isdigit()]
                if not integer_directories:
                    max_run_id = 0
                else:
                    # If there are directories under experiment_dir that aren't
                    # numeric run directories, ignore those
                    max_run_id = max(integer_directories)

            _id = max_run_id + 1

        self.runs_dir = s3_join(self.experiment_dir, "runs", str(_id))
        self.metrics_dir = s3_join(self.experiment_dir, "metrics", str(_id))
        self.artifacts_dir = s3_join(self.experiment_dir, "artifacts", str(_id))
        self.resource_dir = s3_join(self.experiment_dir, "resources", str(_id))
        self.source_dir = s3_join(self.experiment_dir, "sources", str(_id))

        self.dirs = (
            self.runs_dir,
            self.metrics_dir,
            self.artifacts_dir,
            self.resource_dir,
            self.source_dir,
        )
        for dir_to_check in self.dirs:
            if objects_exist_in_dir(self.s3, self.bucket_name, dir_to_check):
                raise FileExistsError(
                    "S3 dir at {} already exists".format(self.runs_dir)
                )

        return _id

    def queued_event(
        self, ex_info, command, host_info, queue_time, config, meta_info, _id
    ):
        _id = self._determine_run_dir(_id)

        self.run_entry = {
            "experiment": dict(ex_info),
            "command": command,
            "host": dict(host_info),
            "config": flatten(config),
            "meta": meta_info,
            "status": "QUEUED",
        }
        self.config = config
        self.info = {}

        self.save_json(self.run_entry, "run.json")

        return _id

    def started_event(
        self, ex_info, command, host_info, start_time, config, meta_info, _id
    ):
        _id = self._determine_run_dir(_id)
        self.experiment_id = _id

        ex_info["sources"] = self.save_sources(ex_info)

        self.run_entry = {
            "experiment_id": self.experiment_id,
            "experiment": dict(ex_info),
            "format": self.VERSION,
            "command": command,
            "host": dict(host_info),
            "start_time": start_time.isoformat(),
            "config": flatten(config),
            "meta": meta_info,
            "status": "RUNNING",
            "resources": [],
            "artifacts": [],
            "captured_out": "",
            "info": {},
            "heartbeat": None,
        }
        self.config = config
        self.info = {}
        self.cout = ""
        self.cout_write_cursor = 0

        self.save_json(self.runs_dir, self.run_entry, "run.json")

        return _id

    def heartbeat_event(self, info, captured_out, beat_time, result):
        self.info = info
        self.run_entry["heartbeat"] = beat_time.isoformat()
        self.run_entry["captured_out"] = captured_out
        self.run_entry["result"] = result
        self.save_json(self.runs_dir, self.run_entry, "run.json")

    def completed_event(self, stop_time, result):
        self.run_entry["stop_time"] = stop_time.isoformat()
        self.run_entry["result"] = result
        self.run_entry["status"] = "COMPLETED"

        self.save_json(self.runs_dir, self.run_entry, "run.json")

    def interrupted_event(self, interrupt_time, status):
        self.run_entry["stop_time"] = interrupt_time.isoformat()
        self.run_entry["status"] = status
        self.save_json(self.runs_dir, self.run_entry, "run.json")

    def failed_event(self, fail_time, fail_trace):
        self.run_entry["stop_time"] = fail_time.isoformat()
        self.run_entry["status"] = "FAILED"
        self.run_entry["fail_trace"] = fail_trace
        self.save_json(self.runs_dir, self.run_entry, "run.json")

    def resource_event(self, filename):
        store_path, md5sum = self.find_or_save(filename, self.resource_dir)
        self.run_entry["resources"].append([filename, store_path])
        self.save_json(self.runs_dir, self.run_entry, "run.json")

    def artifact_event(self, name, filename, metadata=None, content_type=None):
        self.save_file(self.artifacts_dir, filename, name)
        self.run_entry["artifacts"].append(name)
        self.save_json(self.runs_dir, self.run_entry, "run.json")

    def log_metrics(self, metrics_by_name, info):
        """Store new measurements into metrics.csv"""
        print(metrics_by_name)
        if len(metrics_by_name.values()) > 0:
            metric_frames = [pd.DataFrame(v) for v in metrics_by_name.values()]
            metrics = pd.concat(metric_frames).reset_index(drop=True)
            metrics["experiment_id"] = self.experiment_id
            metrics_path = f"s3://{self.bucket_name}/{self.metrics_dir}/metrics.csv"
            metrics.to_csv(metrics_path, index=False)

    def __eq__(self, other):
        if isinstance(other, AWSLakeObserver):
            return (
                self.bucket == other.bucket
                and self.experiment_dir == other.experiment_dir
            )
        else:
            return False

# Cell
@cli_option("-L", "--lake")
def lake_option(args, run):
    """Add a Data Lake observer to the experiment.

    The argument value should be `s3://<bucket>/path/to/exp`.
    """
    match_obj = re.match(r"s3:\/\/([^\/]*)\/(.*)", args)
    if match_obj is None or len(match_obj.groups()) != 2:
        raise ValueError(
            "Valid bucket specification not found. "
            "Enter bucket and directory path like: "
            "s3://<bucket>/path/to/exp"
        )
    bucket_name, experiment_dir = match_obj.groups()
    run.observers.append(
        AWSLakeObserver(bucket_name=bucket_name, experiment_dir=experiment_dir)
    )