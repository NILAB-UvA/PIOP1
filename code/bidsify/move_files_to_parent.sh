subs=`ls -d1 raw/pi0*`
for sub in $subs; do
    mv $sub/*/* $sub/
done
