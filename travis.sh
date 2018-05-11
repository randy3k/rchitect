#!/bin/bash

set -e


InstallR() {
    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E084DAB9
    sudo add-apt-repository -y "deb http://cran.rstudio.com/bin/linux/ubuntu $(lsb_release -s -c)/"
    sudo apt-get update -qq -y
    if [ -z "$1" ]; then
        sudo apt-get install git r-base r-base-dev r-recommended -y
    else
        RVER="$1"
        if [ "$RVER" == "3.5.0" || "$RVER" == "3.5" ]; then
            VERFLAG=""
        elif [ "$RVER" == "3.4.4" ]; then
            VERFLAG="=3.4.4-1trusty0"
        elif [ "$RVER" == "3.4.3" ]; then
            VERFLAG="=3.4.3-1trusty0"
        elif [ "$RVER" == "3.4.2" ]; then
            VERFLAG="=3.4.2-2trusty"
        elif [ "$RVER" == "3.4.1" ]; then
            VERFLAG="=3.4.1-2trusty0"
        elif [ "$RVER" == "3.4.0" ]; then
            VERFLAG="=3.4.0-1trusty0"
        fi
        echo download R version "$1"
        sudo apt-get install git r-base"$VERFLAG" -y
        sudo apt-get install git r-base-dev"$VERFLAG" -y
        sudo apt-get install git r-recommended"$VERFLAG" -y
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
