#!/bin/bash

EPICS_SITE_TOP=/reg/g/pcds/package/epics/3.14
source $EPICS_SITE_TOP/tools/current/bin/epicsenv.sh
export EPICS_CA_MAX_ARRAY_BYTES=12000000

. /reg/g/psdm/etc/ana_env.sh
. /reg/g/psdm/bin/sit_setup.sh

PYTHONPATH=$PYTHONPATH:/reg/neh/home/koglin/lib/python

args="$@"

SOURCE="${BASH_SOURCE[0]}"
# resolve $SOURCE until the file is no longer a symlink
while [ -h "$SOURCE" ]; do 
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" 
  # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

cd $DIR
ipython -i  -c "%run psdata.py $args"


