# SCIFLOW GENERATED FILE - DO NOT EDIT
from metaflow import FlowSpec, step, Parameter
from sciflow.test.test_top2vec import something, preprocess, fit, evaluate
from sciflow.test.test_top2vec import traffic_percent, speed, workers, dremio_access, model_level, min_date


class TestTop2VecFlow(FlowSpec):
    traffic_percent = Parameter('traffic_percent', default=traffic_percent)
    speed = Parameter('speed', default=speed)
    workers = Parameter('workers', default=workers)
    model_level = Parameter('model_level', default=model_level)
    min_date = Parameter('min_date', default=min_date)

    @step
    def start(self):
        something()
        self.next(self.preprocess)

    @step
    def preprocess(self):
        self.documents = preprocess(dremio_access, self.model_level, self.min_date, self.traffic_percent)
        self.next(self.fit)

    @step
    def fit(self):
        self.model = fit(self.documents, self.workers, self.speed)
        self.next(self.end)

    @step
    def end(self):
        self.results = evaluate(self.model)

if __name__ == "__main__":
    TestTop2VecFlow()