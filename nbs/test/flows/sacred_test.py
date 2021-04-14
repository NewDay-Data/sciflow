#!/usr/bin/env python
# coding=utf-8

# SCIFLOW GENERATED FILE - DO NOT EDIT
from metaflow import FlowSpec, step, Parameter, current
from sciflow.test.test_top2vec import something, preprocess, fit, evaluate
from sciflow.test.test_top2vec import traffic_percent, speed, workers, dremio_access, model_level, min_date
from sacred import Experiment
from sacred.run import Run
from sciflow.lake_observer import AWSLakeObserver
 
ex = Experiment("captured_functions", interactive=True)

bucket = "pprsandboxpdlras3"
region = "eu-west-1"
exp_name = "sacred_sciflow"
lib_name = "sciflow"
obs = AWSLakeObserver(
    bucket_name=bucket,
    experiment_dir=f"experiments/{lib_name}/{exp_name}",
    region=region,
)
ex.observers.append(obs)

@ex.config
def cfg():
    message = "This is printed by func {}."

@ex.main
def main():
    TestTop2VecFlow()

class TestTop2VecFlow(FlowSpec):
    #traffic_percent = Parameter('traffic_percent', default=traffic_percent)
        
    @ex.capture
    def some_function(self, message):
        print(message.format("foo"))
        
    @step
    def start(self):
        self.some_function()
        self.next(self.end)
        
    @step
    def end(self):
        print("done")
        

    
if __name__ == "__main__":
    run = ex.run()
