#!/usr/bin/env python
# coding=utf-8
# SCIFLOW GENERATED FILE - EDIT COMPANION NOTEBOOK
from metaflow import FlowSpec, step, current
from sciflow.test.test_clustering_no_params import something, preprocess, fit, evaluate
from sacred import Experiment
from sciflow.experiment.lake_observer import AWSLakeObserver
import time