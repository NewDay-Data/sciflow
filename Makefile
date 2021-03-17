.ONESHELL:
SHELL := /bin/bash
SRC = $(wildcard ./*.ipynb)
VERSION = grep version settings.ini | cut -d'=' -f2 | xargs
# TODO - need to generate meta.yaml from settings.ini
BUILD_NUMBER=0

all: {lib_name} docs

{lib_name}: $(SRC)
	nbdev_build_lib
	touch {lib_name}

sync:
	nbdev_update_lib

docs_serve: docs
	cd docs && bundle exec jekyll serve

docs: $(SRC)
	nbdev_build_docs
	touch docs

test:
	nbdev_test_nbs

local_release: art_pip art_conda
	nbdev_bump_version

art_conda: 
    mkdir conda-local-build
    conda mambabuild . --output-folder conda-build
    curl -4 -XPUT "https://${ARTIFACTORY_USER}:${ARTIFACTORY_PASSWORD}@$ARTIFACTORY_URL/artifactory/${ARTIFACTORY_CONDA_CHANNEL}/linux-64/" -T linux-64/{lib_name}-$(VERSION)-$(BUILD_NUMBER).tar.bz2
    rm -rf conda-local-build

art_pip: dist
	twine upload --repository local dist/*
    
release: pypi conda_release
	nbdev_bump_version

conda_release:
	fastrelease_conda_package

pypi: dist
	twine upload --repository pypi dist/*

dist: clean
	python setup.py sdist bdist_wheel

clean:
	rm -rf dist