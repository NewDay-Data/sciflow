
#!/usr/bin/env python3.7
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict

import boto3
import pandas as pd
import numpy as np
from six.moves.urllib.parse import urlparse
from sklearn.experimental import enable_hist_gradient_boosting
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import mean_squared_error
from sklearn.inspection import permutation_importance
import matplotlib.pyplot as plt
import joblib
import time
import logging


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sm_model_dir", type=str, default=os.environ.get("SM_MODEL_DIR")
    )
    parser.add_argument(
        "--train", type=str, default=os.environ.get("SM_CHANNEL_TRAIN")
    )
    parser.add_argument(
        "--validation", type=str, default=os.environ.get("SM_CHANNEL_VALIDATION")
    )
    parser.add_argument(
        "--hyperparameters", type=json.loads, default=os.environ["SM_HPS"]
    )
    parser.add_argument(
        "--training_env", type=json.loads, default=os.environ["SM_TRAINING_ENV"]
    )
    return parser.parse_known_args()


def parse_s3_url(url):
    """Returns an (s3 bucket, key name/prefix) tuple from a url with an s3 scheme.
    Args:
        url (str):
    Returns:
        tuple: A tuple containing:
            - str: S3 bucket name
            - str: S3 key
    """
    parsed_url = urlparse(url)
    if parsed_url.scheme != "s3":
        raise ValueError("Expecting 's3' scheme, got: {} in {}.".format(parsed_url.scheme, url))
    return parsed_url.netloc, parsed_url.path.lstrip("/")


def save_metrics(metrics: Dict, s3_dir: str, job_name: str):
    s3_client = boto3.client("s3")
    metrics_data = metrics_to_json(metrics)
    bucket, prefix = parse_s3_url(s3_dir)
    key = f"{prefix.strip('/')}/{job_name}.json"
    print(f"Uploading metrics to s3://{bucket}/{key}")
    s3_client.put_object(Body=metrics_data, Bucket=bucket, Key=key)


def main(sm_model_dir, train, validation, hyperparameters, training_env):

    model = HistGradientBoostingClassifier(**hyperparameters)
    
    logger.debug(f"Using GBM with {model.max_iter} estimators")

    with (Path(train) / "train.csv").open() as f:
        train_data = pd.read_csv(f)
    y_train = train_data.iloc[:, 0].to_numpy()
    train_data.drop(train_data.columns[0], axis=1, inplace=True)
    X_train = train_data.values
    logger.debug(f"Training data loaded")
    
    st = time.time()
    model.fit(X_train, y_train)
    train_time = (time.time() - st)/60
    logger.info(f"Model trained after: {train_time} minutes")
    
    with (Path(validation) / "validation.csv").open() as f:
        validation_data = pd.read_csv(f)
    y_val = validation_data.iloc[:, 0].to_numpy()
    validation_data.drop(validation_data.columns[0], axis=1, inplace=True)
    X_val = validation_data.values
    logger.debug(f"Validation data loaded")
    
    y_pred = model.predict(X_val)
    
    logger.debug("Calculating mean squared error.")
    mse = mean_squared_error(y_val, y_pred)
    std = np.std(y_val - y_pred)
    metrics = {
        "regression_metrics": {
            "mse": {
                "value": mse,
                "standard_deviation": std
            },
        },
    }
    
    logger.debug("Calculated mean squared error.")
    logger.info(f'Validation MSE={mse}; Validation STD={std};')

    result = permutation_importance(
        model, X_train, y_train, n_repeats=10, random_state=42, n_jobs=2
    )
    sorted_idx = result.importances_mean.argsort()

    fig, ax = plt.subplots()
    ax.boxplot(
        result.importances[sorted_idx].T, vert=False, labels=X_train.columns[sorted_idx]
    )
    ax.set_title("Permutation Importances (train set)")
    fig.tight_layout()
    plt.savefig(os.path.join(sm_model_dir, "permutation_importances_train.pdf"), dpi=150)
    
#     job_name = training_env.get("job_name")
#     metrics = {
#         "job_name": job_name,
#         **metrics,
#         **hyperparameters,
#     }
#     model_dir_bucket, _ = parse_s3_url(sm_model_dir)
#     metric_s3_dir = f"s3://{model_dir_bucket}/{METRICS_DIR_NAME}"
#     logger.debug(f"Saving metrics to: {metric_s3_dir}")
#     save_metrics(metrics, metric_s3_dir, job_name)
#     logger.debug("Saved metrics")
    
#     model_save_path = Path(sm_model_dir) / "1"
#     metrics_save_path = model_save_path / "assets" / "extra" / "metrics.json"
#     metrics_save_path.write_text(metrics_to_json(metrics))
    
    joblib.dump(model, os.path.join(sm_model_dir, "model.joblib"))
    logger.info("Model persisted to file.")
        
        
if __name__ == "__main__":
    args, unknown = parse_args()
    main(**vars(args))
