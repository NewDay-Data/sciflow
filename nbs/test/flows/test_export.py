#!/usr/bin/env python# coding=utf-8# SCIFLOW GENERATED FILE - EDIT COMPANION NOTEBOOK
from metaflow import FlowSpec, step, current, Parameter
from sciflow.test.test_export import first, preprocess, train, last
from sciflow.test.test_export import some_params, some_param, input_path, model_path
from sacred import Experiment
from sciflow.lake_observer import AWSLakeObserver
import time

ex = Experiment("test_export")
# TODO inject observers
obs = AWSLakeObserver(
    bucket_name="pprsandboxpdlras3",
    experiment_dir="experiments/sciflow/test_export",
    region="eu-west-1",
)
ex.observers.append(obs)

@ex.config
def config():
    flow_run_id = None
    metrics = []
    artifacts = []
    

class TestExportFlow(FlowSpec):
    some_params = Parameter('some_params', default=some_params)
    some_param = Parameter('some_param', default=some_param)
    input_path = Parameter('input_path', default=input_path)
    model_path = Parameter('model_path', default=model_path)
    artifacts = []
    metrics = []

    @step
    def start(self):
        """This the entrypoint.
        
        :param some_params: this is a first param
        :returns: this is a description of what is returned"""
        first(self.some_params)
        self.start_time = time.time()
        self.next(self.preprocess)

    @step
    def preprocess(self):
        """Pre-process the input data"""
        preprocess(self.input_path)
        self.next(self.train)

    @step
    def train(self):
        """Train the model"""
        train(self.input_path, self.model_path)
        self.next(self.last)

    @step
    def last(self):
        """Clean up and close connections"""
        self.one = last(self.some_param)
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
    TestExportFlow()