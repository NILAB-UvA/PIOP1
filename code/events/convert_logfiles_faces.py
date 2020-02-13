import os.path as op
import numpy as np
import pandas as pd
from glob import glob


files = sorted(glob('../../logs/faces/raw/pi*'))
out_dir = '../../logs/faces/clean'
emo_mapper = dict(P='Pride', J='Joy', A='Anger', C='Contempt', N='Neutral')
id_mapper = {1:'1', 2:'2', 3:'3', 4:'4', 5:'6', 6:'9'}
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
    df = df.loc[~df.trial_type.isin(['Pulse', 'Response', 'Video', 'ITI', '1', '2', '100', '200', '300', '400', '500']), :]
    df = df.drop('Code', axis=1)
    df.index = range(df.shape[0])

    idf = [s.split(' ')[0].split('.')[0] for s in df.trial_type]
    df = df.drop('trial_type', axis=1)
    df['gender'] = 'Female'
    df['trial_type'] = [emo_mapper[s[0]] for s in idf]
    df['ADFES_id'] = ['F0' + id_mapper[int(s[1])] for s in idf]
    df['ethnicity'] = ['NorthEuropean' if int(s[1]) < 5 else 'Mediterranean' for s in idf]
    #df['stim_file'] = ['F0' + s[1] + '-' + emo_mapper[s[0]] + '-Face Forward.mpeg' for s in idf]
    df.trial_type = [emo_mapper[s[0]] for s in df.trial_type]
    df['duration'] = 2.00
    df = df.loc[:, ['onset', 'duration', 'trial_type', 'gender', 'ethnicity', 'ADFES_id']]
    sub_id = op.basename(f).split('-')[0][2:]
    f_out = op.join(out_dir, f'sub-{sub_id}_task-faces_acq-mb3_events.tsv')

    df.to_csv(f_out, sep='\t', index=False)
    f_out = op.join(bids_dir, f'sub-{sub_id}', 'func', f'sub-{sub_id}_task-faces_acq-mb3_events.tsv')
    if op.isdir(op.dirname(f_out)):
        df.to_csv(f_out, sep='\t', index=False)
    print(f'{f_out}, {df.shape[0]}')
