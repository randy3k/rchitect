#!/bin/bash

set -e

get_package() {
    package="$1"
    ver="$2"
    wget -qO- https://cran.rstudio.com/bin/linux/ubuntu/$(lsb_release -s -c)/ | sed -n "s/.*\(${package}\)_\($ver-[a-z0-9]*\).*/\1=\2/p" | tail -1
}

InstallR() {
    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E084DAB9
    sudo add-apt-repository -y "deb http://cran.rstudio.com/bin/linux/ubuntu $(lsb_release -s -c)/"
    sudo apt-get update -qq -y
    if [ "$1" == "r-release" ]; then
        sudo apt-get install r-base r-base-core r-recommended -y
    else
        sudo apt-get install -y \
            $(get_package r-base  "$1") \
            $(get_package r-base-core  "$1") \
            $(get_package r-recommended "$1")
    fi
}

COMMAND=$1
shift
echo "Running command: ${COMMAND} $@"
case $COMMAND in
    "install-r")
        InstallR "$@"
        ;;
esac
