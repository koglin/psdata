__all__ = []

from psdata import *

__version__ = '00.00.01'

import logging

logger = logging.getLogger('padata')
logger.setLevel(logging.DEBUG)

#fh = logging.FileHandler('data_summary.log')
#fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
#fh.setFormatter(formatter)
ch.setFormatter(formatter)

#logger.addHandler(fh)
logger.addHandler(ch)


def set_logger_level(lvl):
    logger.setLevel( getattr(logging,lvl) )
#    fh.setLevel( getattr(logging,lvl) )
    ch.setLevel( getattr(logging,lvl) )
    return

def logger_flush():
#    fh.flush()
    return


