#!/usr/bin/env python
# coding=utf-8
# SCIFLOW GENERATED FILE - EDIT COMPANION NOTEBOOK
from metaflow import FlowSpec, step, current, Parameter
from sciflow.test.test_module import first
from sciflow.test.test_module import some_param
from sacred import Experiment
from sciflow.lake_observer import AWSLakeObserver
import time

ex = Experiment("test_module")
# TODO inject observers
obs = AWSLakeObserver(
    bucket_name="pprsandboxpdlras3",
    experiment_dir="experiments/sciflow/test_module",
    region="eu-west-1",
)
ex.observers.append(obs)

@ex.config
def config():
    flow_run_id = None
    artifacts = []
    metrics = []
    

class TestModuleFlow(FlowSpec):
    some_param = Parameter('some_param', default=some_param)
    artifacts = []
    metrics = []

    @step
    def start(self):
        results = first(self.some_param)

        for key in results.keys():
            if key in self.__dict__:
                self.__dict__[key] = self.__dict__[key] + results[key]
            else:
                self.__dict__[key] = results[key]

        self.start_time = time.time()
        self.next(self.end)

    @step
    def end(self):
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
    TestModuleFlow()