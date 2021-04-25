#!/usr/bin/env python
# coding=utf-8
# SCIFLOW GENERATED FILE - EDIT COMPANION NOTEBOOK
from metaflow import FlowSpec, step, current, Parameter
from sciflow.test.test_clustering import something, preprocess, fit, evaluate
from sciflow.test.test_clustering import traffic_percent, speed, workers, dremio_access, model_level, min_date
from sacred import Experiment
from sciflow.experiment.lake_observer import AWSLakeObserver
import time

ex = Experiment("test_clustering")
# TODO inject observers
obs = AWSLakeObserver(project="sciflow", experiment_name="test_clustering")
ex.observers.append(obs)

@ex.config
def config():
    flow_run_id = None
    artifacts = []
    metrics = []
    

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
        results = preprocess(dremio_access, self.model_level, self.min_date, self.traffic_percent)

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
            "run_id": current.run_id,
            "pathspec": current.pathspec,
            "namespace": current.namespace,
            "username": current.username,
            "flow_parameters": str(current.parameter_names),
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
    TestClusteringFlow()