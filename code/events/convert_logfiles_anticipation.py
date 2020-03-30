import os.path as op
import numpy as np
import pandas as pd
from glob import glob


files = sorted(glob('../../logs/anticipation/raw/pi*'))
out_dir = '../../logs/anticipation/clean'
negneu_mapper = dict(neg='negative', neu='neutral')
bids_dir = '../'
for f in files:
    df = pd.read_csv(f, sep='\t', skiprows=3)
    pulse_idx = df.loc[df.loc[:, 'Event Type'] == 'Pulse'].index[0]
    df = df.iloc[pulse_idx:, :]
    df = df.loc[:, ['Event Type', 'Code', 'Time']]
    df = df.rename({'Event Type': 'trial_type', 'Time': 'onset'}, axis=1)
    start_task = df.iloc[0, :].loc['onset']
    df.loc[:, 'onset'] = df.loc[:, 'onset'] - start_task
    df = df.loc[df.trial_type != 'Pulse', :]
    df.onset /= 10000
    df['trial_type'] = df['Code']
    df = df.loc[~df.trial_type.isin(['ITI', 'Response', '1', '2', '3', '4']), :]
    df = df.drop('Code', axis=1)
    df.index = range(df.shape[0]) 
    for i, tt in enumerate(df.trial_type):
        if 'cue' in tt:
            df.loc[i, 'trial_type'] = 'cue_' + negneu_mapper[tt.split('_')[1]]
        else:
            tt = int(tt)
            df.loc[i, 'trial_type'] = 'img_negative' if (tt < 200 or tt > 399) else 'img_neutral'
            
    df['duration'] = [2 if 'cue' in x else 3 for x in df.trial_type]
    df = df.loc[:, ['onset', 'duration', 'trial_type']]
    sub_id = op.basename(f).split('-')[0][2:]
    f_out = op.join(out_dir, f'sub-{sub_id}_task-anticipation_acq-seq_events.tsv')
    df.to_csv(f_out, sep='\t', index=False)

    f_out = op.join(bids_dir, f'sub-{sub_id}', 'func', f'sub-{sub_id}_task-anticipation_acq-seq_events.tsv')
    if op.isdir(op.dirname(f_out)):
        df.to_csv(f_out, sep='\t', index=False)

    print(f'{f_out}, {df.shape[0]}')
