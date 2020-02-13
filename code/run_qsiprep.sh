bids_dir=..
out_dir=$bids_dir/derivatives
n_jobs=1

subs=(`ls -d1 $bids_dir/sub-0003`)
# Run subjects one at the time as to avoid memory issues

i=0
for sub in ${subs[@]}; do
    base_sub=`basename $sub`

    if [ -f ${out_dir}/qsiprep/${base_sub}.html ]; then
        echo "${base_sub} already done!"
        continue
    fi	

    label=${base_sub//sub-/}
    echo "Processing $label ..."
    qsiprep-docker $bids_dir $out_dir \
        --image pennbbl/qsiprep:0.7.2 \
        --participant-label $label \
        --nthreads 1 \
        --omp-nthreads 1 \
	--force-syn \
	--output-resolution 2 \
	--output-space T1w \
	--force-spatial-normalization \
	--skip-bids-validation \
	-u 1002:1002 \
	-w ../../qsiprep_work \
        --fs-license-file /usr/local/freesurfer/license.txt &

    i=$(($i + 1))
    if [ $(($i % $n_jobs)) = 0 ]; then
        wait
    fi
done

