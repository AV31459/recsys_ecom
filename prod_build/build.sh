#!/bin/bash
# Just a convenience script to run dvc repro from /prod_build
cd $(dirname $0)
dvc repro $1