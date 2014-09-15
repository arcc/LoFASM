#!/bin/bash

data_home=$LOFASMDATA_HOME
save_dir=$data_home/snaps

#clear previous copies
if [ "$(ls -A $save_dir)" ]
then
    echo deleting contents of $save_dir
    rm $save_dir/*
fi
echo 'running python file'
#get new ADC snaps
/usr/local/bin/get_adc_snaps.py
