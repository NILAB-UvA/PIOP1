from glob import glob
import os

files = sorted(glob('raw/*/*.edf'))

for f in files:
    fnew = f.replace('.edf', '_phy.edf')
    os.rename(f, fnew)

