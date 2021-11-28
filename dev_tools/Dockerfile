FROM continuumio/anaconda3:2021.05

# Set remote and local dirs
ENV WD=/app
ENV SOURCE=./
WORKDIR $WD

# Install the base conda environment
ENV PYROOT=$WD/pyroot
RUN conda create --prefix $PYROOT python==3.7.6 -y

# CV2 requires libGL.so.1
RUN apt update
RUN apt install -y libgl1 adb

# Install the requriements to the conda environment
# So we can cache this layer
COPY $SOURCE/requirements-in.txt $WD/requirements-in.txt
RUN $PYROOT/bin/pip install -r $WD/requirements-in.txt

CMD $PYROOT/bin/python $WD/AzurLaneAutoScript/gui.py
