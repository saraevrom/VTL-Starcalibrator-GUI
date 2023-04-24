#!/bin/bash

source venv/bin/activate
CUDNN_PATH=$(dirname $(python -c "import nvidia.cudnn;print(nvidia.cudnn.__file__)"))
TENSORRT_PATH=$(dirname $(python -c "import tensorrt;print(tensorrt.__file__)"))
echo "CUDNN_PATH=${CUDNN_PATH}"
echo "TENSORRT_PATH=${TENSORRT_PATH}"
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CUDNN_PATH/lib:$TENSORRT_PATH/lib:
./main.py
