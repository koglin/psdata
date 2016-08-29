#!/bin/bash

echo "Setting base python paths"
export DAQREL=/reg/g/pcds/dist/pds/cxi/current
#export AMIREL=/reg/g/pcds/dist/pds/ami-current
export AMIREL=/reg/g/pcds/dist/pds/cxi/ami-current
export PYTHONPATH=~/lib/python:${DAQREL}/tools/procmgr:${DAQREL}/build/pdsapp/lib/x86_64-linux:${AMIREL}/build/ami/lib/x86_64-linux:/reg/neh/operator/cxiopr/lib/python:/reg/g/pcds/controls/pycasi:/reg/g/pcds/controls:/reg/g/pcds/package/epics/3.14/extensions/current/src/ChannelArchiver/casi/python/O.linux-x86_64

EPICS_SITE_TOP=/reg/g/pcds/package/epics/3.14
source $EPICS_SITE_TOP/tools/current/bin/epicsenv.sh
export EPICS_CA_MAX_ARRAY_BYTES=12000000

. /reg/g/psdm/etc/ana_env.sh
. /reg/g/psdm/bin/sit_setup.sh

PYTHONPATH=$PYTHONPATH:/reg/g/pcds/pyps/apps/camviewer/latest
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

./dg3_2color_plots.sh &

ipython -i  -c "%run dg3_2color.py"



