from nitools.firstlevel import Dataset, compute_rfx_contrast
from functools import partial
from joblib import Parallel, delayed


def preproc_df(df, col):
    df.loc[:, 'trial_type'] = df.loc[:, col]
    df = df.loc[~df['trial_type'].isna(), :]
    return df


def _parallel_fit(sub, task, space, acq, hemi, df_filter, con):

    ds = Dataset(bids_dir='../..', sub=sub, n_jobs=1, log_level=30)
    ds.create_taskset(
        task=task,
        space=space,
        acq=acq,
        ses=False,
        hemi=hemi,
        use_gm_mask=True,
        gm_threshold=0.3
    )
    getattr(ds, task).preprocess(
        smoothing_fwhm=5,
        hp_cutoff=0.01,
        conf_vars=None,
        df_filter=df_filter,
        slice_time_ref=0.5,
        add_ricor=True,
        add_motion_outliers=False,
        regress_confounds=False
    )
    getattr(ds, task).glm_detect(
        dm=None,
        hrf_model='glover',
        noise_model='ar1',
        osf=30,
        slice_time_ref=0.5,
        mask=None,
        rf_condition=None
    )
    try:
        img = getattr(ds, task).compute_fxe_contrast(
            contrast_def=con,
            stat_type='t',
            run=None,
            output_type='effect_size'
        )
    except:
        return None
    else:
        return img


if __name__ == '__main__':
    import os
    import json
    import numpy as np
    import pandas as pd
    import os.path as op
    from glob import glob
    from tqdm import tqdm

    INFO = dict(
        faces=dict(
            acq='mb3',
            contrasts=dict(
                negpos=dict(
                    con_def='Joy + Pride - Anger - Contempt',
                    col='trial_type'
                )
            )
        ),
        workingmemory=dict(
            acq='seq',
            contrasts=dict(
                wmload=dict(
                    con_def='active_change + active_nochange - 2 * passive',
                    col='trial_type'
                )
            )
        ),
        emorecognition=dict(
            acq='seq',
            contrasts=dict(
                emocon=dict(
                    con_def='emotion - control',
                    col='trial_type'
                ),
                accuracy=dict(
                    con_def='correct - incorrect',
                    col='response_accuracy'
                )
            )
        ),
        gstroop=dict(
            acq='seq',
            contrasts=dict(
                congruency=dict(
                    con_def='incongruent - congruent',
                    col='trial_type'
                ),
                accuracy=dict(
                    con_def='incorrect - correct',
                    col='response_accuracy'
                )
            )    
        )
    )
    
    for task, info in INFO.items():
        acq = info['acq']
        subs = sorted(
            glob(f"../../derivatives/fmriprep/sub-*/func/sub-*_task-{task}_acq-{acq}_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz")
        )#[:50]

        subs = [op.basename(op.dirname(op.dirname(sub))).split('-')[1] for sub in subs]
        for space, hemi in [('MNI152NLin2009cAsym', ''), ('fsaverage5', 'L'), ('fsaverage5', 'R')]:
            for con_name, con_info in info['contrasts'].items():
                df_filter = partial(preproc_df, col=con_info['col'])
                imgs = Parallel(n_jobs=25)(delayed(_parallel_fit)(
                    sub, task, space, acq, hemi, df_filter, con_info['con_def']
                ) for sub in tqdm(subs, desc=task))

                for sub, img in zip(subs, imgs):
                    if img is not None:
                        d_out = op.join('results', f'sub-{sub}')
                        if not op.isdir(d_out):
                            os.makedirs(d_out, exist_ok=True)

                        f_out = f'sub-{sub}_task-{task}_space-{space}_con-{con_name}'
                        if space == 'fsaverage5':
                            f_out += f'_hemi-{hemi}_cope.npy'
                            np.save(op.join(d_out, f_out), img)
                        else:
                            f_out += '_cope.nii.gz'
                            img.to_filename(op.join(d_out, f_out))

                imgs = [img for img in imgs if img is not None]
                dm = pd.DataFrame({'icept': np.ones(len(imgs))})                
                out = compute_rfx_contrast(
                    imgs=np.vstack(imgs) if space == 'fsaverage5' else imgs,
                    design_matrix=dm,
                    contrast_def='icept',
                    stat_type='t'
                )
                f_out = f'task-{task}_space-{space}_con-{con_name}'
                if space == 'fsaverage5':
                    f_out += f'_hemi-{hemi}_groupT.npy'
                    np.save(op.join('results', f_out), out)
                else:
                    f_out += '_groupT.nii.gz'
                    out.to_filename(op.join('results', f_out))
