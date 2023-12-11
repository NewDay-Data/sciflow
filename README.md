# Sciflow 🔬
***Iterate from idea to impact***

`SciFlow` is a meta-workflow tool that **converts your notebook-based workflow** consistent, observable and managed workflows using existing **popular Data Science worflow frameworks** through the use of some simple commands. It mixes the strengths of the notebook environment: flexibility, access to data and constant feedback with the strengths of production-like workflows: resilience and dedicated compute.

## Convert from Notebooks to Managed Worflows

![`SciFlow` 🔬](img/sciflow_banner.PNG)

## Features
* Separate the aspects of your research that need to be validated in a production environment from your exploration journey.
* Know that your notebooks are of high quality, consistent style and that they are always in good working order.
* Automatically convert your exploratory workflows to highly visible, managed workflows.
* Explore faster: execute your current notebook-based workflow while writing it; accelerating the pace at which you can explore your problem space.
* Track experiments simply with almost no modification to your existing workflow.

## Purpose
Scientists can benefit from:
* Trying more ideas
* Easier collaboration
* Workflow portability
* Tracked Experiments

Data Science teams can benefit from:
* Shorter production lead times
* Easier collaboration between anybody involved in turning research into production
* Knowing what is important from a deployment perspective within a notebook
* Knowing that research code still has a quality standard

*Note: Sciflow is built using the excellent `nbdev` library (by fastai) and wouldn't be possible without the creation of the literate programming environment made possible by that library.*![image.png](attachment:image.png)

## Currently Supported Environments

* AWS
* *More to follow*

## Currently Supported ML Frameworks

Local
* Metaflow
* *More to follow*

Remote
* Sagemaker
* *More to follow*

# Getting Started

As `SciFlow` is built on top of `nbdev` walking through the `nbdev` [tutorial](https://nbdev.fast.ai/tutorial.html) will really help you get started using `SciFlow`. [Export](https://nbdev.fast.ai/export.html) and [test](https://nbdev.fast.ai/test.html) are the key sections for those that want to get going quickly.

## Install

* **Note:** Currently only private artifactory repositories or editable pip install are supported. Once some advanced alpha (😊) bugs have been cleared then the project will be released to pypi and public conda channels and install process will be simplified.*

### Editable pip install

The easiest approach is to install `sciflow` as an editable pip install using `pip install -e .` from the `SciFlow` projetc root directory. Activate your conda environment or virtual env before running this command.

### Pip (Artifactory)

Some one-time setup is needed for the install to work.

Create and edit a `~/.pypirc` file:

```
[distutils]
index-servers = local
[local]
repository: https://[XXX]artifactory.jfrog.io/artifactory/api/pypi/pypi
username: XXX
password: XXX
```

Create and edit a `~/.condarc` file:

```
remote_connect_timeout_secs: 25.0
remote_read_timeout_secs: 45.0
channels:
  - https://[USER]:[PWD]@[XXX]artifactory.jfrog.io/artifactory/api/conda/conda
  - https://[USER]:[PWD]@[XXX]artifactory.jfrog.io/artifactory/api/conda/conda-forge
channel_priority: flexible
```

Edit your `~/.profile` file:

```
export ARTIFACTORY_USER=XXX
export ARTIFACTORY_PASSWORD=XXX
export ARTIFACTORY_URL=[XXX]artifactory.jfrog.io
export ARTIFACTORY_CONDA_CHANNEL=conda-local
export LIB_NAME=sciflow
export VERSION=1.2.3
export BUILD_NUMBER=0
```

Then you should be able to run:

* `pip install sciflow==0.0.1`

and see:

```
Name: sciflow
Version: 0.0.1
Summary: This library bridges the gap between research and production for Data Science.
```

# How to annotate your workflow

See `examples/hello_sciflow.ipynb` for details of how to mark your notebook based workflows for conversion. Once your notebooks have been annotated correctly you can start using `SciFlow`

## 1. Initialise your project using `sciflow_init`

```console
~/codedir/project: sciflow_init
```

Edit and populate your sciflow environment file; the file will be created using `sciflow_init` you need to populate these values.

Sourcing the environment file adds the variables to the environment

```console
~/codedir/project: source "~/.sciflow/env
```

## 2. Edit your settings.ini file

You can use the settings.ini fle from `sciflow` as a base to edit and make changes to.

## 3. Test your setup

### 3.1 Converting your notebooks to Python modules then test all is working

> the order may seem unusual to build the modules then test the notebooks but this is because your project notebooks will likely import from other modules in your project so you want to test on the latest versin of these modules. 

```console

~/codedir/project: sciflow_build_lib
~/codedir/project: nbdev_test_nbs --pause=3
```

### 3.2 Ensure your notebooks have a consistent style

```console
~/codedir/project: sciflow_tidy
```

### 3.3 Convert your Python Moules to Workflows

```console
~/codedir/project: sciflow_metaflow
~/codedir/project: sciflow_sagemaker
~/codedir/project: sciflow_check_metaflows
~/codedir/project: sciflow_check_sagemaker_flows
```

### 3.4 Running your workflows

```console
~/codedir/project: sciflow_run_metaflows
~/codedir/project: sciflow_run_sagemaker_flows
```


# Commands
    
* sciflow_init
* sciflow_export
* nbdev_test_nbs
* sciflow_metaflow
* sciflow_sagemaker
* sciflow_check_metaflows
* sciflow_check_sagemaker_flows

# Development

`SciFlow` is written using `nbdev` so the means of editing this library is through the notebooks not the generated modules. The easiest way of developing `nbdev` applications is using editable pip installs:

Run this command from project root: `pip install -e .`

This ensures changes are propagated while developing and along with autoreload means you don't have to re-build all the time.
