FROM continuumio/anaconda3:2021.05

# Set remote and local dirs
WORKDIR /app
ENV SOURCE=./

# Install the base conda environment
ENV PYROOT=/app/pyroot
RUN conda create --prefix $PYROOT python==3.7.6 -y

# CV2 requires libGL.so.1
RUN apt update
RUN apt install -y libgl1 adb

# Install the requriements to the conda environment
COPY $SOURCE/requirements-in.txt /app/requirements-in.txt
RUN $PYROOT/bin/pip install -r /app/requirements-in.txt

# When running the image, mount the ALAS folder into the container
CMD $PYROOT/bin/python /app/AzurLaneAutoScript/gui.py
