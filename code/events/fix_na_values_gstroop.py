import pandas as pd
from glob import glob

files = glob('../sub-0*/func/sub-0*_task-gstroop_acq-seq_events.tsv')
for f in files:
    df = pd.read_csv(f, sep='\t').fillna('n/a').to_csv(f, sep='\t', index=False)

