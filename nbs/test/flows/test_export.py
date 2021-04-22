#!/usr/bin/env python
# coding=utf-8
# SCIFLOW GENERATED FILE - EDIT COMPANION NOTEBOOK
from metaflow import FlowSpec, step, current, Parameter
from sciflow.test.test_export import first, preprocess, train, last
from sciflow.test.test_export import some_params, some_param, input_path, model_path
from sacred import Experiment
from sciflow.lake_observer import AWSLakeObserver
import time

ex = Experiment("test_export")
# TODO inject observers
obs = AWSLakeObserver(experiment_name="test_export")
ex.observers.append(obs)

@ex.config
def config():
    flow_run_id = None
    artifacts = []
    metrics = []
    

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
        results = last(self.some_param)

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
    TestExportFlow()