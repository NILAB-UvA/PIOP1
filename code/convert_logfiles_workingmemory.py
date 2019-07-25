import os.path as op
import pandas as pd
import numpy as np
from glob import glob

p_logs = sorted(glob('../../logs/workingmemory/raw/pi*.log'))
con_mapper = {0: 'null', 1: 'active_nochange', 2: 'active_change', 3: 'passive'}
resp_mapper = {'active_nochange': 1, 'active_change': 2}
bids_dir = '../'

for p_log in p_logs:
    sub_id = op.basename(p_log).split('-')[0]
    txt = glob(op.join(op.dirname(p_log), sub_id + '*.txt'))
    if len(txt) == 0:
        print(f"Could not find txt for {sub_id}")
    elif len(txt) > 1:
        print(f"Found multiple txts for {sub_id}")
    else:
        txt = txt[0]

    df1 = pd.read_csv(p_log, skiprows=3, sep='\t')
    pulse_idx = df1.loc[df1.loc[:, 'Event Type'] == 'Pulse'].index[0]
    df1 = df1.iloc[pulse_idx:, :]
    df1 = df1.loc[:, ['Event Type', 'Code', 'Time']]
    df1 = df1.rename({'Event Type': 'trial_type', 'Time': 'onset'}, axis=1)
    start_task = df1.iloc[0, :].loc['onset']
    df1.loc[:, 'onset'] = df1.loc[:, 'onset'] - start_task
    df1 = df1.loc[df1.trial_type == 'Response', :]
    df1.onset /= 10000
    df1.index = range(df1.shape[0])
    #print(df1)

    df2 = pd.read_csv(txt, sep='\t', names=['trial_nr', 'condition', 'dur', 'response'])
    df2['condition'] = [con_mapper[x] for x in df2.condition]
    df2['response_time'] = np.nan
    df2['response_hand'] = np.nan
    df2['response_type'] = np.nan

    t = 0
    for i in range(df2.shape[0]):
        df2.loc[i, 'onset'] = t
        con = df2.loc[i, 'condition']
        df2.loc[i, 'duration'] = df2.loc[i, 'dur'] if con == 'null' else 6
        t += df2.loc[i, 'duration']

    df2['correct_resp'] = [resp_mapper[con] if 'active' in con  else np.nan for con in df2.condition]
    active_idx = df2.condition.isin(('active_change', 'active_nochange'))
    nr_resps = (df2.response != 0).sum()
    
    trials_with_resp = df2.loc[df2.condition.isin(['active_change', 'active_nochange', 'passive']), :]
    
    for idx in trials_with_resp.index:
        resp_period = trials_with_resp.loc[idx, 'onset'] + 5
        correct_resp = trials_with_resp.loc[idx, 'correct_resp']
        cond = trials_with_resp.loc[idx, 'condition']
        found = False
        for idx2 in range(df1.shape[0]):
            onset = df1.iloc[idx2].loc['onset']
            resp = df1.iloc[idx2].loc['Code']
            if (resp_period < onset) and (onset < (resp_period + 1)):
                # hit!
                if cond == 'passive':
                    rtype = np.nan
                else:
                    rtype = 'correct' if correct_resp == resp else 'incorrect'
                df2.loc[idx, 'response_time'] = onset - resp_period
                df2.loc[idx, 'response_accuracy'] = rtype
                df2.loc[idx, 'response_hand'] = 'left' if resp == 1 else 'right'
                found = True
        if not found:
            df2.loc[idx, 'response_accuracy'] = 'miss'

    df2 = df2.drop(['response', 'correct_resp', 'dur', 'trial_nr'], axis=1)
    df2 = df2.loc[df2.condition != 'null', :]
    df2 = df2.rename({'condition': 'trial_type'}, axis=1)
    corr = (df2.response_accuracy == 'correct').sum() / 32
    df2 = df2.loc[:, ['onset', 'duration', 'trial_type', 'response_accuracy', 'response_time', 'response_hand']]
    sub_id = sub_id[2:]
    f_out = f'../../logs/workingmemory/clean/sub-{sub_id}_task-workingmemory_acq-seq_events.tsv'
    print(f'{f_out}, {corr}, {df2.shape[0]}')
    df2.to_csv(f_out, sep='\t')
    f_out = f'{bids_dir}/sub-{sub_id}/func/sub-{sub_id}_task-workingmemory_acq-seq_events.tsv'
    if op.isdir(op.dirname(f_out)):
        df2.to_csv(f_out, sep='\t')
