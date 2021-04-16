#!/usr/bin/env python# coding=utf-8# SCIFLOW GENERATED FILE - EDIT COMPANION NOTEBOOK
import json
from metaflow import FlowSpec, step, current, Parameter, JSONType
from sciflow.test.test_data_handling import scalar, py_advanced, pandas
from sciflow.test.test_data_handling import int_param, float_param, str_param, input_path, model_path, dict_param, list_param, ones, text, series_param, df_param
from sacred import Experiment
from sciflow.lake_observer import AWSLakeObserver
import time

ex = Experiment("test_data_handling")
# TODO inject observers
obs = AWSLakeObserver(
    bucket_name="pprsandboxpdlras3",
    experiment_dir="experiments/sciflow/test_data_handling",
    region="eu-west-1",
)
ex.observers.append(obs)

@ex.config
def config():
    flow_run_id = None
    metrics = []
    artifacts = []
    

class TestDataHandlingFlow(FlowSpec):
    int_param = Parameter('int_param', default=int_param)
    float_param = Parameter('float_param', default=float_param)
    str_param = Parameter('str_param', default=str_param)
    input_path = Parameter('input_path', default=str(input_path))
    model_path = Parameter('model_path', default=str(model_path))
    dict_param = Parameter('dict_param', default=json.dumps(dict_param), type=JSONType)
    list_param = Parameter('list_param', default=json.dumps(list_param), type=JSONType)
    artifacts = []
    metrics = []

    @step
    def start(self):
        self.results = scalar(self.int_param, self.float_param, self.str_param)

        if self.results:
            if "artifacts" in results:
                self.artifacts = self.artifacts + results['artifacts']
            if "metrics" in results:
                self.metrics = self.metrics + results['metrics']

        self.start_time = time.time()
        self.next(self.py_advanced)

    @step
    def py_advanced(self):
        py_advanced(self.input_path, self.list_param, self.dict_param)
        self.next(self.pandas)

    @step
    def pandas(self):
        pandas(series_param, df_param)
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
    TestDataHandlingFlow()