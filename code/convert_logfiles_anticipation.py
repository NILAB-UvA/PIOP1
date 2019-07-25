import os.path as op
import numpy as np
import pandas as pd
from glob import glob


files = sorted(glob('../logs/anticipation/raw/pi*'))
out_dir = '../logs/anticipation/clean'
negneu_mapper = dict(neg='negative', neu='neutral')
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
            df.loc[i, 'cue_type'] = negneu_mapper[tt.split('_')[1]]
        else:
            tt = int(tt)
            df.loc[i, 'img_type'] = 'negative' if tt > 200 else 'neutral'
            
    df['duration'] = [2 if isinstance(x, str) else 3 for x in df.cue_type]
    df['trial_type'] = ['cue' if 'cue' in x else 'image' for x in df.trial_type]
    
    sub_id = op.basename(f).split('-')[0][2:]
    f_out = op.join(out_dir, f'sub-{sub_id}_task-anticipation_events.tsv')
    df.to_csv(f_out, sep='\t', index=False)
    print(f'{f_out}, {df.shape[0]}')
