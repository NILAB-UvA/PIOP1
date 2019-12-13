set -e

if [ -z "$1" ]; then
    bids_dir=$PWD
else
    bids_dir=$1
fi

if [ ! -d ${bids_dir} ]; then
    echo "ERROR: ${bids_dir} is not an existing dir!"
    exit 1
fi

if [ -z "$2" ]; then
    idx_b0=0
else
    idx_b0=$2
fi

if [ -z "$3" ]; then
    n_cores=1
else
    n_cores=$3
fi

echo "Processing bids-dir ${bids_dir} with ${n_cores} cores!"

out_dir=${bids_dir}/derivatives/dti_fa
if [ ! -d ${out_dir} ]; then
    mkdir -p ${out_dir}
fi

### BETTING ###
tmp_dir=${bids_dir}/tmp
if [ ! -d ${tmp_dir} ]; then
    mkdir ${tmp_dir}
fi

sub_dirs=($(ls -d ${bids_dir}/sub-*))
echo "Found ${#sub_dirs[@]} sub dirs!"

for sub_dir in ${sub_dirs[@]}; do
    sub=$(basename ${sub_dir})
    echo "Running BET and DTIFIT on ${sub}"
    dwis=($(ls ${sub_dir}/dwi/*.nii.gz))
    for dwi in ${dwis[@]}; do 
        basen=$(basename ${dwi})
        b0=${tmp_dir}/${basen/.nii.gz/_b0.nii.gz}
        fslroi ${dwi} ${b0} ${idx_b0} 1
        bet ${b0} ${b0} -m -f 0.2 -n -R
        b0_mask=${b0/.nii.gz/_mask.nii.gz}
        fslmaths ${b0_mask} -kernel sphere 2 -ero -bin ${b0_mask} -odt char
        rm ${b0}
        b0_mask=${b0/.nii.gz/_desc-brain_mask.nii.gz}
        bvec=${dwi/.nii.gz/.bvec}
        bval=${dwi/.nii.gz/.bval}

        s_out=${out_dir}/${sub}
        if [ ! -d ${s_out} ]; then
            mkdir ${s_out}
        fi

        dtifit -k ${dwi} -o ${s_out}/${sub}_space-native -m ${b0/.nii.gz/_mask.nii.gz} -r ${bvec} -b ${bval} 
        mv ${b0/.nii.gz/_mask.nii.gz} ${s_out}/${sub}_space-native_desc-brain_mask.nii.gz

        for mod in L1 L2 L3 MO S0 V1 V2 V3; do
            rm ${s_out}/${sub}_space-native_${mod}.nii.gz
        done

    done
done

### FNIRT ###
sub_dirs_d=($(ls -d ${out_dir}/sub-*))

for sub_dir in ${sub_dirs_d[@]}; do
    sub=$(basename ${sub_dir})
    echo "Registering ${sub}!"
    
    for mod in FA MD; do
        echo "Working on ${mod} image"
        imgs=($(ls ${sub_dir}/*space-native*${mod}.nii.gz))
        for img in ${imgs[@]}; do
            out=${img/native/FSLHCP1065}
            out=${out/.nii.gz/}
            fsl_reg ${img} $FSLDIR/data/standard/FSL_HCP1065_${mod}_1mm.nii.gz ${out} -FA
            rm ${out}_warp.msf
            rm ${out}_warp.nii.gz
            rm ${img/.nii.gz/_to_FSL_HCP1065_${mod}_1mm.log}
        done
    done
done
