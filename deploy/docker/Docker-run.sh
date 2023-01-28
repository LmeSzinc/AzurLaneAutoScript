#!/bin/env bash

pprint() { # Pretty print
    echo -e "==> \e[36m${1}\e[39m"
}
prun() { # Pretty run
    pprint "$ ${1}"
    eval " ${1}" || exit 1
}
prun_or_continue() { # Pretty run or continue
    pprint "$ ${1}"
    eval " ${1}" || pprint "↳ Not needed!"
}

SOURCE="$(dirname $(realpath ${BASH_SOURCE}))" # Poiting to dev_tools folder
CONTAINER="azurlaneautoscript"

# Sanity checks
if [[ "$(id -u)" -eq 0 ]]; then
    pprint "Don't run this as root!"
    exit 1
fi
# Create a lockfile so only one instance of this script can run
if [[ -f "${XDG_RUNTIME_DIR}/${CONTAINER}.lock" ]]; then
    pprint "This script is already running!"
    pprint "If this is not the case, please restart your computer!"
    exit 1
else
    touch "${XDG_RUNTIME_DIR}/${CONTAINER}.lock"
fi

# ALAS update
pprint "Updating this repo"
prun "cd ${SOURCE}/.."
prun "git fetch origin master"
prun "git stash"
prun "git pull --ff origin master"
prun_or_continue "git stash pop"

# Container cleanup
pprint "Killing any previous container"
prun "docker ps | grep ${CONTAINER} | awk '{print \$1}' | xargs -r -n1 docker kill"
pprint "Deleting old containers"
prun "docker ps -a | grep ${CONTAINER} | awk '{print \$1}' | xargs -r -n1 docker rm"

pprint "Build the image"
prun "docker build -t ${CONTAINER} -f ${SOURCE}/Dockerfile ${SOURCE}/.."

pprint "Killing any adb servers in the host machine"
prun_or_continue "adb kill-server"

pprint "Running the container"
trap "rm ${XDG_RUNTIME_DIR}/${CONTAINER}.lock && docker kill ${CONTAINER}" EXIT

prun "docker run --net=host --volume=${SOURCE}/..:/app/AzurLaneAutoScript:rw --interactive --tty --name ${CONTAINER} ${CONTAINER}"
# If you need MAA support, uncomment the following two lines and comment the line above(Modify the path of MAA according to the actual situation)
# MAA_SOURCE="${SOURCE}/../../MAA"
# prun "docker run --net=host --volume=${SOURCE}/..:/app/AzurLaneAutoScript:rw --vloume=${MAA_SOURCE}:/app/MAA:rw --interactive --tty --name ${CONTAINER} ${CONTAINER}"
