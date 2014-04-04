#!/bin/sh

set -e

venvdir=$(dirname $0)/env/

if [ ! -e $venvdir ] ; then

    echo "initialize venv at $venvdir"
    pyvenv $venvdir
fi
bash --rcfile $venvdir/bin/activate
