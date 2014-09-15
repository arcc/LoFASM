#!/bin/bash

data_home=$LOFASMDATA_HOME
save_dir=$data_home/snaps

#clear previous copies
if [ -e $save_dir/* ]
    then
        rm $save_dir/*
fi

#get new ADC snaps
/usr/local/bin/get_adc_snaps.py
