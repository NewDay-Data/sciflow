# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/test/test_clustering.ipynb (unless otherwise specified).

__all__ = ['something', 'traffic_percent', 'speed', 'workers', 'dremio_access', 'model_level', 'min_date',
           'get_traffic_text', 'get_experiment_segment', 'get_utterances', 'get_button_responses_filter', 'preprocess',
           'Topics', 'fit', 'get_num_docs', 'evaluate', 'serve_num_topics', 'serve_reduced_hierarchies']

# step:first


def something():
    pass

# Cell


import numpy as np
import pandas as pd
from ..utils import load_dremio_access

# Cell

traffic_percent = 1
speed = "fast-learn"
workers = 8
dremio_access = load_dremio_access()
model_level = "TopLevelDispatcher"
min_date = "2021-01-01"

# Cell
def get_traffic_text(percent):
    return str(percent) if int(percent) >= 10 else "0" + str(percent)

# Cell
def get_experiment_segment(traffic_percent):
    return tuple(get_traffic_text(tp) for tp in range(traffic_percent))

# Cell


def get_utterances(dremio_access, model, min_date, traffic_percent):
    segment = get_experiment_segment(traffic_percent)
    return dremio_access.read_sql_to_dataframe(
        f"""
    select Utterance from "chatbot_unpublish_s3"."lambda-output"."finn_feedback"
    where model = '{model}' and to_date(substr("Timestamp", 0, 10), 'YYYY-MM-dd') >= to_date('{min_date}', 'YYYY-MM-dd')
    and substr(AccountNumber, 15, 16) IN ('{"','".join(segment)}')
    """
    )

# Cell


def get_button_responses_filter(dremio_access):
    button_responses_query = f"""
    SELECT "text"
    FROM "chatbot_unpublish_s3"."lambda-output"."live_person".messages a
    inner join "chatbot_unpublish_s3"."lambda-output".digital.events b
    on a."conversationId" = b."LivePersonConversationId"
    where b.QuickReplyButton = true and a.eventBy = 'Consumer'
    """
    button_responses = dremio_access.read_sql_to_dataframe(button_responses_query)
    additional_button_responses = [
        "Transaction enquiry",
        "Transaction Enquiry",
        "Hi",
        "Hello",
        "Card declined",
        "Close account",
    ]
    return button_responses.text.tolist() + additional_button_responses

# step:preprocess


def preprocess(dremio_access, model_level, min_date, traffic_percent):
    data = get_utterances(dremio_access, model_level, min_date, traffic_percent)
    button_filter = get_button_responses_filter(dremio_access)
    user_texts = data[~data.Utterance.isin(button_filter)].copy()
    documents = user_texts.Utterance.tolist()
    return documents

# Cell


class Topics:
    def __init__(self, documents, workers, speed):
        pass

    def get_num_topics(self):
        return 6

    def get_topic_sizes(self):
        return [1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6]

    def get_topics(self):
        return (
            ["cat", "sat", "mat", "mouse", "house", "grouse"],
            [1, 1, 1, 1, 1, 1],
            [1, 2, 3, 4, 5, 6],
        )

    def search_documents_by_topic(self, topic_num):
        return (
            ["cat", "sat", "mat", "mouse", "house", "grouse"],
            [1, 1, 1, 1, 1, 1],
            [1, 2, 3, 4, 5, 6],
        )

    def generate_topic_wordcloud(self, topic_num):
        print("wordcloud")

    def hierarchical_topic_reduction(self):
        return ["cat", "sat", "mat"]

# step:fit


def fit(documents, workers=workers, speed="fast-learn"):
    model = Topics(documents, workers=workers, speed=speed)
    return model

# Cell
def get_num_docs(topic_idx, topic_sizes, max_k=50):
    n_docs = topic_sizes[topic_idx]
    return n_docs if n_docs < max_k else max_k

# step:evaluate


def evaluate(model):
    topic_words, word_scores, topic_nums = model.get_topics(model.get_num_topics())

    topic_contains_non_empty_words = all([len(tw) > 0 for tw in topic_words])
    word_scores_in_range = word_scores.min() >= 0.0 and word_scores.max() <= 1.0
    as_many_items_as_topics = (
        model.get_num_topics() == len(topic_words) == word_scores.shape[0]
    )
    results = (
        topic_contains_non_empty_words
        and word_scores_in_range
        and as_many_items_as_topics
    )
    return results

# Cell
def serve_num_topics(model):
    return model.get_num_topics()

# Cell
def serve_reduced_hierarchies(model, desired_num_topics):
    return model.hierarchical_topic_reduction(desired_num_topics)