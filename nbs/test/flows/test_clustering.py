#!/usr/bin/env python# coding=utf-8# SCIFLOW GENERATED FILE - EDIT COMPANION NOTEBOOK
from metaflow import FlowSpec, step, current, Parameter
from sciflow.test.test_clustering import something, preprocess, fit, evaluate
from sciflow.test.test_clustering import traffic_percent, speed, workers, dremio_access, model_level, min_date
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
    metrics = []
    artifacts = []
    

class TestClusteringFlow(FlowSpec):
    traffic_percent = Parameter('traffic_percent', default=traffic_percent)
    speed = Parameter('speed', default=speed)
    workers = Parameter('workers', default=workers)
    model_level = Parameter('model_level', default=model_level)
    min_date = Parameter('min_date', default=min_date)
    artifacts = []
    metrics = []

    @step
    def start(self):
        something()
        self.start_time = time.time()
        self.next(self.preprocess)

    @step
    def preprocess(self):
        self.documents = preprocess(dremio_access, self.model_level, self.min_date, self.traffic_percent)
        self.next(self.fit)

    @step
    def fit(self):
        self.model = fit(self.documents, self.workers, self.speed)
        self.next(self.evaluate)

    @step
    def evaluate(self):
        self.results = evaluate(self.model)
        self.next(self.end)


    @step
    def end(self):
        flow_info = {
            "flow_name": current.flow_name,
            "run id": current.run_id,
            "origin run id": current.origin_run_id,
            "pathspec": current.pathspec,
            "namespace": current.namespace,
            "username": current.username,
            "flow parameters": str(current.parameter_names),
            "run_time_mins": (time.time() - self.start_time) / 60.0
        }

        run = ex.run(config_updates={'flow_run_id': current.run_id,
                                    'artifacts': self.artifacts,
                                    'metrics': self.metrics},
                     meta_info = flow_info)

    @ex.main
    def track_flow(artifacts, metrics, _run):
        for artifact in artifacts:
            _run.add_artifact(artifact)
        for metric_name, metric_value, step in metrics:
            _run.log_scalar(metric_name, metric_value, step)
    
if __name__ == "__main__":
    TestClusteringFlow()