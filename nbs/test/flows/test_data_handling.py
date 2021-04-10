# SCIFLOW GENERATED FILE - DO NOT EDIT
import json
from metaflow import FlowSpec, step, Parameter, JSONType
from sciflow.test.test_data_handling import scalar, py_advanced, pandas
from sciflow.test.test_data_handling import int_param, float_param, str_param, input_path, model_path, dict_param, list_param, ones, text, series_param, df_param


class TestDataHandlingFlow(FlowSpec):
    int_param = Parameter('int_param', default=int_param)
    float_param = Parameter('float_param', default=float_param)
    str_param = Parameter('str_param', default=str_param)
    input_path = Parameter('input_path', default=str(input_path))
    model_path = Parameter('model_path', default=str(model_path))
    dict_param = Parameter('dict_param', default=json.dumps(dict_param), type=JSONType)
    list_param = Parameter('list_param', default=json.dumps(list_param), type=JSONType)

    @step
    def start(self):
        scalar(self.int_param, self.float_param, self.str_param)
        self.next(self.py_advanced)

    @step
    def py_advanced(self):
        py_advanced(self.input_path, self.list_param, self.dict_param)
        self.next(self.end)

    @step
    def end(self):
        pandas(series_param, df_param)

if __name__ == "__main__":
    TestDataHandlingFlow()