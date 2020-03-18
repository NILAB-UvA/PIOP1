bids_dir=..
work_dir=../../fmriprep_work
out_dir=$bids_dir/derivatives
n_jobs=1

subs=(`ls -d1 $bids_dir/sub-????`)
# Run subjects one at the time as to avoid memory issues

i=0
for sub in ${subs[@]}; do
    base_sub=`basename $sub`

    if [ -f ${out_dir}/fmriprep/${base_sub}.html ]; then
        echo "${base_sub} already done!"
        continue
    fi

    label=${base_sub//sub-/}
    echo "Processing $label ..."
    fmriprep-docker $bids_dir $out_dir \
        --image poldracklab/fmriprep:1.4.1 \
        --participant-label $label \
        --nthreads 5 \
        --omp-nthreads 5 \
        --ignore slicetiming fieldmaps \
        --output-spaces T1w MNI152NLin2009cAsym fsaverage5 \
        --use-syn-sdc \
        --skip-bids-validation \
        -u 1002:1002 \
        -w $work_dir \
        --fs-license-file /usr/local/freesurfer/license.txt \
        --notrack &

    i=$(($i + 1))
    if [ $(($i % $n_jobs)) = 0 ]; then
        wait
    fi
done
wait
