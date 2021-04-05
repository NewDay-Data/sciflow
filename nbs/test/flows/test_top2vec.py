# SCIFLOW GENERATED FILE - DO NOT EDIT
from metaflow import FlowSpec, step, Parameter
from sciflow.test/test_top2vec import something, preprocess, fit, evaluate
from sciflow.test/test_top2vec import traffic_percent, speed, workers


class Test/TestTop2VecFlow(FlowSpec):
    traffic_percent = Parameter('traffic_percent', default=traffic_percent)
    speed = Parameter('speed', default=speed)
    workers = Parameter('workers', default=workers)

    @step
    def start(self):
        something(self.)
        self.next(self.preprocess)

    @step
    def preprocess(self):
        preprocess(self.dremio_access,self.model_level,self.min_date,self.traffic_percent)
        self.next(self.fit)

    @step
    def fit(self):
        fit(self.documents,self.workers,self.speed)
        self.next(self.end)

    @step
    def end(self):
        evaluate(self.model)

if __name__ == "__main__":
    Test/TestTop2VecFlow()