# docker build -t hgjazhgj/alas:latest .
# docker run -v ${PWD}:/app/AzurLaneAutoScript -p 22267:22267 --name alas -it --rm hgjazhgj/alas

FROM python:3.7-slim

WORKDIR /app/AzurLaneAutoScript

COPY requirements.txt /tmp/requirements.txt

# Initial download of UiAutomator2 is slow outside of China using appetizer mirror, switch to GitHub
RUN apt update \
 && apt install -y git adb libgomp1 openssh-client \
 && git config --global --add safe.directory '*' \
 && pip install -r /tmp/requirements.txt \
 && rm /tmp/requirements.txt \
 && rm -r ~/.cache/pip

CMD python gui.py
