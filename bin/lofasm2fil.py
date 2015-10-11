#!/opt/python2.7/bin/python2.7

BASELINES = ['AA', 'BB', 'CC', 'DD', 'AB', 'AC', 'AD', 'BC', 'BD', 'CD']
OUTFILES = {}
HDRLEN = str(110)
HDR_VER = str(1)

if __name__ == "__main__":
    import argparse
    from lofasm import parse_data as pdat
    from lofasm.write import fmt_header_entry as fmt_str
    from lofasm.write import complex2str

    import os
    import struct


    parser = argparse.ArgumentParser(description="LoFASM file extractor")
    parser.add_argument("lofasm_file", type=str,
        help="LoFASM file to extract")
    parser.add_argument('-v','--verbose', dest='v', action='store_true',
        help='print header and progress information')
    parser.add_argument('-s', '--scanfirst', dest='scanfirst',
        action='store_true',
        help='scan .lofasm file prior to extraction. (not recommended)')

    args = parser.parse_args()

    basename = os.path.basename(args.lofasm_file).split('.',1)[0]

    crawler = pdat.LoFASMFileCrawler(args.lofasm_file, scan_file=args.scanfirst)
    crawler.open()

    hdr = crawler.getFileHeader()

    if args.v:
        pdat.print_hdr(hdr)
        print 'starting integration number: ', crawler.getAccReference()
        raw_input('Press enter to continue.')

    TARGET = 'NULL' if hdr[12][1] == '' else hdr[12][1]

    NUM_INTEGRATIONS = crawler.getNumberOfIntegrationsInFile()

    #open output files and write file headers
    if args.v:
        print "Preparing files..."
    try:
        for baseline in BASELINES:
            output_filename = basename + '_' + baseline + '.lofil'
            OUTFILES[baseline] = open(output_filename, 'w')
            OUTFILES[baseline].write(fmt_str(HDRLEN, 10))
            OUTFILES[baseline].write(fmt_str(HDR_VER, 10))
            OUTFILES[baseline].write(fmt_str(hdr[4][1], 10)) #station
            OUTFILES[baseline].write(fmt_str(NUM_INTEGRATIONS, 10))
            OUTFILES[baseline].write(fmt_str(hdr[5][1], 10)) #No. of freq. bins
            OUTFILES[baseline].write(fmt_str(hdr[6][1], 10)) #freq. start
            OUTFILES[baseline].write(fmt_str(hdr[7][1], 10)) #freq. step size
            OUTFILES[baseline].write(fmt_str(hdr[8][1], 10)) #mjd day
            OUTFILES[baseline].write(fmt_str(hdr[9][1], 10)) #mjd milliseconds
            OUTFILES[baseline].write(fmt_str(hdr[10][1], 10)) #integration time
            OUTFILES[baseline].write(fmt_str(TARGET, 10))
    except IOError as err:
        print "Error opening files for writing."
        exit()

    #read and extract data contents
    if args.v:
        for i in range(NUM_INTEGRATIONS):
            print "\n %3i/%i\t%i" % (i, NUM_INTEGRATIONS, crawler.getAccNum())
            for b in BASELINES:
                print b + "..",

                auto_pol = True if b in crawler.autos.keys() else False

                if auto_pol:
                    data = ''
                    for i in range(len(crawler.autos[b])):
                        data += struct.pack('>L',crawler.autos[b][i])
                else:
                    data = complex2str(crawler.cross[b])

                OUTFILES[b].write(data)

            try:
                crawler.forward()
            except EOFError:
                print "reached end of file."
    else:
        for i in range(NUM_INTEGRATIONS):
            for b in BASELINES:
                auto_pol = True if b in crawler.autos.keys() else False

                if auto_pol:
                    data = ''
                    for i in range(len(crawler.autos[b])):
                        data += struct.pack('>L',crawler.autos[b][i])
                else:
                    data = complex2str(crawler.cross[b])

                OUTFILES[b].write(data)

            try:
                crawler.forward()
            except EOFError:
                if args.v:
                    print 'reached end of file'


    if args.v:
        print "closing files..."
    for baseline in BASELINES:
        OUTFILES[b].close()

    if args.v:
        print "done."
