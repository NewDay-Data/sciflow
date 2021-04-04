from sacred import Experiment
from sacred.run import Run

ex = Experiment('hello_config')

from aws_lake_observer import AWSLakeObserver
from sacred.observers import S3Observer
obs = AWSLakeObserver(bucket='s3bawspprwe1chatbotunpub01', 
                   basedir='discovery/experiments/lake_test',
                   region='eu-west-1')

ex.observers.append(obs)

@ex.config
def my_config():
    recipient = "world"
    message = "Hello %s!" % recipient

@ex.automain
def my_main(message, _run: Run):
    _run.add_artifact('requirements.txt')
    _run.add_artifact('../dataframe_artifact.csv')
    _run.log_scalar('mae', 1.79, 0)
    _run.log_scalar('mae', 3.12, 1)
    _run.log_scalar('another one', 9.12, 0)
    print(message)