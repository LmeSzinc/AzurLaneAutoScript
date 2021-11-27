#!/bin/env bash

pprint() { # Pretty print
    echo -e "==> \e[36m$1\e[39m"
}
prun() { # Pretty run
    pprint "$ $1"
    eval " $1" || exit 1
}

SOURCE="$(dirname $(realpath $BASH_SOURCE))" # Poiting to dev_tools folder
CONTAINER="azurlaneautoscript"

pprint "Updating this repo"
prun "git fetch origin master"
prun "git stash"
prun "git pull origin master"
prun "git stash pop" || pprint "Not needed"

pprint "Checking for existing config file"
if [[ ! -f "$SOURCE/../config/alas.json" ]]; then
    prun "cp -a \"$SOURCE/../config/template.json\" \"$SOURCE/../config/alas.json\""
else
    pprint "Config file OK"
fi

pprint "Killing any previous container"
prun "docker ps | grep $CONTAINER | awk '{print \$1}' | xargs -r -n1 docker kill"

pprint "Deleting old containers..."
prun "docker ps -a | grep $CONTAINER | awk '{print \$1}' | xargs -r -n1 docker rm"

pprint "Build the container"
prun "docker build -t $CONTAINER -f $SOURCE/Dockerfile $SOURCE/.."

pprint "Running the container"
prun "docker run --net=host --volume=$SOURCE/../config/alas.json:/app/AzurLaneAutoScript/config/alas.json:rw --interactive --tty $CONTAINER"
