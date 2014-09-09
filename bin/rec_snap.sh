#!/bin/bash

# acquire data
ten_gbe_recorder.py -t 15

data_home=$LOFASMDATA_HOME
data_recent=$LOFASMDATA_RECENT

#get latest directory
latest_directory=$( ls -Art $data_home | tail -n 1)

#get latest filename
latest_filename=$( ls -Art $data_home/* | tail -n 1)

#clear last copy
rm $data_recent/*

#copy new file
cp $latest_directory/$latest_filename $data_recent/
