graph [
  node [
    id 0
    label "0"
    name "first"
    args "some_params"
    has_return 0
    code "from typing import List&#10;&#10;&#10;def first(some_params: List[str]):&#10;    print(&#34;&#34;.join(some_params))&#10;    return len(some_params)&#10;&#10;"
  ]
  node [
    id 1
    label "1"
    name "preprocess"
    args "input_path"
    has_return 0
    code "def preprocess(input_path: Path):&#10;    import time&#10;&#10;    print(f&#34;Preprocessing input data from {input_path}...&#34;)&#10;    time.sleep(1)&#10;&#10;"
  ]
  node [
    id 2
    label "2"
    name "train"
    args "input_path,model_path"
    has_return 0
    code "def train(input_path: Path, model_path: Path):&#10;    import time&#10;&#10;    print(f&#34;Training {model_path} on {input_path}...&#34;)&#10;    time.sleep(1)&#10;&#10;"
  ]
  node [
    id 3
    label "3"
    name "last"
    args "some_param"
    has_return 0
    code "def last(some_param: None):&#10;    return 1"
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
