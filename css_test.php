<?php
/*
 * Created on Dec 30, 2007
 *
 * To change the template for this generated file go to
 * Window - Preferences - PHPeclipse - PHP - Code Templates
 */
?>

<html>
<head>
<title>PHP Gas Mileage Database</title>
<link rel="stylesheet" type="text/css" href="spreadsheet.css">
</head>
<body>

<div id="frame">
<div id="header">
<h1>PHP Gas Mileage Database</h1>
</div>

<div class="form"><form action="/~ryan/workspace/pgmdb/index.php" method="post">
<strong>Database Query: </strong>
Data File: <select name="datafile"><option selected>ryan-matrix.txt</option>
<option>jenn-civic.txt</option>
<option>dogmeat.txt</option>
</select>
Function: <select name="function">
<option selected>summary</option>
<option>print</option>
<option>record</option>
<option>plot</option>
<option>create</option>
</select>
<input type="submit" value="Go" /></form></div>
<hr>

<div id="content">

<div class="notice">This is a notice.</div>

<div class="alert">This is an alert!</div>

<h2>Toyota Matrix XR Gas Mileage Summary</h2>
<p>Data File Name: <tt><a href="var/ryan-matrix.txt">ryan-matrix.txt</a></tt>, Report Format: <b>Data Waveforms</b></p>
<p>Year: <b>2006</b>, Make: <b>Toyota</b>, Model: <b>Matrix XR</b>, Owner: <b>Ryan Helinski</b>, Tank Size: <b>13.2</b></p>
<table class="summary">
<tr><th><b>Date</b></th><th align=right><b>Days</b></th><th align=right><b>Odo.</b></th><th align=right><b>Trvl'd</b></th><th align=right><b>Gallons</b></th><th align=right><b>$/gal</b></th><th align=right><b>cost</b></th><th align=right><b>mi/day</b></th><th><b>Location</b></th><th><b>Station</b></th><th><b>Filled?</b></th><th align=right><b>Miles/Gal</b></th></tr>
<tr><td>06/29/2006</td><td align=right>0</td><td align=right>282</td><td align=right>0</td><td align=right>13.200</td><td align=right>0.000</td><td align=right>0.00</td><td align=right>0.00</td><td>Clarksville</td><td>Antwerpen</td><td>Yes</td><td align=right>0.0</td></tr>
<tr class="odd"><td>07/03/2006</td><td align=right>4</td><td align=right>609</td><td align=right>327</td><td align=right>6.553</td><td align=right>3.059</td><td align=right>20.05</td><td align=right>81.75</td><td>Timonium</td><td>Yorkridge Shell</td><td>No</td><td align=right>49.9</td></tr>
<tr><td>07/09/2006</td><td align=right>6</td><td align=right>780</td><td align=right>171</td><td align=right>8.005</td><td align=right>3.119</td><td align=right>24.97</td><td align=right>28.50</td><td>Timonium</td><td>Shell</td><td>No</td><td align=right>21.4</td></tr>
<tr class="odd"><td>07/15/2006</td><td align=right>6</td><td align=right>1,022</td><td align=right>242</td><td align=right>9.350</td><td align=right>3.059</td><td align=right>28.60</td><td align=right>40.33</td><td>Glen Burnie</td><td>Shell</td><td>Yes</td><td align=right>25.9</td></tr>
<tr class="units"><td>mm/dd/yyyy</td><td align=right>days</td><td align=right>miles</td><td align=right>miles</td><td align=right>gallons</td><td align=right>USD</td><td align=right>USD</td><td align=right>miles</td><td></td><td></td><td>yes/no</td><td align=right>miles/gal</td></tr>
</table>
<h2>Gas Mileage Summary</h2>
<table class="summary">
<tr><td>Number of Records: </td><td><b>55</b></td><td>records</td></tr>
<tr><td>Total Gallons Consumed: </td><td><b>537</b> </td><td>gallons<td></td></tr>
</table>
<h2>Detailed Statistics</h2>
Latest Gas Mileage: <b>29.62</b> mpg<br>
Minimum Gas Mileage: <b>23.6</b> miles/gallon<br>
</div>
<hr>
<div id="footer">PHP Gas Mileage Database, by Ryan Helinski.
Executed in: 0.011 s</div>

</div>

</body>
</html>