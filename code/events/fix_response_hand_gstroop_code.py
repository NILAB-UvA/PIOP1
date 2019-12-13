import pandas as pd
from glob import glob

tsvs = sorted(glob('../../sub*/func/*task-gstroop*.tsv'))
for tsv in tsvs:
    df = pd.read_csv(tsv, sep='\t')
    df.loc[df['response_hand'] == 1, 'response_hand'] = 'left'
    df.loc[df['response_hand'] == 2, 'response_hand'] = 'right'
    df.to_csv(tsv, sep='\t', index=False)
