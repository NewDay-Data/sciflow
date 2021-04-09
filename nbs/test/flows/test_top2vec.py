# SCIFLOW GENERATED FILE - DO NOT EDIT
from metaflow import FlowSpec, step, Parameter
from sciflow.test.test_top2vec import something, preprocess, fit, evaluate
from sciflow.test.test_top2vec import traffic_percent, speed, workers, dremio_access


class TestTop2VecFlow(FlowSpec):
    traffic_percent = Parameter('traffic_percent', default=traffic_percent)
    speed = Parameter('speed', default=speed)
    workers = Parameter('workers', default=workers)

    @step
    def start(self):
        something()
        self.next(self.preprocess)

    @step
    def preprocess(self):
        preprocess(self.dremio_access, model_level, min_date, self.traffic_percent)
        self.next(self.fit)

    @step
    def fit(self):
        fit(documents, self.workers, self.speed)
        self.next(self.end)

    @step
    def end(self):
        evaluate(model)

if __name__ == "__main__":
    TestTop2VecFlow()