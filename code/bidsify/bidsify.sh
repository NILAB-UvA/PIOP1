bids_dir=`realpath ..`
raw_dir=`realpath ../../raw`
bidsify -c $raw_dir/config.yml -d $raw_dir -o $bids_dir --docker
