""" Example usage of Python interface of scanphyslog2bids.
This shows how to set up a parallelized conversion workflow. """

import numpy as np
import os.path as op
import nibabel as nib
from glob import glob
from scanphyslog2bids import PhilipsPhysioLog, CouldNotFindThresholdError
from joblib import Parallel, delayed


def _run_parallel(log):
    """ Function for Parallel call """

    TRIGGER_METHOD = 'gradient_log'
    sub = op.basename(log).split('_')[0]
    nii = log.replace('_recording-respcardiac_physio.phy', '_bold.nii.gz')
    vols = nib.load(nii).shape[-1]
    tr = np.round(nib.load(nii).header['pixdim'][4], 3)
    
    if op.isfile(log.replace('.phy', '.tsv.gz')):
        print(f"Skipping {log}, as it's converted already.")
        return
    else:
        print(f"Processing {log}, with tr={tr}, n_dyns={vols}, and trigger_method={TRIGGER_METHOD}.")

    phlog = PhilipsPhysioLog(f=log, tr=tr, n_dyns=vols, sf=496, manually_stopped=False)  # init
    phlog.load()
    try:
        phlog.align(trigger_method=TRIGGER_METHOD)  # load and find vol triggers
    except CouldNotFindThresholdError:
        phlog.logger.warn("COULD NOT FIND THRESHOLD; SWITCH TO INTERPOLATION")
        phlog = PhilipsPhysioLog(f=log, tr=tr, n_dyns=vols, sf=496, manually_stopped=False)  # init
        phlog.load()    
        try:
            phlog.align(trigger_method='interpolate')
        except:
            print(f"COULD NOT CONVERT {log}!")
        else:
            out_dir = op.join(f'../../derivatives/physiology/{sub}/figures')
            phlog.plot_alignment(out_dir=out_dir)  # plots alignment with gradient
            phlog.to_bids()  # writes out .tsv.gz and .json files
            phlog.plot_traces(out_dir=out_dir)
            phlog.plot_alignment(out_dir=out_dir)
    else:
        out_dir = op.join(f'../../derivatives/physiology/{sub}/figures')
        phlog.plot_alignment(out_dir=out_dir)  # plots alignment with gradient
        phlog.to_bids()  # writes out .tsv.gz and .json files
        phlog.plot_traces(out_dir=out_dir)
        phlog.plot_alignment(out_dir=out_dir)


logs = sorted(glob('../../sub-*/func/*_physio.phy'))
Parallel(n_jobs=10)(delayed(_run_parallel)(log) for log in logs)
