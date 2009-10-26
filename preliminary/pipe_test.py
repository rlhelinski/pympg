#!/usr/bin/python
import subprocess

commands = [
    "set xdata time",
    "set timefmt '%s'",
    "set xtics rotate by 90",
    "set autoscale",
    "unset key",
    "set grid",

    "set title 'Miles per Day'",
    "set xlabel 'Date' 0,-1",
    "set ylabel 'Average Speed [mi/d]'",
    "plot 'matrix.wfm' using 1:8 with lines",
    ]

proc = subprocess.Popen('/usr/bin/gnuplot', shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        )


for cmd in commands:
    if (proc.poll() == 0):
        print "Child terminated."
        break

    print cmd, ":", proc.poll(), proc.stdin.write(cmd + "\n")

proc.wait()

