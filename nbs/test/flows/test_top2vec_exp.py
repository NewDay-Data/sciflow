# SCIFLOW GENERATED FILE - DO NOT EDIT
from metaflow import FlowSpec, step, Parameter
from sciflow.test.test_top2vec import something, preprocess, fit, evaluate
from sciflow.test.test_top2vec import traffic_percent, speed, workers, dremio_access, model_level, min_date
from sacred import Experiment
from sacred.run import Run


ex = Experiment('TestTop2VecFlow')

@ex.config
def training_config():
    traffic_percent = traffic_percent

    
class TestTop2VecFlow(FlowSpec):   
    traffic_percent = Parameter('traffic_percent', default=traffic_percent)

    @ex.capture
    @step
    def start(self):
        print('Start')
        self.next(self.middle)

    @ex.capture
    @step
    def middle(self, _run):
        _run.log_scalar("end", 2)
        self.next(self.end)
        
    @ex.capture
    @step
    def end(self):
        print('Done')
        
@ex.main
def run_flow():
    TestTop2VecFlow()
    
if __name__ == "__main__":
    run_flow()
