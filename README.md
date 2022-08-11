```python
# hide
```

# Sciflow 🔬
***Iterate from idea to impact***


This library **bridges the gap between research and production for Data Science.** This library takes a different approach to achieve this. The interactive notebook is very well suited to facilitating exploration. However this environment does have some limitations with respect to quality and stability in pratice. 

Most exploration is only valuable if it can be turned into implemented code validated by users. `sciflow` is a meta-workflow tool that converts your notebook-based workflow to consistent, observable and managed workflows using existing popular workflow frameworks through the use of some simple commands. It mixes the strengths of the notebook environment: flexibility, access to data and constant feedback with the strengths of production-like workflows: resilience and dedicated compute.

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

# Getting Started

As `SciFlow` is built on top of `nbdev` walking through the `nbdev` [tutorial](https://nbdev.fast.ai/tutorial.html) will really help you get started using `SciFlow`. [Export](https://nbdev.fast.ai/export.html) and [test](https://nbdev.fast.ai/test.html) are the key sections for those that want to get going quickly.

## Install

* `pip install sciflow`

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

### 3.3 Inspect your notebooks for any potential quality issues [Experimental]

```console
~/codedir/project: sciflow_lint
```

### 3.4 Convert your Python Moules to Workflows

```console
~/codedir/project: sciflow_metaflow
~/codedir/project: sciflow_sagemaker
~/codedir/project: sciflow_check_metaflows
~/codedir/project: sciflow_check_sagemaker_flows
```

### 3.5 Running your workflows

```console
~/codedir/project: sciflow_run_metaflows
~/codedir/project: sciflow_run_sagemaker_flows
```


# Commands
       
* sciflow_build_lib
* nbdev_test_nbs --pause=3
* sciflow_tidy
* sciflow_clean
* sciflow_lint
* sciflow_metaflow
* sciflow_sagemaker
* sciflow_check_metaflows
* sciflow_check_sagemaker_flows
