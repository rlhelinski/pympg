set terminal png small #size 640,480
set output './mpg.png'
set size 0.8, 0.8

set style line 1 lt 1 lw 2 pt 1 ps 0.4
set style line 2 lt 2 lw 2 pt 2 ps 0.4
set style line 3 lt 3 lw 2 pt 3 ps 0.4
set style line 4 lt 4 lw 2 pt 4 ps 0.4
set style line 5 lt 9 lw 5 pt 5 ps 0.4
set style line 6 lt 7 lw 5 pt 6 ps 0.4
set style line 7 lt 8 lw 5 pt 9 ps 0.4
set style line 8 lt 5 lw 5 pt 5 ps 0.4
set style line 9 lt -1 lw 5 pt 7 ps 0.4
set style line 10 lt 0 lw 15 pt 4 ps 0.6

set title "Gas Mileage Analysis" #font "Times-Roman,26"

set multiplot
set origin 0,0

set xlabel "Date" #font "Helvetica,20"
set ylabel "Miles/Gallon" #font "Times-Italic,22"
set y2label "Miles/Day" #font "Times-Italic,22"

set autoscale x
set xdata time
set timefmt "%s" # seconds since UNIX Epoch
set xtics rotate by 90

set autoscale y
set ytics nomirror
set autoscale y2
set y2tics

plot \
 "./fuelstat.wfm" using 1:7 title "Gas Mileage (mi/gal)"  with lines linestyle 1 axes x1y1,\
 "./fuelstat.wfm" using 1:6 title "Velocity (mi/day)"  with lines linestyle 2 axes x1y2

unset multiplot
set terminal png small #size 640,480
set output './fuelcost.png'

set title "Fuel Cost Statistics" #font "Times-Roman,26"

set multiplot

set xlabel "Date" #font "Helvetica,20"
set ylabel "Dollars / Gallon" #font "Times-Italic,22"
set y2label "Dollars / Tank" #font "Times-Italic,22"

plot \
 "./fuelstat.wfm" using 1:4 title "Fuel Cost ($/gal)"  with lines linestyle 1 axes x1y1,\
 "./fuelstat.wfm" using 1:5 title "Tank Cost ($/tank)"  with lines linestyle 2 axes x1y2
