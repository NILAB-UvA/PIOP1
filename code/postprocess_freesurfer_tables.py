import os.path as op
import pandas as pd
from glob import glob


for measure in ['volume', 'thickness', 'area', 'meancurv']:

    for parc in ['aparc', 'aparc.a2009s'][:1]:

        lh = f'../derivatives/fs_stats/data-cortical_type-{parc}_measure-{measure}_hemi-lh.tsv'
        lh = pd.read_csv(lh, sep='\t')
        lh.columns = [f'lh_{col}' if col[:2] != 'lh' else col for col in lh.columns]
        rh = f'../derivatives/fs_stats/data-cortical_type-{parc}_measure-{measure}_hemi-rh.tsv'
        rh = pd.read_csv(rh, sep='\t')
        rh.columns = [f'rh_{col}' if col[:2] != 'rh' else col for col in rh.columns]
        rh = rh.drop(f'rh.{parc}.{measure}', axis=1)
        merged = pd.concat([lh, rh], axis=1).set_index(f'lh.{parc}.{measure}')
        merged.index = merged.index.rename('sub_id')
        merged.to_csv(f'../derivatives/fs_stats/data-cortical_type-{parc}_measure-{measure}_hemi-both.tsv',
                      sep='\t', index=True)
