# First arm64 version
FROM continuumio/anaconda3:2021.11

# Set remote and local dirs
WORKDIR /app

# Install the base conda environment
# Cannot find python 3.7.6 for arm64, so use 3.7.10
ENV PYROOT=/app/pyroot
RUN conda create --prefix $PYROOT python==3.7.10 -y

# CV2 requires libGL.so.1
RUN apt-get update && apt-get install -y libgl1 adb libatlas-base-dev libopencv-dev build-essential && rm -rf /var/lib/apt/lists/*

# Install the requriements to the conda environment
COPY ./requirements.txt /app/requirements.txt
RUN $PYROOT/bin/pip install -r /app/requirements.txt

RUN wget https://raw.githubusercontent.com/binss/python-wheel/main/mxnet-1.9.1-py3-none-any.whl -P /app/
RUN $PYROOT/bin/pip uninstall mxnet -y && $PYROOT/bin/pip install /app/mxnet-1.9.1-py3-none-any.whl

ENV LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/app/pyroot/mxnet/"

# When running the image, mount the ALAS folder into the container
CMD $PYROOT/bin/python /app/AzurLaneAutoScript/gui.py
