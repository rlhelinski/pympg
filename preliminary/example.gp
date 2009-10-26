#!/usr/bin/gnuplot


# Always want these
set xdata time
set timefmt '%s'
set xtics rotate by 90

# Might want these
set autoscale
unset key # turn legend off

set title "Miles per Day"
set xlabel 'Date' 0,-1 # set position a little lower
set ylabel 'Average Speed [mi/d]'
plot "matrix.wfm" using 1:8 with lines


