# Sciflow 🔬
> This library bridges the gap between research and production for Data Science. The exploration driven development is a different paradigm to most software engineering exercises. We start by assuming only that there are high levels of uncertainty and that the code needs not only to work but to be well conditioned to real data. `sciflow` mixes the strengths of the notebook environment: flexibility, access to data and constant feedback with the strengths of production-like workflows: resilience and dedicated compute.


This file will become your README and also the index of your documentation.

## Install

# Boa
`mamba install sciflow`
# Conda
`conda install sciflow`
# Pip
`pip install sciflow`

## How to use

...

# Concepts

## Steps

Steps are functions which can be executed independently. Structuring your code into steps brigns many benefits:

* Save Time:
    * Checkpointing: can skip having to run expensive steps again
    * Re-use: write a step once and use in many different workflows

## Flows

A flow is short for workflow; they help you structure your work into something can be executed from start to finish. Structuring your work into flows has the following benefits:

* Ordered execution: anyone can run your workflow because the order is defined.
* Portability: writing your research as a flow helps to draw out dependencies on libraries or anything that can run in your environment but not elsewhere.

# Commands
       
* nbdev_diff_nbs                   
* nbdev_fix_merge          
* nbdev_test_nbs  
* nbdev_clean_nbs                                  
* nbdev_new     
* sciflow_tidy
* sciflow_build_lib
* sciflow_prepare
* sciflow_build
* sciflow_generate
* sciflow_check_flows
* sciflow_release
