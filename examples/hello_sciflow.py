#!/usr/bin/env python
# coding=utf-8
# SCIFLOW GENERATED FILE - EDIT COMPANION NOTEBOOK
from metaflow import FlowSpec, step, current, Parameter
from sciflow_examples.hello_sciflow import first, second
from sciflow_examples.hello_sciflow import traffic_percent
from sacred import Experiment
from sciflow.experiment.lake_observer import AWSLakeObserver
import time

ex = Experiment("hello_sciflow")
# TODO inject observers
obs = AWSLakeObserver(project="sciflow_examples", experiment_name="hello_sciflow")
ex.observers.append(obs)

@ex.config
def config():
    flow_run_id = None
    artifacts = []
    metrics = []
    

class HelloSciflowFlow(FlowSpec):
    traffic_percent = Parameter('traffic_percent', default=traffic_percent)
    artifacts = []
    metrics = []

    @step
    def start(self):
        first()
        self.start_time = time.time()
        self.next(self.second)

    @step
    def second(self):
        results = second(self.traffic_percent)

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
    HelloSciflowFlow()