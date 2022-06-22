FROM condaforge/mambaforge:4.12.0-0

# Install dependencies
RUN apt update && \
    apt install -y adb netcat

# Create user
RUN useradd -m abc && \
    usermod -G users abc

# Set remote and local dirs
WORKDIR /app
ENV SOURCE=./
RUN chown abc:abc /app
USER abc

# Install the base conda environment
ENV PYROOT=/app/pyroot
RUN mamba create --prefix $PYROOT python==3.7.6 -y

# Install the requriements to the conda environment
COPY --chown=abc:abc $SOURCE/requirements.txt /app/requirements.txt
RUN $PYROOT/bin/pip install -r /app/requirements.txt

# Initial download of UIAutomator2 is really slow with appetizer mirror
RUN sed -i "s#path = mirror_download(url,#path = cache_download(url,#" $PYROOT/lib/python3.7/site-packages/uiautomator2/init.py

# When running the image, mount the ALAS folder into the container
CMD $PYROOT/bin/python /app/AzurLaneAutoScript/gui.py
