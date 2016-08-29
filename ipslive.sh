#!/bin/bash

echo "Starting interactive epics, pyami and pydaq"
source /reg/g/pcds/setup/pathmunge.sh

export EPICS_CA_MAX_ARRAY_BYTES=8000000
export PSPKG_ROOT=/reg/common/package

export PSPKG_RELEASE="xpp-1.1.0"
source $PSPKG_ROOT/etc/set_env.sh

export PYTHONPATH=$PYTHONPATH:/reg/g/psdm/sw/releases/ana-current/arch/x86_64-rhel6-gcc44-opt/python

#echo "Setting base python paths"
#export DAQREL=/reg/g/pcds/dist/pds/cxi/current
#export AMIREL=/reg/g/pcds/dist/pds/cxi/ami-current
#export PYTHONPATH=~/lib/python:${DAQREL}/tools/procmgr:${DAQREL}/build/pdsapp/lib/x86_64-linux:${AMIREL}/build/ami/lib/x86_64-linux:/reg/neh/operator/cxiopr/lib/python:/reg/g/pcds/controls/pycasi:/reg/g/pcds/controls:/reg/g/pcds/package/epics/3.14/extensions/current/src/ChannelArchiver/casi/python/O.linux-x86_64
#
#echo "Setting up Epics Environment"
#EPICS_SITE_TOP=/reg/g/pcds/package/epics/3.14
#source $EPICS_SITE_TOP/tools/current/bin/epicsenv.sh
#export EPICS_CA_MAX_ARRAY_BYTES=12000000

# Ana environment only words with 
#echo "Setting up Analysis Environment"
#. /reg/g/psdm/etc/ana_env.sh
#. /reg/g/psdm/bin/sit_setup.sh

#export PATH=$PATH:/reg/common/package/python/2.7.5/bin


proxy_host='daq-cxi-mon03'
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
ipython -i -c "%run pslive.py $args"


