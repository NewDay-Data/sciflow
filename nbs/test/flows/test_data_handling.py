#!/usr/bin/env python
# coding=utf-8
# SCIFLOW GENERATED FILE - EDIT COMPANION NOTEBOOK
import json
from metaflow import FlowSpec, step, current, Parameter, JSONType
from sciflow.test.test_data_handling import scalar, py_advanced, pandas
from sciflow.test.test_data_handling import int_param, float_param, str_param, input_path, model_path, dict_param, list_param, ones, text, series_param, df_param
from sacred import Experiment
from sciflow.experiment.lake_observer import AWSLakeObserver
import time

ex = Experiment("test_data_handling")
# TODO inject observers
obs = AWSLakeObserver(project="sciflow", experiment_name="test_data_handling")
ex.observers.append(obs)

@ex.config
def config():
    flow_run_id = None
    artifacts = []
    metrics = []
    

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
        results = scalar(self.int_param, self.float_param, self.str_param)

        for key in results.keys():
            if key in self.__dict__:
                self.__dict__[key] = self.__dict__[key] + results[key]
            else:
                self.__dict__[key] = results[key]

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
    TestDataHandlingFlow()