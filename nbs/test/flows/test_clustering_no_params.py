#!/usr/bin/env python
# coding=utf-8
# SCIFLOW GENERATED FILE - EDIT COMPANION NOTEBOOK
from metaflow import FlowSpec, step, current
from sciflow.test.test_clustering import something, preprocess, fit, evaluate
from sacred import Experiment
from sciflow.lake_observer import AWSLakeObserver
import time

ex = Experiment("test_clustering")
# TODO inject observers
obs = AWSLakeObserver(
    bucket_name="pprsandboxpdlras3",
    experiment_dir="experiments/sciflow/test_clustering",
    region="eu-west-1",
)
ex.observers.append(obs)

@ex.config
def config():
    flow_run_id = None
    artifacts = []
    metrics = []
    

class TestClusteringFlow(FlowSpec):
    artifacts = []
    metrics = []

    @step
    def start(self):
        something()
        self.start_time = time.time()
        self.next(self.preprocess)

    @step
    def preprocess(self):
        results = preprocess(dremio_access, model_level, min_date, traffic_percent)

        for key in results.keys():
            if key in self.__dict__:
                self.__dict__[key] = self.__dict__[key] + results[key]
            else:
                self.__dict__[key] = results[key]

        self.next(self.fit)

    @step
    def fit(self):
