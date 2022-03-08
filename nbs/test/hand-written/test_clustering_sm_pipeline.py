#!/usr/bin/env python
# coding=utf-8
# SCIFLOW GENERATED FILE - EDIT COMPANION NOTEBOOK

import os

import sagemaker
from sagemaker.session import Session

from sagemaker.inputs import TrainingInput
from sagemaker.processing import ScriptProcessor, ProcessingInput, ProcessingOutput
from sagemaker.workflow.parameters import ParameterInteger, ParameterString
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep, TrainingStep
from sagemaker.estimator import Estimator

from sciflow.test.test_clustering import something, preprocess, fit, evaluate
from sciflow.test.test_clustering import traffic_percent, workers, model_level, min_date


class TestClusteringPipeline():
    traffic_percent = ParameterInteger(name="traffic_percent", default_value=traffic_percent)
    workers = ParameterInteger(name="workers", default_value=workers)
    model_level = ParameterString(name="model_level", default_value=model_level)
    min_date = ParameterString(name="min_date", default_value=min_date)
    
    
    # Auto-generate
    proc_image_uri = ParameterString(name="proc_image_uri", default_value="141502667606.dkr.ecr.eu-west-1.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3")
    proc_instance_count = ParameterInteger(name="proc_instance_count", default_value=1)
    proc_instance_type = ParameterString(name="proc_instance_type", default_value="ml.m5.xlarge")
    
    train_image_uri = ParameterString(name="train_image_uri", default_value="141502667606.dkr.ecr.eu-west-1.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3")
    train_instance_type = ParameterString(name="train_instance_type", default_value="ml.m5.xlarge")
    
    # Hyperparameters
    # Collection of params dict -> Iterable[params]

    steps = ["start", "preprocess", "fit", "evaluate"]
    
    def start(self):
        script_processor = ScriptProcessor(
            command=['python3'],
            image_uri=self.proc_image_uri,
            role=self.role,
            instance_count=self.proc_instance_count,
            instance_type=self.proc_instance_type,
            sagemaker_session=self.sagemaker_session,
            env={'AWS_DEFAULT_REGION': self.region},
            base_job_name=f'processing-job/{__file__}'
        )
        
        start_step = ProcessingStep(
            name="start",
            processor=script_processor,
            code="test_clustering_pipeline_start.py",
        )
        
        self.start_step = start_step
        return start_step

    def preprocess(self):
        script_processor = ScriptProcessor(
            command=['python3'],
            image_uri=self.proc_image_uri,
            role=self.role,
            instance_count=self.proc_instance_count,
            instance_type=self.proc_instance_type,
            sagemaker_session=self.sagemaker_session,
            env={'AWS_DEFAULT_REGION': self.region},
            base_job_name=f'processing-job/{__file__}'
        )
        
        preprocess_step = ProcessingStep(
            name="preprocess",
            processor=script_processor,
            outputs=[
                ProcessingOutput(output_name="documents", source="/opt/ml/processing/documents"),
                ProcessingOutput(output_name="workers", source="/opt/ml/processing/workers")
            ],
            job_arguments=[
                "--model_level", self.model_level.__str__(),
                "--min_date", self.min_date.__str__(),
                "--traffic_percent", str(self.traffic_percent.__int__()),
            ],
            code = "test_clustering_pipeline_preprocess.py"
        )
        
        self.preprocess_step = preprocess_step
        return preprocess_step

    def fit(self):
        metrics = ["Train MSE", "Train STD", "Validation MSE", "Validation STD"]
        metrics_regex = [{"Name": m, "Regex": f"{m}=(.*?);"} for m in metrics]

        estimator = Estimator(
            image_uri = self.train_image_uri,
            entry_point="test_clustering_pipeline_fit.py",
            #hyperparameters={"max_iter": 30, "learning_rate": 0.1},
            instance_type=self.train_instance_type,
            instance_count=1,
            output_path=f"s3://{os.environ['SCIFLOW_BUCKET']}/test_clustering/training-job-output",
            base_job_name=f'processing-job/{__file__}',
            sagemaker_session = self.sagemaker_session,
            role = self.role,
            metric_definitions=metrics_regex,
            enable_sagemaker_metrics=True,
        )

        step_train = TrainingStep(
            name="fit-cluster",
            estimator=estimator,
            inputs={
                "documents": TrainingInput(
                    s3_data=self.preprocess_step.properties.ProcessingOutputConfig.Outputs[
                        "documents"
                    ].S3Output.S3Uri,
                    content_type="text/csv",
                ),
                "workers": TrainingInput(
                    s3_data=self.preprocess_step.properties.ProcessingOutputConfig.Outputs[
                        "workers"
                    ].S3Output.S3Uri,
                    content_type="text/csv",
                ),
            }
        )
        
        self.step_train = step_train
        return step_train
    
    
    def evaluate(self):
        script_processor = ScriptProcessor(
            command=['python3'],
            image_uri=self.proc_image_uri,
            role=self.role,
            instance_count=self.proc_instance_count,
            instance_type=self.proc_instance_type,
            sagemaker_session=self.sagemaker_session,
            env={'AWS_DEFAULT_REGION': self.region},
            base_job_name=f'processing-job/{__file__}'
        )
        
        evaluate_step = ProcessingStep(
            name="evaluate",
            processor=script_processor,
            inputs = [
                ProcessingInput(source=self.step_train.properties.ModelArtifacts.S3ModelArtifacts, destination="/opt/ml/processing/model")
            ],
            outputs=[
                ProcessingOutput(output_name="word_summaries", source="/opt/ml/processing/word_summaries"),
                ProcessingOutput(output_name="artifacts", source="/opt/ml/processing/artifacts"),
                ProcessingOutput(output_name="metrics", source="/opt/ml/processing/metrics")
            ],
            code = "test_clustering_pipeline_evaluate.py"
        )
        
        self.evaluate_step = evaluate_step
        return evaluate_step
    
    def get_pipeline(self) -> Pipeline:
        pipeline_steps = [getattr(self, step)() for step in self.steps]
        pipeline = Pipeline(
            name="test-clustering-sm-pipeline",
            parameters=[
                self.proc_image_uri,
                self.proc_instance_type,
                self.proc_instance_count,
                self.train_image_uri,
                self.train_instance_type,
                self.traffic_percent,
                self.workers,
                self.model_level,
                self.min_date 
            ],
            steps = pipeline_steps,
            sagemaker_session = self.sagemaker_session,
        )
        
        return pipeline
    
    def run(self):
        self.bucket = os.environ['SCIFLOW_BUCKET']
        self.role = sagemaker.get_execution_role()
        self.region = 'eu-west-1'
        self.sagemaker_session = Session(default_bucket=self.bucket)
        
        pipeline = self.get_pipeline()
        pipeline.upsert(role_arn=self.role)
        execution = pipeline.start()
        execution.wait()
    
if __name__ == "__main__":
    TestClusteringPipeline().run()