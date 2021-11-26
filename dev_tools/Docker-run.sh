#!/bin/env bash

pprint() {
    echo -e "\n==> \e[36m$1\e[39m"
}
prun() {
    pprint "$1"
    eval " $1" || exit 1
}

SOURCE="$(dirname $(realpath $BASH_SOURCE))"

pprint "Checking for config file..."
if [[ ! -f "$SOURCE/../config/alas.json" ]]; then
    cp -a "$SOURCE/../config/template.json" "$SOURCE/../config/alas.json"
fi

pprint "Build the container"
prun "docker build -t alas -f $SOURCE/Dockerfile $SOURCE/.."

pprint "Running the container"
prun "docker run --net=host --volume=$SOURCE/../config/alas.json:/app/AzurLaneAutoScript/config/alas.json:rw --interactive --tty alas"
