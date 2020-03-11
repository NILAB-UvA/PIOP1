set -e

########### UTILS ############
function check_and_copy {
    dwi=$1
    sub_out=$2
    bval=${dwi/nii.gz/bval}
    if [ ! -f ${bval} ]; then
        echo "ERROR: did not find ${bval}."
        exit 1
    fi
    bvec=${dwi/nii.gz/bvec}
    if [ ! -f ${bvec} ]; then
        echo "ERROR: did not find ${bvec}."
        exit 1
    fi
    
    for f in ${dwi} ${bval} ${bvec}; do
        cp ${f} ${sub_out}
    done
}

function concatenate_dwis {
    dwis=$1
    bvecs=$2
    bvals=$3
    sub_out=$4
    sub_base=$(basename ${sub_out})
    fslmerge -t ${sub_out}/${sub_base}_dwi.nii.gz ${dwis[@]}
    paste ${bvecs[@]} > ${sub_out}/${sub_base}_dwi.bvec
    paste ${bvals[@]} > ${sub_out}/${sub_base}_dwi.bval
}
####################################

if [ -z "$1" ]; then
    echo "ERROR: you have to provide a BIDS directory as first argument."
    exit 1
fi

bids_dir=$1

echo "Processing BIDS dir ${bids_dir} ..."

if [ -z "$2" ]; then
    n_cores=1
else
    n_cores=$2
fi

echo "Using ${n_cores} cores ..."
export OMP_NUM_THREADS=${n_cores}

if [ -z "$3" ]; then
    out_dir=${bids_dir}/derivatives/dti
else
    out_dir=$3
fi

echo "Setting output directory to ${out_dir} ..."

if [ ! -d ${out_dir} ]; then
    mkdir -p ${out_dir}
fi

sub_dirs=($(ls -d ${bids_dir}/sub-*))
echo "Found ${#sub_dirs[@]} sub dirs!"

for sub_dir in ${sub_dirs[@]:1:1}; do
    sub_base=$(basename ${sub_dir})
    sub_out=${out_dir}/${sub_base}
    if [ ! -d ${sub_out} ]; then
        mkdir ${sub_out}
    fi

    dwis=($(find ${sub_dir} -maxdepth 2 -name *_dwi.nii.gz -print0 | sort -z | xargs -r0))
    n_dwi=${#dwis[@]}
    if [ ${n_dwi} -eq 0 ]; then
        echo "Did not found DWIs for ${sub_base} ..."
        continue
    elif [ ${n_dwi} = 1 ]; then
        echo "Found exactly one DWI for ${sub_base} ..."
        check_and_copy ${dwis[0]} ${sub_out}
    else
        # Check if the data is complete
        bvals=($(find ${sub_dir} -maxdepth 2 -name *_dwi.bval -print0 | sort -z | xargs -r0))
        bvecs=($(find ${sub_dir} -maxdepth 2 -name *_dwi.bvec -print0 | sort -z | xargs -r0))
        
        for nr in ${#bvals[@]} ${#bvecs[@]}; do
            if [ ! ${nr} -eq ${n_dwi} ]; then
                echo "ERROR: number of DWIs, bvals, and bvecs are not equal."
                exit 1
            fi
        done

        echo "Found ${n_dwi} DWIs for ${sub_base} - going to merge!"
        concatenate_dwis ${dwis} ${bvecs} ${bvals} ${sub_out} 
    fi

    # These files are now concatenated
    dwi=${sub_out}/${sub_base}_dwi.nii.gz
    if [ ! -f ${dwi} ]; then
        echo "ERROR: ${dwi} does not exist."
        exit 1
    fi
    bval=${dwi/nii.gz/bval}
    bvec=${dwi/nii.gz/bvec}

    # Create mask
    mask=${dwi/_dwi/_desc-brain_mask}
    dwi2mask ${dwi} ${mask} -fslgrad ${bvec} ${bval} -force

    # Denoise
    denoised=${dwi/_dwi/_desc-denoised_dwi}
    noise_map=${dwi/_dwi/_noisemap}
    dwidenoise ${dwi} ${denoised} \
        -mask ${mask} \
        -noise ${noise_map} \
        -nthreads 10 \
        -force  

    # dwiprepoc
    preproc_dwi=${dwi/_dwi/_desc-preproc_dwi}
    preproc_bvec=${bvec/_dwi/_desc-preproc_dwi}
    preproc_bval=${bval/_dwi/_desc-preproc_dwi}
    
    qc_dir=${sub_out}/eddy_qc
    if [ ! -d ${qc_dir} ]; then
        mkdir ${qc_dir}
    fi
    dwipreproc ${denoised} ${preproc_dwi} \
        -rpe_none \
        -pe_dir PA \
        -readout_time 0.1 \
        -eddy_options "--slm=linear " \
        -eddyqc_text ${qc_dir} \
        -fslgrad ${bvec} ${bval} \
        -export_grad_fsl ${preproc_bvec} ${preproc_bval} \
        -force

    rm ${denoised}

    # dwi2tensor
    tensor=${preproc_dwi/_desc-preproc_dwi/_desc-dti_tensor}
    dwi2tensor ${preproc_dwi} ${tensor} \
        -mask ${mask} \
        -fslgrad ${preproc_bvec} ${preproc_bval}

    # Remove NaNs???
    fslmaths ${tensor} -nan ${tensor} 

    # tensor2metric
    fa_out=${tensor/_tensor/_FA}
    v1_out=${tensor/_tensor/_V1}
    #tensor2metric -fa ${fa_out} -vector ${v1_out} -num 1 ${tensor}

    fslmaths ${v1_out} -nan ${v1_out} 

    # register to template
    fa_reg_out=${fa_out/_desc-dti_FA.nii.gz/_space-FSLHCP1065_desc-dti_FA}
    fsl_reg ${fa_out} $FSLDIR/data/standard/FSL_HCP1065_FA_1mm.nii.gz ${fa_reg_out} -FA
    
    # Do this separately for all vols in v1
    fslsplit ${v1_out} ${v1_out/.nii.gz/_dir}
    for i in 0 1 2; do
        f_in=${v1_out/.nii.gz/_dir000${i}}
        f_out=${f_in/_desc-dti/_space-FSLHCP1065_desc-dti}
        applywarp -i ${f_in} -o ${f_out} -r $FSLDIR/data/standard/FSL_HCP1065_FA_1mm.nii.gz -w ${fa_reg_out}_warp.nii.gz
    done
    fslmerge -t ${v1_out/_desc-dti/_space-FSLHCP1065_desc-dti} $(ls ${sub_out}/*space-FSLHCP1065*dir*.nii.gz)
    rm ${sub_out}/*dir*.nii.gz
    rm ${sub_out}/*warp*
    rm ${sub_out}/*.mat
    rm ${sub_out}/*.log
done

