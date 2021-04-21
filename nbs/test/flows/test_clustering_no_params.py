#!/usr/bin/env python
# coding=utf-8
# SCIFLOW GENERATED FILE - EDIT COMPANION NOTEBOOK
from metaflow import FlowSpec, step, current
from sciflow.test.test_clustering_no_params import something, preprocess, fit, evaluate
from sacred import Experiment
from sciflow.lake_observer import AWSLakeObserver
import time

ex = Experiment("test_clustering_no_params")
# TODO inject observers
obs = AWSLakeObserver(
    bucket_name="pprsandboxpdlras3",
    experiment_dir="experiments/sciflow/test_clustering_no_params",
    region="eu-west-1",
)
ex.observers.append(obs)

@ex.config
def config():
    flow_run_id = None
    artifacts = []
    metrics = []
    

class TestClusteringNoParamsFlow(FlowSpec):
    artifacts = []
    metrics = []

    @step
    def start(self):
        something()
        self.start_time = time.time()
        self.next(self.preprocess)

    @step
    def preprocess(self):
        results = preprocess(self.dremio_access, self.model_level, self.min_date, self.traffic_percent)

        for key in results.keys():
            if key in self.__dict__:
                self.__dict__[key] = self.__dict__[key] + results[key]
            else:
                self.__dict__[key] = results[key]

        self.next(self.fit)

    @step
    def fit(self):
        results = fit(self.documents, self.workers, self.speed)

        for key in results.keys():
            if key in self.__dict__:
                self.__dict__[key] = self.__dict__[key] + results[key]
            else:
                self.__dict__[key] = results[key]

        self.next(self.evaluate)

    @step
    def evaluate(self):
        results = evaluate(self.model)

        for key in results.keys():
            if key in self.__dict__:
                self.__dict__[key] = self.__dict__[key] + results[key]
            else:
                self.__dict__[key] = results[key]

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
            "run_time_mins": round((time.time() - self.__getattr__('start_time')) / 60.0, 1)
        }

        run = ex.run(config_updates={'artifacts': self.__getattr__('artifacts'),
                                    'metrics': self.__getattr__('metrics')},
                     meta_info = flow_info)

    @ex.main
    def track_flow(artifacts, metrics, _run):
        for artifact in artifacts:
            _run.add_artifact(artifact)
        for metric_name, metric_value, step in metrics:
            _run.log_scalar(metric_name, metric_value, step)
    
if __name__ == "__main__":
    TestClusteringNoParamsFlow()