import os.path as op
import numpy as np
import pandas as pd
from glob import glob

hand_mapper = {1: 'left', 2: 'right'}
image_mapper = {
    11: dict(gender='male', ethn_target='caucasian', ethn_match='caucasian', ethn_distractor='caucasian', emo_match='anger', correct=1),
    12: dict(gender='female', ethn_target='caucasian', ethn_match='caucasian', ethn_distractor='caucasian', emo_match='fear', correct=1),
    13: dict(gender='male', ethn_target='black', ethn_match='black', ethn_distractor='black', emo_match='anger', correct=2),
    14: dict(gender='female', ethn_target='black', ethn_match='asian', ethn_distractor='asian', emo_match='anger', correct=1),
    15: dict(gender='male', ethn_target='caucasian', ethn_match='caucasian', ethn_distractor='white', emo_match='fear', correct=2),
    16: dict(gender='female', ethn_target='asian', ethn_match='asian', ethn_distractor='black', emo_match='fear', correct=2),
    21: dict(gender='male', ethn_target='caucasian', ethn_match='caucasian', ethn_distractor='caucasian', emo_match='fear', correct=2),
    22: dict(gender='female', ethn_target='black', ethn_match='asian', ethn_distractor='asian', emo_match='fear', correct=1),
    23: dict(gender='male', ethn_target='caucasian', ethn_match='caucasian', ethn_distractor='caucasian', emo_match='anger', correct=2),
    24: dict(gender='male', ethn_target='black', ethn_match='black', ethn_distractor='black', emo_match='fear', correct=1),
    25: dict(gender='female', ethn_target='caucasian', ethn_match='caucasian', ethn_distractor='caucasian', emo_match='anger', correct=1),
    26: dict(gender='female', ethn_target='asian', ethn_match='asian', ethn_distractor='black', emo_match='anger', correct=2),
    31: dict(gender='female', ethn_target='caucasian', ethn_match='caucasian', ethn_distractor='caucasian', emo_match='fear', correct=1),
    32: dict(gender='male', ethn_target='black', ethn_match='black', ethn_distractor='black', emo_match='anger', correct=2),
    33: dict(gender='female', ethn_target='caucasian', ethn_match='caucasian', ethn_distractor='caucasian', emo_match='anger', correct=2),
    34: dict(gender='male', ethn_target='black', ethn_match='black', ethn_distractor='black', emo_match='fear', correct=1),
    35: dict(gender='male', ethn_target='caucasian', ethn_match='caucasian', ethn_distractor='caucasian', emo_match='anger', correct=1),
    36: dict(gender='female', ethn_target='asian', ethn_match='black', ethn_distractor='asian', emo_match='fear', correct=2),
    41: dict(gender='female', ethn_target='caucasian', ethn_match='caucasian', ethn_distractor='caucasian', emo_match='anger', correct=2),
    42: dict(gender='male', ethn_target='black', ethn_match='black', ethn_distractor='black', emo_match='anger', correct=1),
    43: dict(gender='female', ethn_target='caucasian', ethn_match='caucasian', ethn_distractor='caucasian', emo_match='fear', correct=2),
    44: dict(gender='male', ethn_target='black', ethn_match='black', ethn_distractor='black', emo_match='fear', correct=2),
    45: dict(gender='male', ethn_target='caucasian', ethn_match='caucasian', ethn_distractor='caucasian', emo_match='fear', correct=1),
    46: dict(gender='female', ethn_target='asian', ethn_match='black', ethn_distractor='asian', emo_match='anger', correct=1),
    51: dict(ori_match='horizontal', correct=1),
    52: dict(ori_match='vertical', correct=2),
    53: dict(ori_match='vertical', correct=1),
    54: dict(ori_match='vertical', correct=2),
    55: dict(ori_match='vertical', correct=2),
    56: dict(ori_match='horizontal', correct=1),
    61: dict(ori_match='horizontal', correct=1),
    62: dict(ori_match='horizontal', correct=2),
    63: dict(ori_match='vertical', correct=1),
    64: dict(ori_match='vertical', correct=2),
    65: dict(ori_match='horizontal', correct=2),
    66: dict(ori_match='vertical', correct=1),
    71: dict(ori_match='horizontal', correct=1),
    72: dict(ori_match='horizontal', correct=2),
    73: dict(ori_match='vertical', correct=1),
    74: dict(ori_match='vertical', correct=2),
    75: dict(ori_match='horizontal', correct=2),
    76: dict(ori_match='vertical', correct=1)
}


files = sorted(glob('../logs/emorecognition/raw/pi*'))
out_dir = '../logs/emorecognition/clean'
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

    new_df = pd.DataFrame(columns=['onset', 'duration', 'event_type',
                                   'response_time', 'response_hand', 'response_type'])

    i = 0
    trial_i = 0
    hand_mapper = {1: 'left', 2: 'right'}
    while True:
        row = df.iloc[i, :]
        if row.trial_type == 'Picture':
            new_df.loc[trial_i, 'onset'] = df.iloc[i, :].loc['onset']
            for k, v in image_mapper[df.iloc[i, :].loc['Code']].items():
                new_df.loc[trial_i, k] = v
            #new_df.loc[trial_i, 'img'] = df.iloc[i, :].loc['Code']
            trial_i += 1

        if row.trial_type == 'Response':
            new_df.loc[trial_i - 1, 'response_hand'] = int(row.Code)#hand_mapper[row.Code]
            new_df.loc[trial_i - 1, 'response_time'] = row.onset - new_df.loc[trial_i - 1, 'onset']
        i += 1
        if i == df.shape[0]:
            break
    new_df.loc[:, 'response_type'] = new_df['response_hand'] == new_df['correct']
    new_df.loc[:, 'response_type'] = ['correct' if x else 'incorrect' for x in new_df['response_type']]
    new_df.loc[:, 'duration'] = new_df['response_time']  # CHECKEN! WEET NIET ZEKER
    new_df = new_df.drop('correct', axis=1)
    miss = new_df.response_hand.isna()
    new_df['response_hand'] = [{1:'left', 2:'right'}[x] if not np.isnan(x) else x for x in new_df['response_hand']]
    new_df.response_type[miss] = 'miss'
    new_df.duration[miss] = 4.900
    new_df['event_type'] = ['emotion' if x in ['fear', 'anger'] else 'control' for x in new_df['emo_match']]
    new_df = new_df.round({'onset': 5, 'duration': 5})
    sub_id = op.basename(f).split('-')[0][2:]
    f_out = op.join(out_dir, f'sub-{sub_id}_task-emorecognition_events.tsv')
    new_df.to_csv(f_out, sep='\t', index=False)
    print(f'{f_out}, {new_df.shape[0]}')
