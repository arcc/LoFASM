#!/usr/bin/python2.7
"""This is script to check a lofasm files and output a file information file.
"""

if __name__=='__main__':
    import numpy as np
    import argparse
    import os
    from lofasm.file_info import LofasmFileInfo


    parser = argparse.ArgumentParser(description="Lofasm check file tool")
    parser.add_argument("-lf",help="Lofasm data files. ", default="", \
                        type=str, nargs='+')
    parser.add_argument("-info",help="File information file ", default="")
    parser.add_argument("-o",help="Output file name", default="lofasm_files_info.dat")
    parser.add_argument("-d",help="A directory to check", default="", \
                        type=str, nargs='+')
    args = parser.parse_args()
    if args.lf == "" and args.info != "":
        lif = LofasmFileInfo(info_file=args.info)
    elif args.lf != "" and args.info == "":
        lif = LofasmFileInfo(files=args.lf)
    elif args.lf != "" and args.info != "":
        lif = LofasmFileInfo(files=args.lf, info_file=args.info)
    else:
        if args.d == "":
            wd = [os.getcwd(),]
        else:
            wd = args.d
        for dd in wd:
            lfs = [f for f in os.listdir(dd) if os.path.isfile(os.path.join(dd, f))]
            os.chdir(dd)
            # Try to file lofasm default file info file
            if 'lofasm_files_info.dat' in lfs:
                lif = LofasmFileInfo(files=lfs, info_file='lofasm_files_info.dat')
            else:
                lif = LofasmFileInfo(files=lfs)

        lif.info_write(args.o)
