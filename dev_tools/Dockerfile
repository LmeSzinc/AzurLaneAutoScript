FROM condaforge/mambaforge:4.12.0-0

# Set remote and local dirs
WORKDIR /app
ENV SOURCE=./

# Install the base conda environment
ENV PYROOT=/app/pyroot
RUN mamba create --prefix $PYROOT python==3.7.6 -y

RUN apt update
RUN apt install -y adb netcat

# Install the requriements to the conda environment
COPY $SOURCE/requirements-in.txt /app/requirements-in.txt
RUN $PYROOT/bin/pip install -r /app/requirements-in.txt

# Initial download of UIAutomator2 is really slow with appetizer mirror
RUN sed -i "s#path = mirror_download(url,#path = cache_download(url,#" $PYROOT/lib/python3.7/site-packages/uiautomator2/init.py

# When running the image, mount the ALAS folder into the container
RUN git config --global --add safe.directory /app/AzurLaneAutoScript
CMD $PYROOT/bin/python /app/AzurLaneAutoScript/gui.py
