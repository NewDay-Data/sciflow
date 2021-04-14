# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/lake_experiment.ipynb (unless otherwise specified).

__all__ = ['file_to_mime_type_map', 'LakeExperiment']

# Cell
import os
from typing import Dict

import boto3
import pandas as pd
from incense.artifact import Artifact, content_type_to_artifact_cls
from pyrsistent import freeze, thaw
from text_discovery.s3_utils import S3File, s3_join

# Cell
file_to_mime_type_map = {
    ".txt": "text/csv",
    ".csv": "text/csv",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".mp4": "video/mp4",
    ".pickle": "application/octet-stream",
}

# Cell
class LakeExperiment:
    def __init__(self, bucket_name, experiments_dir, name, experiment_id, data):
        self.bucket_name = bucket_name
        self.experiments_dir = experiments_dir
        self.name = name
        self.experiment_id = experiment_id
        self.project_name = s3_join(experiments_dir, name)
        self.project_dir = s3_join(self.bucket_name, self.project_name)
        self.metrics_dir = s3_join(self.project_dir, "metrics", str(experiment_id))
        self.artifacts_dir = s3_join(self.project_dir, "artifacts", str(experiment_id))
        self._data = freeze(data)
        self.s3 = boto3.client("s3")
        self.artifacts = self._load_artifacts()
        self.metrics = self._load_metrics()

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.experiment_id}, name={self.name})"

    def __getattr__(self, item):
        """Try to relay attribute access to easy dict, to allow dotted access."""
        return getattr(self._data, item)

    def to_dict(self) -> dict:
        return thaw(self._data)

    def _load_artifacts(self) -> Dict[str, Artifact]:
        artifacts = {}
        s3 = boto3.resource("s3")
        bucket = s3.Bucket(self.bucket_name)

        artifacts_key_prefix = s3_join(
            self.project_name, "artifacts", str(self.experiment_id)
        )
        artifact_keys = [
            obj.key for obj in bucket.objects.filter(Prefix=artifacts_key_prefix)
        ]

        for artifact_key in artifact_keys:
            s3_object = s3.Object(bucket_name=self.bucket_name, key=artifact_key)
            artifact_file = S3File(s3_object)
            name = os.path.basename(artifact_key)

            try:
                content_type = file_to_mime_type_map[os.path.splitext(name)[-1]]
                artifact_type = content_type_to_artifact_cls[content_type]
                artifacts[name] = artifact_type(
                    name, artifact_file, content_type=content_type
                )
            except KeyError:
                artifact_type = Artifact
                artifacts[name] = artifact_type(name, artifact_file)

        return artifacts

    def _load_metrics(self) -> Dict[str, pd.Series]:
        metrics_path = f"s3://{self.metrics_dir}/metrics.csv"
        return pd.read_csv(metrics_path)

    def delete(self, confirmed: bool = False):
        raise NotImplementedError

    def _delete(self):
        raise NotImplementedError

    def _delete_metrics(self):
        raise NotImplementedError

    def _delete_artifacts(self):
        raise NotImplementedError