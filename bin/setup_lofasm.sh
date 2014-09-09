#!/bin/bash

#this script sets the environment variables for each LoFASM Station.
#this script feeds off of the already set STATION environment variable.
#if $STATION is not set then this script will fail.

station=$STATION 

case "$station" in
LoFASMI) echo "Setting up LoFASMI environment..."
	;;
LoFASMII) echo "Setting up LoFASMII environment..."
	export LOFASMDATA_HOME=/data1
	export LOFASMDATA_RECENT=$LOFASMDATA_HOME/latest
	;;
LoFASMIII) echo "Setting up LoFASMIII environment..."
	;;
LoFASMIV) echo "Setting up LoFASMIV environment..."
	;;
*) echo "Not a valid LoFASM station!"
	exit
	;;
esac

