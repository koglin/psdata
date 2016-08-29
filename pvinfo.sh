#!/bin/bash

show_help=0
if [[ "$1" ]]; then
  if [[ $1  == '-h' ]]; then
    show_help=1
  elif [[ $1 == '--help' ]]; then
    show_help=1
  fi
fi

#while getopts "h" opt; do
#  case $opt in
#    h)
#      show_help=1
#      ;;
#  esac
#done

export DAQREL=/reg/g/pcds/dist/pds/cxi/current
export AMIREL=/reg/g/pcds/dist/pds/cxi/ami-current
#export PYTHONPATH=~koglin/lib/python:${DAQREL}/tools/procmgr:${DAQREL}/build/pdsapp/lib/x86_64-linux:${AMIREL}/build/ami/lib/x86_64-linux
export PYTHONPATH=~koglin/lib/python:~koglin/src/psdata

EPICS_SITE_TOP=/reg/g/pcds/package/epics/3.14
source $EPICS_SITE_TOP/tools/current/bin/epicsenv.sh
export EPICS_CA_MAX_ARRAY_BYTES=12000000

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

#. /reg/g/psdm/etc/ana_env.sh
#. /reg/g/psdm/bin/sit_setup.sh
/reg/g/psdm/bin/uss.sh -s sit_setup.uss > /tmp/tmp.sh && . /tmp/tmp.sh 

rm /tmp/tmp.sh

PYTHONPATH=$PYTHONPATH:/reg/g/pcds/pyps/apps/ioc/latest
PYTHONPATH=$PYTHONPATH:/reg/g/pcds/pyps/config/cxi

python psioc.py $args

#if [ $show_help == 1 ]; then 
#  echo "show help"
#  ./psdata.py --help
#  exit 1
#else
#  ipython -i  -c "%run psdata.py $args"
#fi

