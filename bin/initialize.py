#!/opt/python2.7/bin/python2.7

#TODO: add support for coarse delay change
#TODO: add support for ADC histogram plotting.
#TODO: add support for determining ADC input level 

import corr,time,numpy,struct,sys,logging,pylab

katcp_port=7147
######################
def ipStr2Bin(ip):
    ip = ip.split('.')
    ip.reverse()
    dest_ip = 0
    for i in range(len(ip)):
        dest_ip += 2**(i*8) * int(ip[i])
    return dest_ip

######################
def exit_fail():
    print 'FAILURE DETECTED. Log entries:\n',lh.printMessages()
    try:
        fpga.stop()
    except: pass
    raise
    exit()

def exit_clean():
    try:
        fpga.stop()
    except: pass
    exit()


if __name__ == '__main__':
    from optparse import OptionParser

    p = OptionParser()
    p.set_usage('poco_init.py <ROACH_HOSTNAME_or_IP> [options]')
    p.set_description(__doc__)
    p.add_option('-l', '--acc_len', dest='acc_len', type='int',default=(2**28)/1024,
        help='Set the number of vectors to accumulate between dumps. default is (2^28)/1024.')
    p.add_option('-g', '--gain', dest='gain', type='int',default=1000,
        help='Set the digital gain (4bit quantisation scalar). default is 1000.')
    p.add_option('-s', '--skip', dest='skip', action='store_true',
        help='Skip reprogramming the FPGA and configuring EQ.')
    p.add_option('-b', '--bof', dest='boffile', type='str', default='',
        help='Specify the bof file to load')
    p.add_option('--10gbe_dest_port',dest='ten_gbe_dest_port', type='int',default = '60001',
        help='Specify the 10GbE destination port. Default is 60001.')
    p.add_option('--10gbe_dest_ip',dest='ten_gbe_dest_ip', type='str', default = '192.168.4.10',
    help='Specify the 10GbE destination IP address as a string. For example, the default is \'192.168.4.10\'.')
    p.add_option('--list_boffiles', dest='list_boffiles', action='store_true',
        help='If flag is set then print list of available boffiles and exit.')
    opts, args = p.parse_args(sys.argv[1:])

    if args==[]:
        print 'Please specify a ROACH board. \nExiting.'
        exit()
    else:
        roach = args[0]

    if opts.boffile != '':
        boffile = opts.boffile
    else:
        print "No Boffile supplied! Skipping programming!"
        opts.skip = True

try:
    loggers = []
    lh=corr.log_handlers.DebugLogHandler()
    logger = logging.getLogger(roach)
    logger.addHandler(lh)
    logger.setLevel(10)

    print('Connecting to server %s on port %i... '%(roach,katcp_port)),
    fpga = corr.katcp_wrapper.FpgaClient(roach, katcp_port, timeout=10,logger=logger)
    time.sleep(1)

    if fpga.is_connected():
        print 'ok\n'
    else:
        print 'ERROR connecting to server %s on port %i.\n'%(roach,katcp_port)
        exit_fail()
    
    if opts.list_boffiles:
        bof_list = fpga.listbof()
        print bof_list
        exit()
    

    print '------------------------'
    print 'Programming FPGA: %s...'%boffile,
    if not opts.skip:
        fpga.progdev(boffile)
        print 'done'
        time.sleep(2)
    else:
        print 'Skipped.'

    
    print 'Configuring fft_shift...',
    fpga.write_int('fft_shift',(2**32)-1)
    print 'done'

    print 'Configuring accumulation period...',
    fpga.write_int('acc_len',opts.acc_len)
    print 'done'

    print 'Resetting board, software triggering and resetting error counters...',
    fpga.write_int('ctrl',0) 
    fpga.write_int('ctrl',1<<17) #arm
    fpga.write_int('ctrl',0) 
    fpga.write_int('ctrl',1<<18) #software trigger
    fpga.write_int('ctrl',0) 
    fpga.write_int('ctrl',1<<18) #issue a second trigger
    print 'done'

    #EQ SCALING!
    # writes only occur when the addr line changes value. 
    # write blindly - don't bother checking if write was successful. Trust in TCP!
    print 'Setting gains of all channels on all inputs to %i...'%opts.gain,
    fpga.write_int('quant0_gain',opts.gain) #write the same gain for all inputs, all channels
    fpga.write_int('quant1_gain',opts.gain) #write the same gain for all inputs, all channels
    fpga.write_int('quant2_gain',opts.gain) #write the same gain for all inputs, all channels
    fpga.write_int('quant3_gain',opts.gain) #write the same gain for all inputs, all channels
    for chan in range(1024):
        #print '%i...'%chan,
        sys.stdout.flush()
        for input in range(4):
            fpga.blindwrite('quant%i_addr'%input,struct.pack('>I',chan))
    print 'done'

    #set gains
    #for i in range(4):
    #    print "Setting Channel %i gain %i..." %(i,opts.gain),
    #    fpga.write_int('fft'+str(i)+'_gain',opts.gain)
    #    print "done."
    HOST = '192.168.4.21'

    #config for 10GbE interface
    FABRIC_IP = '192.168.4.10'
    FABRIC_IP = ipStr2Bin(FABRIC_IP)
    FABRIC_PORT = 60000
    DEST_PORT = 60001
    DEST_IP = opts.ten_gbe_dest_ip
    DEST_IP = ipStr2Bin(DEST_IP)
    tx_core_name = 'gbe0'       #simulink name
    mac_base = (2<<40) + (2<<32)

    print 'FPGA Registers: ', fpga.listdev()
    time.sleep(.5)
    print "Configuring 10GbE Packet Transmitter..."
    fpga.write_int('tx_dest_ip',DEST_IP)
    fpga.write_int('tx_dest_port',DEST_PORT)
    time.sleep(0.1)
    print "Starting 10GbE core..."
    gbe0_link = bool(fpga.read_int('gbe0_linkup'))
    if gbe0_link != True:
        print "ERROR: No cable is connected to CX-4 Port 0!"
    else:
        print "Cable verified connected to port 0."
    print "core_name %s" % tx_core_name
    print "mac_base: %i" % mac_base
    print "fabric_ip: %i" % FABRIC_IP
    print "mac_base+fabric_ip: %i" % ((int) (mac_base) + (int) (FABRIC_IP))
    print "fabric_port: %i" % FABRIC_PORT
    sys.stdout.flush()
    fpga.tap_start('gbe0',tx_core_name,mac_base+FABRIC_IP,FABRIC_IP,FABRIC_PORT)

    fpga.write_int('gbe_reset',1)
    fpga.write_int('gbe_reset',0)

    print "ok, all set up. Try plotting using poco_plot_autos.py or poco_plot_cross.py"

#    time.sleep(2)
#
#   prev_integration = fpga.read_uint('acc_num')
#   while(1):
#       current_integration = fpga.read_uint('acc_num')
#       diff=current_integration - prev_integration
#       if diff==0:
#           time.sleep(0.01)
#       else:
#           if diff > 1:
#               print 'WARN: We lost %i integrations!'%(current_integration - prev_integration)
#           prev_integration = fpga.read_uint('acc_num')
#           print 'Grabbing integration number %i'%prev_integration
#           
#           if opts.auto:
#               plot_autos()
#           else:
#               plot_cross(opts.cross)
#
except KeyboardInterrupt:
    exit_clean()
except:
    exit_fail()

exit_clean()

