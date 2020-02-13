import numpy as np 
import nibabel as nib
import json


# first non-mb
N_SLICES = 37
TR = 2
slicetimes = np.linspace(0, TR - TR / N_SLICES, N_SLICES).round(4).tolist()

wfs_hz =  434.214
wfs_ppm = 11.5
sense_acc = 2
npe = 80

ees = wfs_ppm / (wfs_hz * (npe / sense_acc))
trt = ees * (npe / sense_acc - 1)

info = dict(
    EffectiveEchoSpacing=ees,
    TotalReadoutTime=trt,
    SliceTiming=slicetimes
)

for task in ['workingmemory', 'emorecognition', 'gstroop', 'anticipation']:
    f_out = f'../task-{task}_acq-seq_bold.json'
    with open(f_out, 'w') as f:
        json.dump(info, f, indent=4)

npe = 112
wfs_ppm = 18.927
ees = wfs_ppm / (wfs_hz * (npe / sense_acc))
trt = ees * (npe / sense_acc - 1)

info = dict(
    EffectiveEchoSpacing=ees,
    TotalReadoutTime=trt
)

f_out = f'../dwi.json'
with open(f_out, 'w') as f:
    json.dump(info, f, indent=4)

## mb stuff
N_SLICES = 36
TR = 0.75
mb_factor = 3
end = TR - (TR / N_SLICES / mb_factor)
slicetimes = np.tile(np.linspace(0, end, N_SLICES // mb_factor), mb_factor).tolist()

wfs_hz =  434.214
wfs_ppm = 11
sense_acc = 2
mb_factor = 3
npe = 80

ees = wfs_ppm / (wfs_hz * (npe / sense_acc))
trt = ees * (npe / sense_acc - 1)

info = dict(
    EffectiveEchoSpacing=ees,
    TotalReadoutTime=trt,
    SliceTiming=slicetimes
)

for task in ['faces', 'restingstate']:
    f_out = f'../task-{task}_acq-mb3_bold.json'
    with open(f_out, 'w') as f:
        json.dump(info, f, indent=4)
