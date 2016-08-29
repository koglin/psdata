#!/bin/bash

echo "Starting interactive ami with psami"

echo "Setting base python paths"
export DAQREL=/reg/g/pcds/dist/pds/cxi/current
#export AMIREL=/reg/g/pcds/dist/pds/ami-current
export AMIREL=/reg/g/pcds/dist/pds/cxi/ami-current
export PYTHONPATH=~/lib/python:${DAQREL}/build/pdsapp/lib/x86_64-linux:${AMIREL}/build/ami/lib/x86_64-linux:/reg/neh/operator/cxiopr/lib/python:/reg/g/pcds/controls/pycasi:/reg/g/pcds/controls:/reg/g/pcds/package/epics/3.14/extensions/current/src/ChannelArchiver/casi/python/O.linux-x86_64

echo "Setting up Epics Environment"
EPICS_SITE_TOP=/reg/g/pcds/package/epics/3.14
source $EPICS_SITE_TOP/tools/current/bin/epicsenv.sh

echo "Setting up Analysis Environment"
. /reg/g/psdm/etc/ana_env.sh
. /reg/g/psdm/bin/sit_setup.sh

proxy_host='daq-cxi-mon02'
args="$@ -p $proxy_host"

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

echo "Starting psami on $proxy_node with options: $args"
ipython -i  -c "%run psami.py $args"
#ipython -i -c "%run psami.py $args -p='$proxy_host'"
#ipython -i -c "%run psami.py -p='$proxy_host'"


