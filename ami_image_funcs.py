def Xprofile(self):
    return self.data_array.sum(axis=0)

def Yprofile(self):
    return self.data_array.sum(axis=1)

def data_array(self):
    import numpy as np
    return np.array(self.data)

def showX(self):
    """Show the X profile in the terminal
    """
    dat = self.data_array.sum(axis=0)
    dat.resize(40)
    dat = dat-dat.min()
    for i,val in enumerate(dat):
        print '{:4d} {:}'.format(i,'*'*int(val/max(dat)*80))

def showY(self):
    """Show the Y profile in the terminal
    """
    dat = self.data_array.sum(axis=1)
    dat.resize(40)
    dat = dat-dat.min()
    for i,val in enumerate(dat):
        print '{:4d} {:}'.format(i,'*'*int(val/max(dat)*80))



