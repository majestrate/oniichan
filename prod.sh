#!/bin/sh
set -e
# variables
root=$(dirname $(readlink -e $0))
venvdir=$root/prod/

# set up virtual env for production
if [ ! -e $venvdir ] ; then
    echo "creating production level venv..."
    pyvenv $venvdir
fi

# source production's virtual env activate script
echo "entering prod..."
source $venvdir/bin/activate

# install packages required by oniichan app server
echo "installing app packages..."
pip3 install -r $root/requirements.txt

# install packages required by production environment
echo "installing prod packages..."
pip3 install -r $root/prod_requirements.txt

# we gud
echo 
echo "setup done"
