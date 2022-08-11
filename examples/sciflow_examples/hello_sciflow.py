# AUTOGENERATED! DO NOT EDIT! File to edit: 02_hello_sciflow.ipynb (unless otherwise specified).

__all__ = ['first', 'traffic_percent', 'second']

# Cell

from pathlib import Path

from sciflow.run_flow import check_call_flow

# step:first


def first():
    print("The first step")

# Cell


# Cell

traffic_percent = 1

# step:second


def second(traffic_percent):
    results = {}
    # Currently step functions need to return a dictionary. The keys: artifacts and metrics are reserved for experiment tracking otherwiose any other named keys will be available in future steps.
    results["traffic_multiplied"] = traffic_percent * 2
    return results