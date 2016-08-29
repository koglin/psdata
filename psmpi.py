import psdata
import numpy as np
import sys
from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

cxi = psdata.psdata(exp='cxii8715',run=27, indexed=True)

maxEventsPerNode=100000
mylength = len(cxi.times)/size
if mylength>maxEventsPerNode: mylength=maxEventsPerNode
mytimes= cxi.times[rank*mylength:(rank+1)*mylength]

for i in range(mylength):
    cxi.next_event(mytimes[i])
    img = cxi.Dg2Pim.data16
    if img is None:
        print '*** failed to get cam'
        continue
    if 'sum' in locals():
        sum+=img
    else:
        sum=img.astype(float)

    print 'rank',rank,'analyzed event with fiducials',cxi.EventId.fiducials,'and mean',img.mean()

sumall = np.empty_like(sum)
#sum the images across mpi cores
comm.Reduce(sum,sumall)
if rank==0:
    print 'sum is:\n', sumall
MPI.Finalize()


