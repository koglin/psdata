#!/bin/bash

export DAQREL=/reg/g/pcds/dist/pds/cxi/current
#export AMIREL=/reg/g/pcds/dist/pds/ami-current
export AMIREL=/reg/g/pcds/dist/pds/cxi/ami-current
#export PYTHONPATH=~koglin/lib/python:${DAQREL}/tools/procmgr:${DAQREL}/build/pdsapp/lib/x86_64-linux:${AMIREL}/build/ami/lib/x86_64-linux
export PYTHONPATH=${DAQREL}/tools/procmgr:${DAQREL}/build/pdsapp/lib/x86_64-linux:${AMIREL}/build/ami/lib/x86_64-linux
#export PYTHONPATH=
export PSPKG_ROOT=/reg/common/package
export PSPKG_RELEASE=psp-2.0.0
source $PSPKG_ROOT/etc/set_env.sh

