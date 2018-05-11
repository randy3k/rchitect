#!/bin/bash

set -e


InstallR() {
    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E084DAB9
    sudo add-apt-repository -y "deb http://cran.rstudio.com/bin/linux/ubuntu $(lsb_release -s -c)/"
    sudo apt-get update -qq -y
    if [ "$1" = "release" ]; then
        sudo apt-get install r-base r-base-core r-recommended -y
    else
        sh -c "$(curl -fsSL https://raw.githubusercontent.com/Linuxbrew/install/master/install.sh)"
        export PATH="/home/linuxbrew/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/sbin:$PATH"
        brew install https://linuxbrew.bintray.com/bottles/r-"${1}".x86_64_linux.bottle.tar.gz
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
