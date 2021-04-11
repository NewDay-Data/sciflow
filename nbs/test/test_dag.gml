graph [
  node [
    id 0
    label "0"
    name "first"
    docstring "This the entrypoint.&#10;&#10;:param some_params: this is a first param&#10;:returns: this is a description of what is returned"
    args "some_params"
    has_return 0
    return_stmt ""
    code "&#10;&#10;def first(some_params: int):&#10;    &#34;&#34;&#34;&#10;    This the entrypoint.&#10;&#10;    :param some_params: this is a first param&#10;    :returns: this is a description of what is returned&#10;    &#34;&#34;&#34;&#10;    print(some_params)&#10;&#10;"
  ]
  node [
    id 1
    label "1"
    name "preprocess"
    docstring "Pre-process the input data"
    args "input_path"
    has_return 0
    return_stmt ""
    code "def preprocess(input_path: str):&#10;    &#34;&#34;&#34;Pre-process the input data&#34;&#34;&#34;&#10;    import time&#10;&#10;    print(f&#34;Preprocessing input data from {input_path}...&#34;)&#10;    time.sleep(1)&#10;&#10;"
  ]
  node [
    id 2
    label "2"
    name "train"
    docstring "Train the model"
    args "input_path,model_path"
    has_return 0
    return_stmt ""
    code "def train(input_path: str, model_path: str):&#10;    &#34;&#34;&#34;Train the model&#34;&#34;&#34;&#10;    import time&#10;&#10;    print(f&#34;Training {model_path} on {input_path}...&#34;)&#10;    time.sleep(1)&#10;&#10;"
  ]
  node [
    id 3
    label "3"
    name "last"
    docstring "Clean up and close connections"
    args "some_param"
    has_return 1
    return_stmt "one"
    code "def last(some_param: None):&#10;    &#34;&#34;&#34;&#10;    Clean up and close connections&#34;&#34;&#34;&#10;    one = 1&#10;    return one"
  ]
  edge [
    source 0
    target 1
  ]
  edge [
    source 1
    target 2
  ]
  edge [
    source 2
    target 3
  ]
]
