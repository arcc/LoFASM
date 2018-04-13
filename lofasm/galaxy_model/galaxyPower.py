#! /usr/bin/env python
# this functions calculates the closest galaxy power based on the
# given time (h) from 0-24, and the station and frequency
import os
def calculatepower(h, station, freq, hor):


#checks so only information is input correctly
#making sure frequency is a float and station is an int
    freq = float(freq)
    station = int(station)
    hor = float(hor)

    assert h >= 0. and h <= 24., "Enter a time between 24.0 and 0.0."

    assert freq <= 85. and freq >= 5, "Enter a frequency between 5.0 and 85.0."

    assert freq % 5 == 0, "Enter a multiple of 5."

    #find the average of the frequency

    filename = "lofasm" + str(station) + "_" + str(freq) + "MHz_" + str(hor) + "deg.dat"
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),filename)
    data = open(filename, 'r')
    #open and read the file based on the station and frequency given

    lines = data.readlines()[1:]
    lines = [line.rstrip('\n').split() for line in lines]

    lsts, pows = zip(*lines)
    lsts = [float(x) for x in lsts]
    pows = [float(x) for x in pows]

    # calculate the closest power by finding the time of the power that is one
    # more and one less of the time given and dividing that by two
    for i in range(len(lsts)):

        if lsts[i] > h:
            p = (pows[i] + pows[i - 1]) / 2.0
            return p

if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("h", type = float, help = "lstHours: between 0.0 and 24.0")
    p.add_argument("st", type = int, choices = [1,3,4], help = "station: 1, 3, 4")
    p.add_argument("fre", type = float, help = "frequency: between 5.0 and 85.0")
    p.add_argument("ho", type = float, help = "horizon cut off")
    p.add_argument("-p", action = "store_true")
    args = p.parse_args()

    r = calculatepower(args.h, args.st, args.fre, args.ho)
    if(args.p):
        print(r)
