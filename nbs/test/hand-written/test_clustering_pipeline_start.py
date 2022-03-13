# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/test/test_clustering.ipynb (unless otherwise specified).

__all__ = ['something', 'traffic_percent', 'workers', 'model_level', 'min_date', 'get_traffic_text',
           'get_experiment_segment', 'get_utterances', 'preprocess', 'Topics', 'fit', 'evaluate', 'serve_num_topics']

# step:first


def something():
    print("The first step")

# Cell


import numpy as np
import pandas as pd
from pathlib import Path
    
def lib_path(*lib_relative_path):
    lib_root_path = find_project_root(srcs=(str(Path(".").resolve()),))
    return Path(os.path.join(lib_root_path, *lib_relative_path))

# Cell

traffic_percent = 1
workers = 8
model_level = "dispatcher"
min_date = "2021-01-01"

# Cell


def get_traffic_text(percent):
    return str(percent) if int(percent) >= 10 else "0" + str(percent)

# Cell


def get_experiment_segment(traffic_percent):
    return tuple(get_traffic_text(tp) for tp in range(traffic_percent))

# Cell


def get_utterances(model_level=None, min_date=None, traffic_percent=100):
    """
    You will probably call data preparation code here. To simplify dependencies we are just creating synthetic data instead.
    """
    get_experiment_segment(traffic_percent)
    dummy_data = pd.Series(
        np.random.choice(
            [
                "Hello",
                "Goodbye",
                "Hi",
                "Can you help?",
                "I have an issue, can you help me?",
            ],
            100,
        ),
        name="utterance",
    )
    return dummy_data

# step:preprocess


def preprocess(model_level=None, min_date=None, traffic_percent=100):
    data = get_utterances(model_level, min_date, traffic_percent)
    documents = data.tolist()
    results = {"documents": documents}
    return results

# Cell


class Topics:
    def __init__(self, documents, workers):
        pass

    def get_num_topics(self):
        return 6

    def get_topic_sizes(self):
        return [1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6]

    def get_topics(self, num_topics):
        return (
            ["cat", "sat", "mat", "mouse", "house", "grouse"],
            np.asarray([1, 1, 1, 1, 1, 1]),
            [1, 2, 3, 4, 5, 6],
        )

    def plot_wordcloud(self):
        print("you may want to remove plotting code from testing to speed things up")

# step:fit


def fit(documents, workers=workers):
    model = Topics(documents, workers=workers)
    results = {"model": model}
    return results

# step:evaluate


def evaluate(model):
    topic_words, word_scores, topic_nums = model.get_topics(model.get_num_topics())

    topic_contains_non_empty_words = all([len(tw) > 0 for tw in topic_words])
    word_scores_in_range = word_scores.min() >= 0.0 and word_scores.max() <= 1.0
    as_many_items_as_topics = (
        model.get_num_topics() == len(topic_words) == word_scores.shape[0]
    )
    word_summaries = (
        topic_contains_non_empty_words
        and word_scores_in_range
        and as_many_items_as_topics
    )
    # You can add artifacts in a step that will be saved to block storage. Add the paths to the file on the local filesystem
    # and the artifact will be uploaded to remote storage.
    artifacts = [lib_path("nbs", "test", "dataframe_artifact.csv")]
    # You can add step metrics too this time just add a list of 3-tuples where tuple order = (name, value, step)
    metrics = [("mae", 100, 0), ("mae", 67, 1), ("mae", 32, 2)]
    results = {
        "word_summaries": word_summaries,
        "artifacts": artifacts,
        "metrics": metrics,
    }
    return results

# Cell
def serve_num_topics(model):
    return model.get_num_topics()


if __name__ == "__main__":
    # Fetch code from S3
    # add to path
    
    # requirements.txt is a Processing Input
    has_additional_dependencies = Path('requirements.txt').exists()
    
    if has_additional_dependencies:
        logger.info('Installing additional dependencies from requirements.txt')
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        logger.debug("Installed additional dependencies")
        
    something()