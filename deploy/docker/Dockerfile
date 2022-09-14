FROM condaforge/mambaforge:4.12.0-0

# Install dependencies
RUN apt update && \
    apt install -y netcat unzip

# Install latest adb (41)
RUN wget https://dl.google.com/android/repository/platform-tools-latest-linux.zip && \
    unzip platform-tools-latest-linux.zip && \
    rm platform-tools-latest-linux.zip && \
    ln -s /platform-tools/adb /usr/bin/adb

# Set remote and local dirs
WORKDIR /app
ENV SOURCE=./

# Install the base conda environment
ENV PYROOT=/app/pyroot
RUN mamba create --prefix $PYROOT python==3.7.6 -y

# Install the requirements to the conda environment
COPY $SOURCE/requirements.txt /app/requirements.txt
RUN $PYROOT/bin/pip install -r /app/requirements.txt

# Initial download of UIAutomator2 is really slow with appetizer mirror (outside of China), switch to github
RUN sed -i "s#path = mirror_download(url,#path = cache_download(url,#" $PYROOT/lib/python3.7/site-packages/uiautomator2/init.py

# When running the image, mount the ALAS folder into the container
CMD $PYROOT/bin/python -m uiautomator2 init && \
    $PYROOT/bin/python /app/AzurLaneAutoScript/gui.py
