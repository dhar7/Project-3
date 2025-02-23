python eval.py --dataset ft --logfile ft_log_06_03_01 --context-perc=0.1 &
python eval.py --dataset ft --logfile ft_log_06_03_01_norepair --no-repair --context-perc=0.1 &
python eval.py --dataset ft --logfile ft_log_08_01_01 --train-set-perc=0.8 --test-set-perc=0.1 --context-perc=0.1 &
python eval.py --dataset ft --logfile ft_log_08_01_01_norepair --train-set-perc=0.8 --test-set-perc=0.1 --no-repair --context-perc=0.1 &

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
