bids_dir=`realpath ..`
out_dir=$bids_dir/derivatives/mriqc
docker run -it --rm -v $bids_dir:/data:ro -v $out_dir:/out poldracklab/mriqc:0.15.0 /data /out group
