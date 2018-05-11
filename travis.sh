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
    if [ -z "$1" ]; then
        sudo apt-get install git r-base r-base-dev r-recommended -y
    elser
        sudo apt-get install git $(get_package r-base "$1") -y
        sudo apt-get install git $(get_package r-base-dev "$1") -y
        sudo apt-get install git $(get_package r-recommended "$1") -y
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
