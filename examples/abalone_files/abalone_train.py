
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
from sklearn.ensemble import HistGradientBoostingRegressor
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


def plot_perm_importances(sm_model_dir, model, X, y, dataset_name: str):
    result = permutation_importance(
        model, X, y, n_repeats=10, random_state=42, n_jobs=2
    )
    sorted_idx = result.importances_mean.argsort()

    fig, ax = plt.subplots()
    ax.boxplot(
        result.importances[sorted_idx].T, vert=False, labels=X.columns[sorted_idx]
    )
    ax.set_title(f"Permutation Importances: {dataset_name}")
    fig.tight_layout()
    plt.savefig(os.path.join(sm_model_dir, f"permutation_importances_{dataset_name}.pdf"), dpi=150)

    
def main(sm_model_dir, train, validation, hyperparameters):

    model = HistGradientBoostingRegressor(**hyperparameters)
    
    logger.debug(f"Using GBM with {model.max_iter} estimators")

    with (Path(train) / "train.csv").open() as f:
        train_data = pd.read_csv(f)
    y_train = train_data.iloc[:, 0].to_numpy()
    train_data.drop(train_data.columns[0], axis=1, inplace=True)
    X_train = train_data
    logger.debug(f"Training data loaded")
    
    st = time.time()
    model.fit(X_train, y_train)
    train_time = (time.time() - st)/60
    logger.info(f"Model trained after: {train_time} minutes")
    
    with (Path(validation) / "validation.csv").open() as f:
        validation_data = pd.read_csv(f)
    y_val = validation_data.iloc[:, 0].to_numpy()
    validation_data.drop(validation_data.columns[0], axis=1, inplace=True)
    X_val = validation_data
    logger.debug(f"Validation data loaded")
    
    y_pred_train = model.predict(X_train)
    y_pred_val = model.predict(X_val)
    
    logger.debug("Calculating mean squared errors.")
    mse_train = mean_squared_error(y_train, y_pred_train)
    std_train = np.std(y_train - y_pred_train)
    mse_val = mean_squared_error(y_val, y_pred_val)
    std_val = np.std(y_val - y_pred_val)
    metrics = {
        "regression_metrics": {
            "mse": {
                "value": mse_val,
                "standard_deviation": std_val
            },
        },
    }
    
    logger.debug("Calculated mean squared errors.")
    logger.info(f'Train MSE={mse_train}; Train STD={std_train};')
    logger.info(f'Validation MSE={mse_val}; Validation STD={std_val};')

    plot_perm_importances(sm_model_dir, model, X_train, y_train, 'train')
    plot_perm_importances(sm_model_dir, model, X_val, y_val, 'validation')
    
    joblib.dump(model, os.path.join(sm_model_dir, "model.joblib"))
    logger.info("Model persisted to file.")
        
        
if __name__ == "__main__":
    args, unknown = parse_args()
    main(**vars(args))
