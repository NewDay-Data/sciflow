# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/lake_experiment_loader.ipynb (unless otherwise specified).

__all__ = ['MAX_CACHE_SIZE', 'LakeExpLoader']

# Cell

import json
import os
import uuid
from functools import lru_cache
from typing import Tuple

import boto3
import numpy as np
import pandas as pd
from incense.artifact import CSVArtifact
from incense.experiment import Experiment
from pandas.io.sql import DatabaseError
from .lake_experiment import LakeExperiment
from ..s3_utils import delete_dir
from ..utils import odbc_connect, prepare_env, query
from tinydb import Query, TinyDB
from tinydb.storages import MemoryStorage

MAX_CACHE_SIZE = 32

# Cell
class LakeExpLoader:
    def __init__(
        self,
        project,
        experiment_name,
        experiments_key_prefix=None,
        connection=None,
        bucket_name=None,
        bucket_table_alias=None,
    ):
        self.project = project
        self.experiment_name = experiment_name
        self.connection = odbc_connect() if connection is None else connection
        self.bucket_name = (
            os.environ["SCIFLOW_BUCKET"] if bucket_name is None else bucket_name
        )
        self.bucket_table_alias = (
            os.environ["SCIFLOW_BUCKET_TABLE_ALIAS"]
            if bucket_table_alias is None
            else bucket_table_alias
        )
        self.experiments_key_prefix = (
            f"{project}/experiments"
            if experiments_key_prefix is None
            else experiments_key_prefix
        )
        table_path = self.experiments_key_prefix.replace("/", ".")
        self.table_context = f"{self.bucket_table_alias}.{table_path}"
        self.remote_path = (
            f"{self.bucket_name}/{self.experiments_key_prefix}/{self.experiment_name}"
        )
        self.lake_table = f"{self.table_context}.{self.experiment_name}"

    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def _find(
        self,
        experiment_name=None,
        experiment_ids=None,
        experiment_id: str = None,
        order_by: str = None,
        limit: int = None,
    ) -> Experiment:
        if experiment_name is None:
            experiment_name = self.experiment_name
        table_name = f"{self.table_context}.{experiment_name}.runs"
        # TODO Dremio Specific code in utils.py
        data = query(self.connection, f"ALTER TABLE {table_name} REFRESH METADATA")

        query_stmt = f"select * from {table_name}"
        if experiment_ids:
            ", ".join([str(i) for i in experiment_ids])
            query_stmt += (
                f" where dir0 IN {tuple('{}'.format(x) for x in experiment_ids)}"
            )
        if experiment_id:
            query_stmt += f" where dir0 = '{experiment_id}'"
        if order_by:
            query_stmt += f" order by {order_by} desc"
        if limit:
            query_stmt += f" limit {limit}"
        data = query(self.connection, query_stmt)
        experiments = [
            LakeExperiment(
                self.bucket_name,
                self.experiments_key_prefix,
                experiment_name,
                ex_id,
                data.iloc[i, :].to_dict()["start_time"],
                data.iloc[i, :].to_dict(),
            )
            for i, ex_id in enumerate(data.dir0.tolist())
        ]
        return experiments

    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def find_by_id(self, experiment_id):
        experiments = self._find(experiment_id=experiment_id)
        return None if len(experiments) == 0 else experiments[0]

    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def find_by_ids(self, experiment_ids: Tuple[str]):
        if len(experiment_ids) == 1:
            raise ValueError("Use find_by_id for a single experiment")
        return self._find(experiment_ids=experiment_ids)

    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def find_latest(self, n=5):
        return self._find(order_by="start_time", limit=n)

    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def find_all(self):
        return self._find()

    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def find_by_name(self, experiment_name):
        result = None
        try:
            result = self._find(experiment_name=experiment_name)
        except PermissionError:
            print(f"File not found or access not granted; check path information")
        return result

    def insert_docs(self, db, prop_name):
        experiments = self.find_all()
        for ex in experiments:
            document = json.loads(ex._data[prop_name])
            document["experiment_id"] = ex.experiment_id
            db.insert(document)

    def find_by_key(self, prop_name, key, value):
        db = TinyDB(storage=MemoryStorage)
        self.insert_docs(db, prop_name)
        Experiment = Query()
        docs = list(db.search(Experiment[key] == value))
        if len(docs) == 0:
            return None
        if len(docs) == 1:
            return self.find_by_id(docs[0]["experiment_id"])
        return self.find_by_ids(tuple(d["experiment_id"] for d in docs))

    def find_by_config_key(self, key, value):
        return self.find_by_key("config", key, value)

    def cache_clear(self):
        """Clear all caches of all find functions.
        Useful when you want to see the updates to your database."""
        self._find.cache_clear()
        self.find_all.cache_clear()
        self.find_by_id.cache_clear()
        self.find_by_ids.cache_clear()
        self.find_by_name.cache_clear()
        self.find_latest.cache_clear()

    def __repr__(self):
        return (
            f"Project: {self.project}\n"
            f"Experiment: {self.experiment_name}\n"
            f"Remote Path: {self.remote_path}\n"
            f"Lake Table: {self.lake_table}"
        )