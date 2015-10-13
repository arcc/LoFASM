LoFASM Data Download Instructions
=================================

This document explains how to acquire LoFASM data from each of the four LoFASM
stations that are currently running. In each case the instructions will entail
using at least two terminals; one will host the ssh tunnel (a direct link to the
LoFASM Control Computer, labeled LCC_X_ where _X_ is one of [1,2,3,4]) and the
other will be used to actually copy the data to your local machine.



LoFASM I
--------
No info available yet.

LoFASM II
---------
No info available yet.

LoFASM III
----------
1. Obtain ssh passwords for accessing LoFASM III
    * The first password will be hereby referred to as __pw1__ and the second as __pw2__.
2. Open SSH tunnel
    * Open a terminal window and run

        `ssh -N -L 8324:192.33.116.34:22 fjenet@ssh.gb.nrao.edu`
    * Enter ssh password __pw1__ and let that window hang out to the side.
3. Transfer data with Secure Copy (`scp`)
    * Open a *__second__* terminal window while __not__ iterrupting the first window created in the step above.
    * Navigate into the target directory. This is the directory where the LoFASM III data will be stored. For example, if you want to save the data in `/var/data/` then you would run the following:

    `cd /var/data`

    * Now you will use the `scp` command to copy the data over to your current working directory. Let's say (as an example) that the data file you want to copy over is located at `/data1/20151013/20151013_100501.lofasm`. Then the `scp` command that you'll be using would be

    `scp -P 8324 controller@localhost:/data1/20151013/20151013_100501.lofasm .`

    Notice that the port number _8324_ is the same number that was used in step 2 immediately after the _-L_ flag. This is important. Those numbers (be what they may) must be identical. The port number at the end of that parameter (_22_) __must not be changed__ under any circumstances. The flag _-P_ must contain a capital P.

    * Enter password __pw2__ when prompted. The transfer should begin if everything was done correctly.

    Once the `scp` command above finishes you should have the copy of the data available in your current working directory.

4. Perusing the available data files (_optional_)
    If you would simply like to open a shell on the LoFASM III control
    machine (LCC3) and see what data is available then follow these steps.

    * Complete step 2.
    * Open a *__new__* terminal window while __not__ interrupting the window created in step 2.
    * In this new window type

    `ssh -p8324 controller@localhost`

    Then enter the password __pw2__ when prompted.

    The flag _-p_ must contain a lowercase p. Again, the port number (_8324_) must match the port used in step 2.

    * Data files on LCC3 are kept in either `/data1` or `/data2`. Feel free look in these two directories for the data that you need. When you have chosen a file (or set of files) to download then proceed to step 3 to transfer them to your local machine.


LoFASM IV
---------
No info available yet.
