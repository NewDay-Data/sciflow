# SCIFLOW GENERATED FILE - DO NOT EDIT
from metaflow import FlowSpec, step, Parameter
from sciflow.test.test_export import first, preprocess, train, last
from sciflow.test.test_export import some_params, some_param, input_path, model_path


class TestExportFlow(FlowSpec):
    some_params = Parameter('some_params', default=some_params)
    some_param = Parameter('some_param', default=some_param)
    input_path = Parameter('input_path', default=input_path)
    model_path = Parameter('model_path', default=model_path)

    @step
    def start(self):
        """This the entrypoint.
        
        :param some_params: this is a first param
        :returns: this is a description of what is returned"""
        first(self.some_params)
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
        self.next(self.end)

    @step
    def end(self):
        """Clean up and close connections"""
        last(self.some_param)

if __name__ == "__main__":
    TestExportFlow()