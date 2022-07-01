# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/test/test_tracking.ipynb (unless otherwise specified).

__all__ = ['something', 'traffic_percent', 'workers', 'model_level', 'min_date', 'get_traffic_text',
           'get_experiment_segment', 'get_utterances', 'preprocess', 'Topics', 'fit', 'evaluate', 'serve_num_topics']

# Cell

import tempfile

import numpy as np
import pandas as pd

# step:something


def something(tracker=None):
    message = "The first step"
    print(f"{message}")
    if tracker:
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker.log_metric("auroc", 0.5, 0)
            csv_path = f"{temp_dir}/testfile.csv"
            df = pd.DataFrame({"a": [1, 2, 3], "b": ["a", "b", "c"]})
            df.to_csv(csv_path)
            tracker.add_artifact(csv_path)
            fig = df.a.plot.hist().figure
            png_path = f"{temp_dir}/testfile.png"
            fig.savefig(png_path)
            tracker.add_artifact(png_path)
    results = {"message": message}
    return results

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


def preprocess(
    message, model_level=None, min_date=None, traffic_percent=100, tracker=None
):
    print(f"I captialised the message: {message.upper()}")
    data = get_utterances(model_level, min_date, traffic_percent)
    documents = data.tolist()
    if tracker:
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker.log_metric("roc", 0.9, 0)
            csv_path = f"{temp_dir}/preprocess.csv"
            df = pd.DataFrame({"a": [1, 2, 3], "b": ["a", "b", "c"]})
            df.to_csv(csv_path)
            tracker.add_artifact(csv_path)
            fig = df.a.plot.hist().figure
            png_path = f"{temp_dir}/preprocess.png"
            fig.savefig(png_path)
            tracker.add_artifact(png_path)
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


def fit(documents, workers=workers, tracker=None):
    model = Topics(documents, workers=workers)
    if tracker:
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker.log_metric("roc", 0.9, 0)
            csv_path = f"{temp_dir}/fit.csv"
            df = pd.DataFrame({"a": [1, 2, 3], "b": ["a", "b", "c"]})
            df.to_csv(csv_path)
            tracker.add_artifact(csv_path)
            fig = df.a.plot.hist().figure
            png_path = f"{temp_dir}/fit.png"
            fig.savefig(png_path)
            tracker.add_artifact(png_path)
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
    sample_df = pd.DataFrame(
        {"a": model.get_topic_sizes()[0], "b": model.get_topic_sizes()[1]}
    )
    sample_df.to_csv("/tmp/dataframe_artifact.csv", index=False)
    artifacts = ["/tmp/dataframe_artifact.csv"]
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