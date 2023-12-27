# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/s3_utils.ipynb.

# %% auto 0
__all__ = ['is_valid_bucket', 's3_join', 'objects_exist_in_dir', 'delete_dir', 'bucket_exists', 'list_s3_subdirs', 'list_bucket',
           'put_data', 'load_json', 'upload_directory', 'download_directory']

# %% ../nbs/s3_utils.ipynb 3
# | export

import json
import os
import re
import socket
import uuid
from pathlib import Path

import boto3
from botocore.client import Config
from botocore.errorfactory import ClientError
from botocore.exceptions import ConnectTimeoutError
from nbdev.export import get_config

from .utils import lib_path, prepare_env

# %% ../nbs/s3_utils.ipynb 9
# | export


def is_valid_bucket(bucket_name):
    # See https://docs.aws.amazon.com/awscloudtrail/latest/userguide/
    # cloudtrail-s3-bucket-naming-requirements.html
    if len(bucket_name) < 3 or len(bucket_name) > 63:
        return False

    labels = bucket_name.split(".")
    # A bucket name consists of "labels" separated by periods
    for label in labels:
        if len(label) == 0 or label[0] == "-" or label[-1] == "-":
            # Labels must be of nonzero length,
            # and cannot begin or end with a hyphen
            return False
        for char in label:
            # Labels can only contain digits, lowercase letters, or hyphens.
            # Anything else will fail here
            if not (char.isdigit() or char.islower() or char == "-"):
                return False
    try:
        # If a name is a valid IP address, it cannot be a bucket name
        socket.inet_aton(bucket_name)
    except socket.error:
        return True

# %% ../nbs/s3_utils.ipynb 12
# | export


def s3_join(*args):
    return os.path.join(*args).replace("\\", "/")

# %% ../nbs/s3_utils.ipynb 15
# | export


def objects_exist_in_dir(s3_res, bucket_name, prefix):
    bucket = s3_res.Bucket(bucket_name)
    all_keys = [el.key for el in bucket.objects.filter(Prefix=prefix)]
    return len(all_keys) > 0

# %% ../nbs/s3_utils.ipynb 17
# | export


def delete_dir(s3_res, bucket_name, prefix):
    bucket = s3_res.Bucket(bucket_name)
    bucket.objects.filter(Prefix=prefix).delete()

# %% ../nbs/s3_utils.ipynb 22
# | export


def bucket_exists(s3_res, bucket_name):
    if not is_valid_bucket(bucket_name):
        raise ValueError("Bucket name does not follow AWS bucket naming rules")
    try:
        s3_res.meta.client.head_bucket(Bucket=bucket_name)
    except ClientError as er:
        if er.response["Error"]["Code"] == "404":
            return False
    return True

# %% ../nbs/s3_utils.ipynb 25
# | export


def list_s3_subdirs(s3_res, bucket_name, prefix):
    bucket = s3_res.Bucket(bucket_name)
    all_keys = [obj.key for obj in bucket.objects.filter(Prefix=prefix)]
    subdir_match = r"{prefix}\/(.*)\/".format(prefix=prefix)
    subdirs = []
    for key in all_keys:
        match_obj = re.match(subdir_match, key)
        if match_obj is None:
            continue
        else:
            subdirs.append(match_obj.groups()[0])
    distinct_subdirs = set(subdirs)
    return sorted(list(distinct_subdirs))

# %% ../nbs/s3_utils.ipynb 29
# | export


def list_bucket(bucket_name, prefix, s3_res=None):
    s3_res = s3_res if s3_res is not None else boto3.resource("s3")
    bucket = s3_res.Bucket(bucket_name)
    all_keys = [obj.key for obj in bucket.objects.filter(Prefix=prefix)]
    return all_keys

# %% ../nbs/s3_utils.ipynb 32
# | export


def put_data(s3_res, bucket_name, key, binary_data):
    s3_res.Object(bucket_name, key).put(Body=binary_data)

# %% ../nbs/s3_utils.ipynb 36
# | export


def load_json(s3_res, bucket_name, key):
    obj = s3_res.Object(bucket_name, key)
    return json.load(obj.get()["Body"])

# %% ../nbs/s3_utils.ipynb 40
# | export


def upload_directory(s3_client, path, bucket_name, prefix):
    for root, dirs, files in os.walk(path):
        if ".ipynb_checkpoints" not in root and "__pycache__" not in root:
            # Ignore non-python source files and IPython checkpoint files
            for file in [
                f
                for f in files
                if f.split(".")[-1] == "py" and root.find("ipynb_checkpoints") == -1
            ]:
                if root != path:
                    sub_dir = root.replace(path, "").lstrip("/")
                    upload_key = f"{prefix}/{sub_dir}/{file}"
                else:
                    upload_key = f"{prefix}/{file}"
                print(
                    f"Uploading file: {os.path.join(root, file)} to: {bucket_name}/{upload_key}"
                )
                s3_client.upload_file(os.path.join(root, file), bucket_name, upload_key)

# %% ../nbs/s3_utils.ipynb 43
# | export


def download_directory(s3_client, s3_res, bucket_name, remote_key, local_dir):
    if not Path(local_dir).exists():
        Path(local_dir).mkdir(parents=True)
    all_files = [
        obj.key for obj in s3_res.Bucket(bucket_name).objects.filter(Prefix=remote_key)
    ]
    for file in all_files:
        file_name = file.replace(remote_key, "").lstrip("/")
        local_path = Path(local_dir, file_name)
        if not local_path.parent.exists():
            local_path.parent.mkdir(parents=True)
        s3_client.download_file(bucket_name, file, f"{local_path}")
        assert local_path.exists()
