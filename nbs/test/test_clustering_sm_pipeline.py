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

from sciflow.test.test_clustering import something, preprocess, fit, evaluate
from sciflow.test.test_clustering import traffic_percent, workers, model_level, min_date


class TestClusteringPipeline():
    traffic_percent = ParameterInteger(name="traffic_percent", default_value=traffic_percent)
    workers = ParameterInteger(name="workers", default_value=workers)
    model_level = ParameterString(name="model_level", default_value=model_level)
    min_date = ParameterString(name="min_date", default_value=min_date)
    train_metrics = ParameterString(name="train_metrics", default_value=None)
    
    
    # Auto-generate
    proc_image_uri = ParameterString(name="proc_image_uri", default_value="141502667606.dkr.ecr.eu-west-1.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3")
    proc_instance_count = ParameterInteger(name="proc_instance_count", default_value=1)
    proc_instance_type = ParameterString(name="proc_instance_type", default_value="ml.m5.xlarge")
    
    train_image_uri = ParameterString(name="train_image_uri", default_value="141502667606.dkr.ecr.eu-west-1.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3")
    train_instance_type = ParameterString(name="train_instance_type", default_value="ml.m5.xlarge")
    
    # Hyperparameters
    # Collection of params dict -> Iterable[params]

    
    steps = ["start", "preprocess"]
    
    #steps = ["start", "preprocess", "fit"]
    
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
                "--model_level", self.model_level,
                "--min_date", self.min_date,
                "--traffic_percent", self.traffic_percent,
            ],
            code = "test_clustering_pipeline_preprocess.py"
        )
        
        return preprocess_step

    def fit(self):
        metrics = self.train_metrics.split(',')
        metrics_regex = [{"Name": m, "Regex": f"{m}=(.*?);"} for m in metrics]

        estimator = Estimator(
            source_dir="abalone_files",
            entry_point="test_clustering_pipeline_fit.py",
            hyperparameters={"max_iter": 30, "learning_rate": 0.1},
            instance_type=training_instance_type,
            instance_count=1,
            output_path=model_path,
            base_job_name=f'processing-job/{__file__}',
            sagemaker_session = self.sagemaker_session,
            role = self.role,
            metric_definitions=metrics_regex,
            enable_sagemaker_metrics=True,
        )

        step_train = TrainingStep(
            name="TrainAbaloneModel",
            estimator=sklearn_estimator,
            inputs={
                "documents": TrainingInput(
                    s3_data=step_process.properties.ProcessingOutputConfig.Outputs[
                        "train"
                    ].S3Output.S3Uri,
                    content_type="text/csv",
                ),
                "workers": TrainingInput(
                    s3_data=step_process.properties.ProcessingOutputConfig.Outputs[
                        "validation"
                    ].S3Output.S3Uri,
                    content_type="text/csv",
                ),
            },
        )
        return step_train
    
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