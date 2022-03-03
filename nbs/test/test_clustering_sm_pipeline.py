#!/usr/bin/env python
# coding=utf-8
# SCIFLOW GENERATED FILE - EDIT COMPANION NOTEBOOK
from sciflow.test.test_clustering import something, preprocess, fit, evaluate
from sciflow.test.test_clustering import traffic_percent, workers, model_level, min_date


class TestClusteringPipeline():
    traffic_percent = ParameterInteger(name="traffic_percent", default_value=traffic_percent)
    workers = ParameterInteger(name="workers", default_value=workers)
    model_level = ParameterString(name="model_level", default_value=model_level)
    min_date = ParameterString(name="min_date", default_value=min_date)
    
    # Auto-generate
    instance_count = ParameterInteger(name="instance_count", default_value=1)
    instance_type = ParameterString(name="instance_type", default_value="ml.m5.xlarge")


    steps = ["start", "preprocess", "fit"]
    
    def start(self):
        script_processor = ScriptProcessor(
            command=['python3'],
            image_uri=processing_image_uri,
            role=role,
            instance_count=processing_instance_count,
            instance_type=processing_instance_type,
            sagemaker_session=sagemaker_session,
            env={'AWS_DEFAULT_REGION': region},
            base_job_name=f'processing-job/{__file__}'
        )
        
        start_step = ProcessingStep(
            name="start",
            processor=script_processor,
            code="test_clustering_pipeline_start.py",
        )
        
        return start_step

    def preprocess(self):
        results = preprocess(self.model_level, self.min_date, self.traffic_percent)

        script_processor = ScriptProcessor(
            command=['python3'],
            image_uri=processing_image_uri,
            role=role,
            instance_count=processing_instance_count,
            instance_type=processing_instance_type,
            sagemaker_session=sagemaker_session,
            env={'AWS_DEFAULT_REGION': region},
            base_job_name=f'processing-job/{__file__}'
        )
        
        preprocess = ProcessingStep(
            name="start",
            processor=script_processor,
            outputs=[
                ProcessingOutput(output_name="documents", source="/opt/ml/processing/documents"),
                ProcessingOutput(output_name="workers", source="/opt/ml/processing/workers")
            ],
            job_arguments=[
                "--model_level", self.model_level,
                "--min_date", self.min_date,
                "--traffic_percent", self.traffic_percent,
            ]
            code="test_clustering_pipeline_start.py",
        )
        return preprocess_step

    def fit(self):
        results = fit(self.documents, self.workers)

        for key in results.keys():
            if key in self.__dict__:
                self.__dict__[key] = self.__dict__[key] + results[key]
            else:
                self.__dict__[key] = results[key]
    
    def get_pipeline(self) -> Pipeline:
        pipeline = Pipeline(
            name=pipeline_name,
            parameters=[
                processing_instance_type,
                processing_instance_count,
                training_instance_type
            ],
            steps = [f(self) for f in self.steps],
            sagemaker_session = sagemaker_session,
        )
    
    def run(self):
        pipeline = self.get_pipeline()
        pipeline.upsert(role_arn=role)
        execution = pipeline.start()
        execution.wait()
    
if __name__ == "__main__":
    SciflowPipeline()