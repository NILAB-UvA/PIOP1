import numpy as np
import nibabel as nib
from glob import glob
from nilearn import image
from tqdm import tqdm

imgs = sorted(glob('../derivatives/dti_fa/sub*/*space-FSL*V1.nii.gz'))
dat = np.zeros((182, 218, 182, 3, len(imgs)))
for i, img in enumerate(tqdm(imgs)):
    dat[:, :, :, :, i] = nib.load(img).get_fdata()
dat = dat.mean(axis=-1)
av_img = nib.Nifti1Image(dat, affine=nib.load(img).affine)
av_img.to_filename('../derivatives/dti_fa/average_V1.nii.gz')

