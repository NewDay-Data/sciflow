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
    train_metrics = ParameterString(name="train_metrics", default_value=None)
    
    
    # Auto-generate
    instance_count = ParameterInteger(name="instance_count", default_value=1)
    instance_type = ParameterString(name="instance_type", default_value="ml.m5.xlarge")
    
    # Hyperparameters
    # Collection of params dict -> Iterable[params]


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
            code="test_clustering_pipeline_preprocess.py",
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
            sagemaker_session=sagemaker_session,
            role=role,
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
        
        return pipeline
    
    def run(self):
        pipeline = self.get_pipeline()
        pipeline.upsert(role_arn=role)
        execution = pipeline.start()
        execution.wait()
    
if __name__ == "__main__":
    SciflowPipeline().run()