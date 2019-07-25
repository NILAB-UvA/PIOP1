import os
import os.path as op
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from glob import glob
import nibabel as nib
import gzip
import json


class PhilipsPhysioLog:
    """ Reads, converts, and aligns Philips physiology files (SCANPHYSLOG).
    
    Work in progress!
    """
    def __init__(self, f, fmri_file=None, n_dyns=100, sf=496, tr=None):
        """ Initializes PhilipsPhysioLog object. """
        self.f = f
        self.n_dyns = n_dyns
        self.sf = sf  # sampling freq
        self.tr = tr  # TR in secs
        self.fmri_file = fmri_file

        if fmri_file is not None:
            img = nib.load(fmri_file)
            self.tr = img.header['pixdim'][4]
            self.n_dyns = img.header['dim'][4]           
        
        if self.tr is None:
            raise ValueEror("Please provide a TR")
        
        self.trs = self.tr * self.sf

    def load(self):
        
        with open(self.f, 'r') as f_in:
            for i, line in enumerate(f_in):
                if line[:2] != '##':
                    break
        
            txt = f_in.readlines()
            txt = [line.replace('  ', ' ').replace('\n', '') for line in txt if line != '#\n']
            self.markers = np.array([s.split(' ')[9] for s in txt])

        m_start_idx = np.where(self.markers == '0100')[0]
        if len(m_start_idx) == 0:
            m_start_idx = 0
        else:
            m_start_idx = m_start_idx[-1]

        m_end_idx = np.where(self.markers == '0020')[0]
        if len(m_end_idx) == 0:
            m_end_idx = len(txt)
        else:
            m_end_idx = m_end_idx[-1]

        self.m_start_idx = m_start_idx
        self.m_end_idx = m_end_idx
        self.dat = np.loadtxt(self.f, dtype=int, usecols=np.arange(9))
        self.n = self.dat.shape[0]
        self.grad = self.dat[:, (6, 7, 8)]

        return self

    def align(self, which_grad='y'):
        
        found_end = False
        custom_end_idx = self.n
        while not found_end:
            if self.grad[(custom_end_idx - 1), :].any():
                found_end = True
            else:
                custom_end_idx -= 1
        
        self.c_end_idx = custom_end_idx
        self.align_grad = self.grad[:, {'x': 0, 'y': 1, 'z': 2}[which_grad]]
        # set prescan stuff to zero
        self.align_grad[np.arange(self.n) < self.m_start_idx] = 0
        
        approx_start = self.c_end_idx - (self.sf * self.tr * self.n_dyns) 
        approx_start -= self.trs * 0.9  # some leeway
        thr = self.align_grad.min()
        i = 0
        while True:
            # Find potential triggers
            all_triggers = (self.align_grad < thr).astype(int)
            # Remove "double" triggers
            all_triggers = np.where(np.diff(np.r_[all_triggers, 0]) == 1)[0]
            # Has to be after approximate start!
            real_triggers = all_triggers[all_triggers >= approx_start]

            # Remove false alarm triggers
            trigger_diffs = np.diff(np.r_[real_triggers, self.c_end_idx])
            real_triggers = real_triggers[trigger_diffs > (self.trs * 0.8)]

            # Check for missed triggers
            trigger_diffs = np.diff(np.r_[real_triggers, self.c_end_idx])
            prob_missed = real_triggers[np.abs(trigger_diffs - (self.trs * 2)) < 5]
            nr_added = dict(exact=0, approx=0)
            for i, trig in enumerate(prob_missed):
                period = np.zeros(self.n)
                start, end = int(trig + (self.trs * 0.9)), int(trig + (self.trs * 1.1))
                period[start:end] = self.align_grad[start:end]
                potential_missed_trigger = np.argmin(period)
                
                # Check if "exact"
                if (np.abs(potential_missed_trigger - trig) - self.trs) < 5:
                    new_trigger = potential_missed_trigger
                    nr_added['exact'] += 1
                else:
                    new_trigger = int(trig + self.trs)
                    nr_added['approx'] += 1
 
                # Append newly found trigger
                real_triggers = np.append(real_triggers, new_trigger)

            real_triggers.sort()

            if real_triggers.size == self.n_dyns:
                for k, v in nr_added.items():
                    if v > 0:
                        print(f"Added {v} triggers using the {k} method")

                break # Found it!
            
            thr += 1    
            if thr > 0:
                raise ValueError("Could not find threshold!")
        
        dummy_period = (all_triggers >= self.m_start_idx) & (all_triggers <= approx_start)
        dummy_triggers = all_triggers[dummy_period]

        trigger_diffs = np.diff(np.r_[real_triggers, self.c_end_idx])
        # Weird triggers = those with a diff much larger/smaller than TR
        weird_triggers_idx = np.abs(trigger_diffs - self.trs) > (self.trs * 0.1)
        weird_triggers_idx = np.diff(np.r_[weird_triggers_idx, 0]) == 1
        weird_triggers_diff = trigger_diffs[weird_triggers_idx]
        weird_triggers = real_triggers[weird_triggers_idx]

        if weird_triggers.size > 0:
            print(f"WARNING: found {weird_triggers.size} weird triggers!")

        print(f"Found {real_triggers.size} triggers and {dummy_triggers.size} dummies!")
        self.dummy_triggers = dummy_triggers
        self.real_triggers = real_triggers
        self.trigger_diffs = np.diff(np.r_[real_triggers, self.c_end_idx])
        self.weird_triggers = weird_triggers

        t_last_vol = (self.c_end_idx - self.real_triggers[-1]) / self.sf
        if np.abs(t_last_vol - self.tr) > 0.05:
            print(f"WARNING: last trigger might not be correct (dur = {t_last_vol:.3f})")
        
        if self.real_triggers.size != self.n_dyns:
            print("WARNING: number of volumes incorrect!")

        t_per_vol = (self.c_end_idx - self.real_triggers[0]) / self.n_dyns / self.sf
        print(f"Time per volume: {t_per_vol:.5f}")

        return self
    
    def to_bids(self):
        base_name, _ = op.splitext(self.f)
        
        time = np.arange(self.n) / self.sf
        start = time[self.real_triggers[0]]
        time = time - start

        info = {
           "SamplingFrequency": self.sf,
           "StartTime": time[0],
           "Columns": ["cardiac", "respiratory", "trigger"]
        }
        
        with open(f'{base_name}.json', "w") as write_file:
            json.dump(info, write_file, indent=4)
        
        data = self.dat[:, 4:6]
        pulses = np.zeros(self.n)
        pulses[self.real_triggers] = 1
        data = np.c_[data, pulses]
        tsv_out = f'{base_name}.tsv'
        np.savetxt(tsv_out, data, delimiter='\t')
        with open(tsv_out, 'rb') as f_in, gzip.open(tsv_out + '.gz', 'wb') as f_out:
            f_out.writelines(f_in)
        os.remove(tsv_out)
 
    def plot_alignment(self, win=4000, out_dir=None):
        
        n_weird = self.weird_triggers.size
        fig, ax = plt.subplots(nrows=4 + n_weird, figsize=(30, 9 + 3 * n_weird))
        amp = self.align_grad.min() * .25
        dummy_triggers = np.zeros(self.n)
        dummy_triggers[self.dummy_triggers] = amp
        real_triggers = np.zeros(self.n)
        real_triggers[self.real_triggers] = amp
        start_end = np.zeros(self.n)
        start_end[self.m_start_idx] = amp
        start_end[self.m_end_idx] = amp
        start_end[self.c_end_idx] = amp * 2

        windows = [
            ('Full', np.arange(self.n)[self.m_start_idx:]),
            ('Start', np.arange(self.m_start_idx, self.m_start_idx + win)),
            ('End', np.arange(self.m_end_idx - win, self.m_end_idx)),
        ]
        
        for weird_trig in self.weird_triggers:
            trig_nr = np.where(weird_trig == self.real_triggers)[0][0]
            windows.append(
                (f'Weird trigger (#{trig_nr+1}) at {weird_trig}',
                 np.arange(weird_trig - win, np.min([weird_trig + win, self.c_end_idx])))
            )

        for i, (title, period) in enumerate(windows):
            
            ext_space = 300 if i == 0 else 50
            lw_trigs = 1 if i == 0 else 2
            ax[i].plot(period, self.align_grad[period], lw=0.5)
            ax[i].plot(period, start_end[period], lw=2)
            ax[i].plot(period, dummy_triggers[period], lw=2)
            ax[i].plot(period, real_triggers[period], lw=lw_trigs)
            ax[i].set_title(title, fontsize=15)
            ax[i].set_xlim(period[0] - ext_space, period[-1] + ext_space)
            ax[i].legend(['grad', 'start/end', 'dummies', 'triggers'])

        ax[-1].plot(self.trigger_diffs)
        ax[-1].set_title('Number of samples between triggers', fontsize=15)
        fig.tight_layout()
        
        if out_dir is not None:
            f_out = op.join(out_dir, op.splitext(op.basename(self.f))[0] + '.png')
            fig.savefig(f_out, dpi=300)
            plt.close()

if __name__ == '__main__':

    from glob import glob
    files = sorted(glob('../bids/sub-*/func/*.phy'))
    
    for f in files:
        print(f"Processing {op.basename(f)}")
        nii = glob(f.split('acq-')[0] + '*.nii.gz')
        if len(nii) == 1:
            nii = nii[0]
        else:
            print(f'WARNING: found multiple nii-files for {f}: {nii}')
        
        log = PhilipsPhysioLog(f, nii)
        log.load()
        try:
            log.align()
        except ValueError as e:
            print(e)
        else:    
            log.plot_alignment(out_dir='../bids/derivatives/physio')
            log.to_bids()
