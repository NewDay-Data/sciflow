# SCIFLOW GENERATED FILE - DO NOT EDIT
from metaflow import FlowSpec, step, Parameter
from sciflow.test_module import first
from sciflow.test_module import some_param


class TestModuleFlow(FlowSpec):
    some_param = Parameter('some_param', default=some_param)

    @step
    def start(self):
        first(self.some_param)
        self.next(self.end)

    @step
    def end(self):
        pass

if __name__ == "__main__":
    TestModuleFlow()