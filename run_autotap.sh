python eval.py --dataset autotap --logfile autotap_log_06_03_01 &
python eval.py --dataset autotap --logfile autotap_log_06_03_01_norepair --no-repair &
python eval.py --dataset autotap --logfile autotap_log_08_01_01 --train-set-perc=0.8 --test-set-perc=0.1 &
python eval.py --dataset autotap --logfile autotap_log_08_01_01_norepair --train-set-perc=0.8 --test-set-perc=0.1 --no-repair &

for job in `jobs -p`
do
echo $job
    wait $job || let "FAIL+=1"
done

echo $FAIL

if [ "$FAIL" == "0" ];
then
echo "YAY!"
else
echo "FAIL! ($FAIL)"
fi
