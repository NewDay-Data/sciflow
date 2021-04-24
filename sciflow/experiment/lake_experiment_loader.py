# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/experiment/lake_experiment_loader.ipynb (unless otherwise specified).

__all__ = ['MAX_CACHE_SIZE', 'LakeExpLoader']

# Cell

import json
from functools import lru_cache
from typing import Tuple

import numpy as np
import pandas as pd
from incense.artifact import CSVArtifact
from incense.experiment import Experiment
from nbdev import Config
from ..utils import load_dremio_access
from text_discovery.lake_experiment import LakeExperiment
from tinydb import Query, TinyDB
from tinydb.storages import MemoryStorage
from turbodbc.exceptions import DatabaseError

MAX_CACHE_SIZE = 32

# Cell
class LakeExpLoader:
    def __init__(
        self,
        experiment_name,
        experiments_key_prefix=None,
        dremio_access=None,
        bucket_name=None,
        bucket_table_alias=None,
    ):
        config = Config()
        lib_name = config.lib_name
        self.experiment_name = experiment_name
        self.dremio_access = (
            load_dremio_access() if dremio_access is None else dremio_access
        )
        self.bucket_name = config.bucket if bucket_name is None else bucket_name
        self.bucket_table_alias = (
            config.bucket_table_alias
            if bucket_table_alias is None
            else bucket_table_alias
        )
        self.experiments_key_prefix = (
            f"{lib_name}/experiments"
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
        experiment_id: int = None,
        order_by: str = None,
        limit: int = None,
    ) -> Experiment:
        if experiment_name is None:
            experiment_name = self.experiment_name
        query = f"select * from {self.table_context}.{experiment_name}.runs"
        if experiment_ids:
            ids = ", ".join([str(i) for i in experiment_ids])
            query += f" where dir0 IN ({ids})"
        if experiment_id:
            query += f" where dir0 = {experiment_id}"
        if order_by:
            query += f" order by {order_by} desc"
        if limit:
            query += f" limit {limit}"
        data = self.dremio_access.read_sql_to_dataframe(query)
        experiments = [
            LakeExperiment(
                self.bucket_name,
                self.experiments_key_prefix,
                experiment_name,
                ex_id,
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
    def find_by_ids(self, experiment_ids: Tuple[int]):
        if len(experiment_ids) == 1:
            raise ValueError("Use find_by_id for a single experiment")
        return self._find(experiment_ids=experiment_ids)

    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def find_latest(self, n=5):
        return self._find(order_by="dir0", limit=n)

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
            f"Experiment: {self.experiment_name}\n"
            f"Remote Path: {self.remote_path}\n"
            f"Lake Table: {self.lake_table}"
        )