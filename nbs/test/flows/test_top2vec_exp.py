#!/usr/bin/env python
# coding=utf-8

# SCIFLOW GENERATED FILE - DO NOT EDIT
from metaflow import FlowSpec, step, Parameter, current
from sciflow.test.test_top2vec import something, preprocess, fit, evaluate
from sciflow.test.test_top2vec import traffic_percent, speed, workers, dremio_access, model_level, min_date
from sacred import Experiment
from sacred.run import Run
from sciflow.lake_observer import AWSLakeObserver
from pathlib import Path
import os

ex = Experiment("captured_functions", interactive=True)
obs = AWSLakeObserver(
    bucket_name="pprsandboxpdlras3",
    experiment_dir="experiments/sciflow/sacred_sciflow",
    region="eu-west-1",
)
ex.observers.append(obs)

@ex.config
def config():
    run_id = None
    metrics = []
    artifacts = []

class TestTop2VecFlow(FlowSpec):
    traffic_percent = Parameter('traffic_percent', default=traffic_percent)  
    
    @step
    def start(self):
        self.artifacts = [os.path.join(Path(".").resolve(), "nbs", "test", "dataframe_artifact.csv")]
        self.next(self.train)
        
    @step
    def train(self):
        self.artifacts = self.artifacts + [os.path.join(Path(".").resolve(), 
                                                        "nbs", "test", "requirements-generated.txt")]
        self.metrics = [('mae', 100, 0), ('mae', 67, 1), ('mae', 23, 2), ('mae', 2.9, 3)]
        self.next(self.end)
        
    @step
    def end(self):
        flow_info = {
            "flow_name": current.flow_name,
            "run id": current.run_id,
            "origin run id": current.origin_run_id,
            "step name": current.step_name,
            "task ids": current.task_id,
            "pathspec": current.pathspec,
            "namespace": current.namespace,
            "username": current.username,
            "flow parameters": str(current.parameter_names)
        }
        
        run = ex.run(config_updates={'run_id': current.run_id,
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
    TestTop2VecFlow()
