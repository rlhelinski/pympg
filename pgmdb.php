<!-- PHP Gas Mileage DataBase Access Engine, by Ryan Helinski -->
<?php
/*
 * Created on Dec 22, 2007 by Ryan Helinski
 *
 * This is the object which handles the processing of data from 
 * a standard database interface (which contains the data).
 *
 */
 
class pgmdb {
	
	private $function_list = array('summary','print','record','plot','create');
	
	private $functionDesc = array (
		"print" => "Reduced printer-friendly report",
		"summary" => "Full report with derived statistics"
	);
	
	private $configArray = array();
	private $carArray = array();
	private $recordArray = array();
	private $completeArray = array();
	private $globalStats = array();
	
	function readConfigFile($fileName) {
		$newArray = array();
	
		if (count($this->configArray)>0)
			return;
		
		if (($handle = fopen($fileName, "r"))===false)
			echo "Couldn't open ".$fileName;
			
		while(!feof($handle)) {
			if (($buffer = fgets($handle, 4096))!==false)
			{
				$buffer = rtrim ($buffer);
				parse_str($buffer,$newArray);
	//			$configArray[] = $newArray;
				$this->configArray = array_merge($this->configArray,$newArray);
			}
		}
	//	echo "<pre>";
	//	print_r($configArray);
	//	echo "</pre>";
		
	}
	
	function readDataFile($fileName) {
		global $varRoot;
	
		if (count($this->carArray)>0)
			return;
	
		if (($handle = fopen($varRoot.'/'.$fileName, "r"))===false)
			echo "Couldn't open ".$fileName;
	
		while(!feof($handle)) {
			$newRecord = array();
	
			if (($buffer = fgets($handle, 4096))!==false) {
				$buffer = trim($buffer);
				parse_str($buffer,$newRecord);
				# The first record describes the vehicle
				if (count($this->carArray)>0)
					$this->recordArray[] = $newRecord;
				else 
					$this->carArray = $newRecord;
			}
		}
	
	//	echo "<pre>";
	//	print_r($carArray);
	//	print_r($recordArray);
	//	echo "</pre>";
	}
	
	function addRecord ($filename, $record) {
		$newstring = http_build_query($record)."\n";
	
		// Let's make sure the file exists and is writable first.
		if (is_writable($filename)) {
			// Create a backup copy. This is not critical
		 
			if (!copy($filename, $filename."~"))
			    echo "Failed to create backup.\n";
	
			if (!$handle = fopen($filename, 'a')) {
				echo "Cannot open file ($filename)";
				exit;
			}
	
			if (fwrite($handle, $newstring) === FALSE) {
				echo "Cannot write to file ($filename)";
				exit;
			}
		 
			echo "Successfully added record to ".$filename."<br>\n";
				$date = $odo = $gals = $price = $loc = $name = $topd = $note = "";
	
			fclose($handle);
	
		} else {
			echo "The file $filename is not writable";
		}
		
	}
	
	function plotWaveform($wfmFileName) {
		
		global $recordArray;
		
		$descriptorspec = array(
			0 => array("pipe", "r"),  // stdin is a pipe that the child will read from
			1 => array("pipe", "w"),  // stdout is a pipe that the child will write to
			2 => array("file", "var/gnuplot-stderr.txt", "w") // stderr is a file to write to
		);
	
		$cwd = 'var';
		$env = array();
	//	$env = array('some_option' => 'aeiou');
	
	// Note that we've already changed the working directory to the 
	// variable root!
		reset($this->recordArray);
	
		$programme = "reset\n" .
				"set style line 1 lt 1 lw 2 pt 1 ps 0.4\n" .
				"set style line 2 lt 2 lw 2 pt 2 ps 0.4\n" .
				"set style line 3 lt 3 lw 2 pt 3 ps 0.4\n" .
				"set style line 4 lt 4 lw 2 pt 4 ps 0.4\n" .
				"set style line 5 lt 9 lw 5 pt 5 ps 0.4\n" .
				"set style line 6 lt 7 lw 5 pt 6 ps 0.4\n" .
				"set style line 7 lt 8 lw 5 pt 9 ps 0.4\n" .
				"set style line 8 lt 5 lw 5 pt 5 ps 0.4\n" .
				"set style line 9 lt -1 lw 5 pt 7 ps 0.4\n" .
				"set style line 10 lt 0 lw 15 pt 4 ps 0.6\n" .
				"set terminal png small\n" .
				"set size 0.8, 0.8\n" .
				"set autoscale\n" .
				"set origin 0,0\n" .
				"set output 'mpg.png'\n" .
				"set title 'Gas Mileage Statistics (plotted ".date("r").")'\n" .
				"set multiplot\n" .
				"set xlabel 'Date (".$recordArray[1]['date']." - ".$recordArray[count($recordArray)-1]['date'].")' 0,-1\n" .
				"set ylabel 'Miles/Gallon' tc lt 1\n" .
				"set y2label 'Miles/Day' tc lt 2\n" .
				"set xdata time\n" .
				"set timefmt '%s'\n" . # seconds since UNIX Epoch
				"set xtics rotate by 90\n" .
				"set ytics nomirror tc lt 1\n" .
				"set y2tics\n" .
				"plot " .
				"'fuelstat.wfm' using 1:7 title 'Gas Mileage (mi/gal)' " .
				"with lines linestyle 1 axes x1y1, " .
				"'fuelstat.wfm' using 1:6 title 'Average Velocity (mi/day)' " .
				" with lines linestyle 2 axes x1y2 " .
				"\n" .
				"unset multiplot\n" .
				"set output 'fuelcost.png'\n" .
				"set title 'Fuel Cost Statistics (plotted ".date("r").")'\n" .
				"set multiplot\n" .
				"set xlabel 'Date (".$recordArray[1]['date']." - ".$recordArray[count($recordArray)-1]['date'].")' 0,-1\n" .
				"set ylabel 'Dollars/Gallon'\n" .
				"set y2label 'Dollars/Tank'\n" .
				"plot " .
				"'fuelstat.wfm' using 1:4 title 'Fuel Cost (dollars/gal)' " .
				"with lines linestyle 1 axes x1y1," .
				"'fuelstat.wfm' using 1:5 title 'Tank Cost (dollars/tank)' " .
				"with lines linestyle 2 axes x1y2" .
				"\n";
	
	//	echo "<pre>".$programme."</pre>\n";
		
		$process = proc_open($GLOBALS['gnuplot_path'], $descriptorspec, $pipes, $cwd, $env);
	
		if (is_resource($process)) {
			fwrite($pipes[0], $programme);
			fclose($pipes[0]);
		
			echo "<pre>";
			echo stream_get_contents($pipes[1]);
			echo "</pre>\n";
			fclose($pipes[1]);
		
			// It is important that you close any pipes before calling
			// proc_close in order to avoid a deadlock
			$return_value = proc_close($process);
		
			echo "<!-- GNUPLOT returned $return_value -->\n";
		} else {
			echo "Couldn't open pipe to GNUPLOT.";
			exit;
		}
	}
		
	// TODO this function needs to be broken up into FOUR:
	// V first, produce a big table from the input table
	// then create a function to produce the summary table
	// function to produce the print table
	// function to produce the summary and statistics

	// PROCESS RECORDS TO EXPAND DATA
	function process_records () {
		global $varRoot;

	    # We read the file here
		$this->readDataFile($_POST['datafile']);

		# Create references for easy access
		$global_gals = &$this->globalStats['gals'];
		$global_miles = &$this->globalStats['miles'];
		$global_cost = &$this->globalStats['cost'];
		$global_days = &$this->globalStats['days'];
		$max_range = &$this->globalStats['max_range'];
		$min_mpg = &$this->globalStats['min_mpg'];
		$max_mpg = &$this->globalStats['max_mpg'];
		$last_last_odo = &$this->globalStats['last_last_odo'];
		$last_odo = &$this->globalStats['last_odo'];
		$last_date = &$this->globalStats['last_date'];
		$last_gals = &$this->globalStats['last_gals'];
		$last_topd = &$this->globalStats['last_topd'];
		
		# Initialize global stat variables
		$global_gals = 0;
		$global_miles = 0;
		$global_cost = 0;
		$global_days = 0;
		$max_range = 0;
		$max_mpg = 0;
		$min_mpg = INF;
		$records = -1;
		$format = '%m/%d/%Y';

		foreach ($this->recordArray as $record)
		{
			$records++;

			// Update global stats
			if ($records > 0)
			{
				$global_gals = $global_gals + $record['gals'];
				$travelled = $record['odo'] - $last_odo;
			
				if ($max_range < $travelled) 
					$max_range = $travelled;
			
				$mpg = ($record['odo']-$last_odo)/$record['gals'];
				if ($record['topd'][0] == "Y")
				{
					if ($max_mpg < $mpg) $max_mpg = $mpg;
					if ($min_mpg > $mpg) $min_mpg = $mpg;
				}
			
				$time_elap = strtotime($record['date']) - strtotime($last_date);
				$days_elap = round ($time_elap / 86400);
				$global_days = $global_days + $days_elap;
				$global_miles = $global_miles + $travelled; 
				$tank_cost = round($record['price']*$record['gals'],2);
				$global_cost = $global_cost + $tank_cost;
				$miles_per_day = $travelled/$days_elap;
			
			}
			else { 
			  $first_gals = $record['gals'];
			  $travelled = $days_elap = "N/A";
			  $tank_cost = 0;
			  $travelled = 0;
			  $days_elap = 0; 
			  $miles_per_day = 0;
			  $mpg = 0;
			}
	
			// Add array element
			$this->completeArray[] = array (
				"date" => $record['date'],
				"note" => (isset($record['note'])?chop($record['note']):""),
				"days_elap" => $days_elap,
				"odo" => $record['odo'],
				"travelled" => $travelled,
				"gals" => $record['gals'],
				"price" => $record['price'],
				"tank_cost" => $tank_cost,2,
				"miles_per_day" => $miles_per_day,
				"loc" => chop($record['loc']),
				"name" => chop($record['name']),
				"topd" => chop($record['topd']),
				"mpg" => $mpg,
				"mpg_rng_avg" => (
					isset($last_gals) && isset($odo) && isset($last_last_odo) &&  
					($record['gals']+$last_gals > 0) ? 
					($odo-$last_last_odo)/($record['gals']+$last_gals) :
					"N/A" )
			);
		
			// Save Some Data for Next Iteration
			if (isset($last_odo)) $last_last_odo = $last_odo;
			$last_odo = $record['odo'];
			$last_date = $record['date'];
			$last_gals = $record['gals'];
			$last_topd = $record['topd'];
		} // end foreach
		
//		echo "<pre>";
//		print_r($this->completeArray);
//		print_r($this->globalStats);
//		echo "</pre>";
	}
		
	// PRINT DETAILED RECORD CODE
	function print_summary () {
		global $varRoot;
		$records = -1;
		
	    # Call to produce the big table
		$this->process_records();

		echo "<h2>".$this->carArray['make']." ".$this->carArray['model']." Gas Mileage Summary</h2>\n";
		
		$this->print_vehicle_info();

		if (count($this->recordArray)==0) {
			echo "<p>This file contains no records. Please use the 'record'" .
					" function and add at least two fuel records.</p>\n";
			return;
		}
		
		echo "<table class=\"summary\">\n";
		
		// Print Heading Row
		echo "<tr>"
			."<th><b>Date</b></th>"
			."<th align=right><b>Days</b></th>"
			."<th align=right><b>Odo.</b></th>"
			."<th align=right><b>Trvl'd</b></th>"
			."<th align=right><b>Gallons</b></th>"
			."<th align=right><b>$/gal</b></th>"
			."<th align=right><b>cost</b></th>"
			."<th align=right><b>mi/day</b></th>"
			."<th><b>Location</b></th>"
			."<th><b>Station</b></th>"
			."<th><b>Filled?</b></th>"
			."<th align=right><b>Miles/Gal</b></th>"
			.(isset($prnt_rng_avg) ? "<th align=right><b>Rng.Avg.</b></th>" : "")
			."</tr>\n";
		
		foreach ($this->completeArray as $record)
		{
			$records = $records + 1;
	
			if ( $records % 2 == 1 && $_POST['function'] != "print" ) 
				$opts = " class=\"odd\"";
			else
				$opts = "";

			// Print Table Row
			echo "<tr$opts>"
				."<td>".$record['date']
				.(isset($record['note']) && chop($record['note']) != "" ? 
					" <img src=\"fat_pen.png\" alt=\"note\" title=\""
					.chop($record['note'])."\">" : "" )
				."</td>"
				."<td align=right>".$record['days_elap']."</td>"
				."<td align=right>".number_format($record['odo'])."</td>"
				."<td align=right>".$record['travelled']."</td>"
				."<td align=right>".number_format($record['gals'],3)."</td>"
				."<td align=right>".number_format($record['price'],3)."</td>"
				."<td align=right>".number_format($record['tank_cost'],2)."</td>"
				."<td align=right>".number_format($record['miles_per_day'],2)."</td>"
				."<td>".$record['loc']."</td>"
				."<td>".$record['name']."</td>"
				."<td>".$record['topd']."</td>"
				."<td align=right>".number_format($record['mpg'],1)."</td>"
				;
		
			if (isset($prnt_rng_avg))
				echo "<td align=right>".$record['rng_avg']."</td>";

			echo "</tr>\n";
		
		}
	
		// Print units row / table footer
		echo "<tr class=\"units\">"
			."<td>mm/dd/yyyy</td>"
			."<td align=right>days</td>"
			."<td align=right>miles</td>"
			."<td align=right>miles</td>"
			."<td align=right>gallons</td>"
			."<td align=right>USD</td>"
			."<td align=right>USD</td>"
			."<td align=right>miles</td>"
			."<td></td>"
			."<td></td>"
			."<td>yes/no</td>"
			."<td align=right>miles/gal</td>"
			.(isset($prnt_rng_avg) ? "<td align=right>miles/gal</td>" : "")
			."</tr>\n";
	
		echo "</table>\n";
	
		
		
	}


	// PRINT PRINTER-FRIENDLY RECORD CODE
	function print_friendly_records () {
		global $varRoot;
		$records = -1;
		
	    # Call to produce the big table
		$this->process_records();

		echo "<h2>".$this->carArray['make']." ".$this->carArray['model']." Gas Mileage Summary</h2>\n";
		
		$this->print_vehicle_info();

		if (count($this->recordArray)==0) {
			echo "<p>This file contains no records. Please use the 'record'" .
					" function and add at least two fuel records.</p>\n";
			return;
		}
		
		echo "<table border=\"1\">\n";
		
		// Print Heading Row
		echo "<tr>"
			."<th><b>Date</b></th>"
			."<th align=right><b>odo.</b></th>"
			."<th align=right><b>gal</b></th>"
			."<th align=right><b>$/gal</b></th>"
			."<th align=right><b>cost</b></th>"
			."<th><b>Location</b></th>"
			."<th><b>Station</b></th>"
			."<th><b>Fill?</b></th>"
			."<th><b>MPG</b></th>"
			."</tr>\n";
		
		foreach ($this->completeArray as $record)
		{
			// Print Table Row
			echo "<tr>"
				."<td>".$record['date']."</td>"
				."<td align=right>".number_format($record['odo'])."</td>"
				."<td align=right>".number_format($record['gals'],3)."</td>"
				."<td align=right>".number_format($record['price'],3)."</td>"
				."<td align=right>".number_format($record['tank_cost'],2)."</td>"
				."<td>".$record['loc']."</td>"
				."<td>".$record['name']."</td>"
				."<td>".$record['topd']."</td>"
				."<td align=right>".number_format($record['mpg'],1)."</td>"
				;
		
			echo "</tr>\n";
		
			// In the printer-friendly case, print a row with the note on file
			if (isset($record['note']) && chop($record['note']) != "")
				echo "<tr><td></td><td colspan=8><i>"
					.chop($record['note'])."</i></td></tr>";
		
		}
	
		// Print units row / table footer
		echo "<tr class=\"units\">"
			."<td>mm/dd/yyyy</td>"
			."<td align=right>miles</td>"
			."<td align=right>gallons</td>"
			."<td align=right>USD</td>"
			."<td align=right>USD</td>"
			."<td></td>"
			."<td></td>"
			."<td>yes/no</td>"
			."<td>MPG</td>"
			."</tr>\n";
		
	
		echo "</table>\n";
	
		
		
	}


	// PRINT GAS MILEAGE SUMMARY
	function print_stats_summary () {
		# Create references for easy access
		$global_gals = &$this->globalStats['gals'];
		$global_miles = &$this->globalStats['miles'];
		$global_cost = &$this->globalStats['cost'];
		$global_days = &$this->globalStats['days'];
		$max_range = &$this->globalStats['max_range'];
		$min_mpg = &$this->globalStats['min_mpg'];
		$max_mpg = &$this->globalStats['max_mpg'];
		$records = count($this->recordArray);
		$last_last_odo = &$this->globalStats['last_last_odo'];
		$last_odo = &$this->globalStats['last_odo'];
		$last_date = &$this->globalStats['last_date'];
		$last_gals = &$this->globalStats['last_gals'];
		$last_topd = &$this->globalStats['last_topd'];
		
		
		echo "<h2>Gas Mileage Summary</h2>\n";
		
		echo "<table class=\"summary\">\n"
			."<tr><td>Number of Records: </td><td><b>".$records."</b></td><td>records</td></tr>\n"
			."<tr><td>Total Gallons Consumed: </td><td><b>".number_format(round($global_gals))."</b> </td><td>gallons<td></td></tr>\n"
			."<tr><td>Total Miles Travelled: </td><td><b>".number_format($global_miles)."</b> </td><td>miles<td></td></tr>\n"
			."<tr><td>Total Days on Record: </td><td><b>".$global_days."</b> (<b>".round($global_days/365.25,2)."</b>) </td><td>days (years)</td></tr>\n"
			."<tr><td>Total Gas Cost: </td><td><b>$".number_format(round($global_cost))."</b> </td><td>US dollars<td></td></tr>\n"
//			."Latest Gas Mileage: <b>".round(($last_odo-$last_last_odo)/$last_gals,2)."</b> mpg<br>\n"
			."<tr><td>Average Gas Mileage: </td><td><b>".round($global_miles/($global_gals),1)."</b> </td><td>mpg<td></td></tr>\n"
			."</table>\n"
			;
		
	} 
	
	// PRINT GAS MILEAGE STATISTICS
	function print_stats_detailed () {
		# Create references for easy access
		$global_gals = &$this->globalStats['gals'];
		$global_miles = &$this->globalStats['miles'];
		$global_cost = &$this->globalStats['cost'];
		$global_days = &$this->globalStats['days'];
		$max_range = &$this->globalStats['max_range'];
		$min_mpg = &$this->globalStats['min_mpg'];
		$max_mpg = &$this->globalStats['max_mpg'];
		$records = count($this->recordArray);
		$last_last_odo = &$this->globalStats['last_last_odo'];
		$last_odo = &$this->globalStats['last_odo'];
		$last_date = &$this->globalStats['last_date'];
		$last_gals = &$this->globalStats['last_gals'];
		$last_topd = &$this->globalStats['last_topd'];
		
		echo "<h2>Detailed Statistics</h2>\n"
			."Latest Gas Mileage: <b>".round(($last_odo-$last_last_odo)/$last_gals,2)."</b> mpg<br>\n"
			."Minimum Gas Mileage: <b>".round($min_mpg,1)."</b> miles/gallon<br>\n"
			."Average Gas Mileage: <b>".round($global_miles/($global_gals),1)
			."</b> miles/gallon<br>\n"
			."Maxiumum Gas Mileage: <b>".round($max_mpg,1)."</b> miles/gallon<br>\n"
			."Average Days Between Refeuling: <b>".round($global_days/($records-1))."</b> days<br>\n"
			."Average Miles per Day: <b>".round($global_miles/$global_days)
			."</b> miles/day<br>\n"
			."Estimated Miles per Year: <b>"
			.number_format(round(365.25*$global_miles/$global_days,-2),0,'.',',')
			."</b> miles/year<br>\n"
			."Estimated Gallons per Year: <b>".round(365.25*$global_gals/$global_days)."</b> gallons"
			." per day <b>".round($global_gals/$global_days,2)."</b> gallons<br>\n"
			."Estimated Annual Gas Cost: <b>$".round(365.25*$global_cost/$global_days)."</b> US dollars"
			." per day <b>$".round($global_cost/$global_days,2)."</b> US dollars<br>\n"
			// The actual maximum range is the maximum distance between fueling
			// The theoretical maximum range is the range one could drive with 
			// average or maximum gas mileage with 100% of the tank's fuel.
			."Average Range: <b>".round($global_miles/($records))
			."</b> miles<br>\n"
			."Maximum Range: <b>".$max_range."</b> miles<br>\n"
			."Theoretical Range: <b>".round($this->carArray['tanksize']*$global_miles/$global_gals)
			." - ".round($this->carArray['tanksize']*$max_mpg)."</b> miles<br>\n";
			$estimated_mileage = $last_odo+($global_miles/$global_days)*(time()-strtotime($last_date))/86400;
			$days_to_service = round((5000-(fmod($estimated_mileage,5000)))/($global_miles/$global_days),1)
			;

		echo "Estimated Current Milage: <b>"
			.round($estimated_mileage)
	        ."</b> miles<br>\n"
			."Days until next 5k-mile service interval: <b>"
			//.round(($time_to_service*86400-time()+strtotime($date))/86400,2)
			.round($days_to_service)
			."</b> days, on or before <b>"
			.strftime('%m/%d/%Y',$days_to_service*86400+strtotime($last_date))."</b><br>\n"
	      	."</blockquote>\n"
	      	;
	}
	
	// ADD RECORD CODE
	function print_add_record_form () {
		global $configFile;
		global $varRoot;
		
	    $datafile = $varRoot.'/'.$_POST['datafile'];
		$this->readConfigFile($configFile);
	    $index = array_search($_POST['datafile'],$this->configArray['file']);
	    $password_hash = $this->configArray['password'][$index];
	    
	    echo "<h2>Add Refueling Record</h2>\n";
	    echo "<p>Data File Name: <tt><a href=\"".$datafile."\">"
	      .$_POST['datafile']."</a></tt></p>\n";
	
		$record = array();
	
	    //I'm assuming if the date is empty, the user hasn't filled out any of the form. 
	    if (isset($_POST['date']) && $_POST['date'] != "" )
		{
			$record['date'] = date("m/d/Y",strtotime($_POST['date'])); // USA style
			$record['odo'] = number_format($_POST['odo'], 0, '.', '');
			$record['gals'] = number_format($_POST['gals'], 3, '.', '');
			$record['price'] = number_format($_POST['price'], 3, '.', '');
			$record['loc'] = $_POST['loc'];
			$record['name'] = $_POST['name'];
			$record['topd'] = $_POST['topd'];
			$record['note'] = $_POST['note'];
		}
	
		// Attempt to add the record if the date is valid
	    if ( isset($_POST['date']) &&($date_UTC = strtotime($_POST['date']))!==false )
		{
			if (md5($_POST['password']) != rtrim($password_hash))
			{
				echo "Error: Password doesn't match that on file.<br>\n";
				//echo "submitted: ". md5($_POST['password'])." on file: ".$password_hash." ".$index."<br>\n";
				exit;
			}
			
			$this->addRecord($datafile,$record);
	
		} else {
			if (!isset($_POST['date']) || $_POST['date'] == "") 
				echo "Please fill out the form and click submit.<br>\n";
			else if (strtotime($_POST['date']) === false) echo "ERROR: Couldn't understand your date entry.<br>\n";
			else echo "Failed to convert date entry \"".$_POST['date']."\" \"".$date_UTC."\".\n";
		}
	    
	    echo "<form action=\"".$_SERVER['PHP_SELF']."\" method=\"post\">\n"
	      ."<input type=\"hidden\" name=\"function\" value=\"record\" />\n"
	      ."<input type=\"hidden\" name=\"datafile\" value=\"".$_POST['datafile']."\" />\n"
	      ."<pre>\n"
	      ."Password:         <input name=\"password\" type=\"password\" />\n"
	      ."Date:             <input name=\"date\" type=\"text\" value=\"".
	      (isset($record['date'])?$record['date']:"")."\" /> (ex.: 09/07/2006)\n"
	      ."Odometer Reading: <input name=\"odo\" type=\"text\" value=\"".
	      (isset($record['odo'])?$record['odo']:"")."\" /> (ex.: 210512)\n"
	      ."Gallons:          <input name=\"gals\" type=\"text\" value=\"".
	      (isset($record['gals'])?$record['gals']:"")."\"/> (ex.: 10.596)\n"
	      ."Price per Gallon: <input name=\"price\" type=\"text\" value=\"".
	      (isset($record['price'])?$record['price']:"")."\" /> (ex.: 2.199)\n"
	      ."Station:          <input name=\"name\" type=\"text\" value=\"".
	      (isset($record['price'])?$record['name']:"")."\" /> (ex.: Enron)\n"
	      ."Location:         <input name=\"loc\" type=\"text\" value=\"".
	      (isset($record['loc'])?$record['loc']:"")."\" /> (ex.: Clarksville)\n"
	      ."Topped Off:       <select name=\"topd\">\n"
	      ."<option>Yes</option>"
	      ."<option>No</option>"
	      ."</select>\n"
	      ."Notes:\n"
	      ."<textarea name=\"note\" rows=\"2\" cols=\"40\" />"
	      .(isset($record['note'])?$record['note']:"")."</textarea>\n"
	      ."<input type=\"submit\" />"
	      ."<input type=\"reset\" />"
	      ."</pre>"
	      ."</form>";
	
	
	   echo "<p>NOTES: The gas mileage calculation scheme assumes that you top-off each time you fill. If you do not top off, the gas mileage cannot be accurately calculated. Do not use commas in numerical fields. Do not use the ampersand (&) character. The database file (plain text) can be stored for off-line backup or modification purposes via the link above. </p>";
	
		 
	}
	
	// ADD NEW DATA STORAGE FILE CODE
	function print_new_file_form() {
		global $varRoot;
		global $configFile;
		global $pageAddress;

	   echo "<h2>Create New File</h2>\n";
	
	   if ( isset($_POST['filename']) && $_POST['filename'] != "" )
	     {
	       if ( $_POST['password1'] != $_POST['password2'] )
		 {
		   echo "Error: Passwords don't match.<br>\n";
		 }
	
	       if ( ! file_exists($varRoot.'/'.$_POST['filename']) )
		 {
		   $handle = fopen($varRoot.'/'.$_POST['filename'],"x");
		   $headerstring = "year=".$_POST['year']."&make=".$_POST['make']
		   ."&model=".$_POST['model']."&owner=".$_POST['owner']."&tanksize="
		   .$_POST['tanksize']."\n";
	
		   if (fwrite($handle, $headerstring) === FALSE) {
		     echo "Cannot write to file (".$varRoot.'/'.$_POST['filename'].")";
		     exit;
		   }
		   
		   echo "Successfully created data file ".$varRoot.'/'.$_POST['filename']."<br>\n";
		   
		   fclose($handle);
	
			// Create a backup copy. Failure of this is not fatal.
			if (!copy($configFile, $configFile."~"))
				echo "Failed to create backup.\n";
				
			$this->readConfigFile($configFile);
			
			$this->configArray['file'][] = $_POST['filename'];
			$this->configArray['password'][] = $_POST['password1'];
	
			foreach ($this->configArray['file'] as $file)
				$fileArray[] = "file[]=".$file;
			foreach ($this->configArray['password'] as $password)
				$passArray[] = "password[]=".md5($password);
	
			$handle = fopen($configFile,"w");
			if ($handle === false || 
			fwrite($handle, implode("&",$fileArray)."\n")===false ||
			fwrite($handle, implode("&",$passArray)."\n")===false )
			{
				echo "Couldn't add the new file to the list of data files.<br>\n";
				exit;
			}
		     
		   echo "Successfully added new file to list of data files, "
		   	."<a href=\"$pageAddress?datafile=".$_POST['filename']
		   	."&function=record\">Start adding records for this vehicle</a>.<br>\n";
		   fclose($handle);
		   
		   // TODO should switch to 'record' function at this point.
		 }
	       else { echo "File already exists.<br>\n"; }
	     }   
	
	   echo "<p>Create a new (empty) file for storing vehicle gas mileage data. </p>\n"
	     ."<form action=\"".$_SERVER['PHP_SELF']."\" method=\"post\">"
	     ."<input type=\"hidden\" name=\"function\" value=\"create\" />\n"
	     ."<pre>"
	     ."Filename:  <input name=\"filename\" type=\"text\" /> (ex: ryan.txt)\n"
	     ."Password:  <input name=\"password1\" type=\"password\" />\n"
	     ."  repeat:  <input name=\"password2\" type=\"password\" />\n"
	     ."Year:      <input name=\"year\" type=\"text\" /> (ex: 1984)\n"
	     ."Make:      <input name=\"make\" type=\"text\" /> (ex: Honda)\n"
	     ."Model:     <input name=\"model\" type=\"text\" /> (ex: Accord)\n"
	     ."Owner:     <input name=\"owner\" type=\"text\" /> (ex: Ryan Helinski)\n"
	     ."Tank Size: <input name=\"tanksize\" type=\"text\" /> (ex: 12.1)\n"
	     ."<input type=\"submit\" /></pre></form>";
		
	}
	
	# PRINT VEHICLE PROPERTIES
	function print_vehicle_info () {
		global $varRoot;
		
		echo "<p>Data File Name: <tt>";
		if ($_POST['function'] != "print")
			echo "<a href=\"".$varRoot.'/'.$_POST['datafile']."\">".$_POST['datafile']."</a>";
		else 
			echo $_POST['datafile'];
			
		echo "</tt>, Report Format: <b>Data Waveforms</b>"
			."</p>\n";
		
		echo "<p>Year: <b>".$this->carArray['year']."</b>, Make: <b>".$this->carArray['make']
			."</b>, Model: <b>".$this->carArray['model']."</b>, Owner: <b>".$this->carArray['owner']
			."</b>, Tank Size: <b>".$this->carArray['tanksize']."</b></p>\n";
			
	}
	
	// WRITE WAVEFORM AND PLOT CODE
	function display_waveform () {
		global $wfmFileName;
		global $varRoot;
		
		$records = 0;
		
	    if (($wfmHandle = fopen($wfmFileName,"w"))!==FALSE)
	      {
			if (file_exists($varRoot.'/'.$_POST['datafile']))
			  {
//				$this->readDataFile($_POST['datafile']);
				$this->process_records();
								
				echo "<h2>".$this->carArray['make']." ".$this->carArray['model']." Gas Mileage Trends</h2>\n";
				
				$this->print_vehicle_info();

				if (count($this->recordArray)==0) {
					echo "<p>This file contains no records. Please use the 'record'" .
							" function and add at least two fuel records.</p>\n";
					return;
				}
				
			    $heading = "# time\t\tmiles\tgals\t$/gal\t$/tank\tmi/day\tmpg\n";
				  
			    if (fwrite ( $wfmHandle, $heading )===FALSE)
					die ("I/O error.");
				
				echo "<p>Waveform file: <tt><a href=\"".$wfmFileName."\">".$wfmFileName."</a></tt></p>";
		
				foreach ($this->recordArray as $record) 
				{
			      $records = $records + 1;
		
			      if ($records > 1)
				{ 
				  $travelled = $record['odo'] - $last_odo;
				  $mpg = ($record['odo']-$last_odo)/$record['gals'];
				  $time_elap = strtotime($record['date']) - strtotime($last_date);
				  $days_elap = round ($time_elap / 86400);
				  $tank_cost = round($record['price']*$record['gals'],2);
				  
				  // Print Waveforms
				  $fileLine = 
				    round(strtotime($record['date']))."\t"
				    .$travelled."\t"
				    .$record['gals']."\t"
				    .$record['price']."\t"
				    .$tank_cost."\t"
				    .round($travelled/$days_elap,3)."\t"
				    .round($mpg,3)."\n";
		
				  if (fwrite ( $wfmHandle, $fileLine )===FALSE)
				    {
				      echo "I/O error.\n";
				      exit();
				    }
				  
				}
			      else {
				$starttime = strtotime($record['date']);
			      }
		
			      $last_odo = $record['odo'];
			      $last_date = $record['date'];
			    }
		
			    fclose($wfmHandle);
		
				$this->plotWaveform($wfmFileName);
			    
			    echo "<img src=\"var/mpg.png\" alt=\"Gas Mileage\">\n";
	            echo "<img src=\"var/fuelcost.png\" alt=\"Fuel Cost\">\n";
		
			  }
			else {
			  die("Couldn't open ".$_POST['datafile']." for reading.\n");
			}
	
	      }
	    else {
	      die("Couldn't open ".$wfmFileName." for writing.\n");
	    }

	}
		
	// PRINT DATABASE QUERY TOOL CODE
	function print_function_chooser () {
		$this->readConfigFile($GLOBALS['configFile']);
	
		echo "<div class=\"form\">";
		echo "<form action=\"".$GLOBALS['pageAddress']."\" method=\"post\">\n";
		echo "<strong>Database Query: </strong>\n";
	
		if ( count($this->configArray['file']) > 0 )
		{
			echo "Data File: ";
			echo "<select name=\"datafile\">";
			foreach ( $this->configArray['file'] as $dataFile) {
				echo "<option";
				if (isset($_POST['datafile']) && $_POST['datafile']==$dataFile)
					echo " selected";
				echo ">".$dataFile."</option>\n";
	      	}
	      	
			echo "</select>\n";
		}
	
		echo "Function: "
			."<select name=\"function\">\n";
	
		foreach ( $this->function_list as $func ) {
			echo "<option";
			if (isset($_POST['function']) && $_POST['function'] == $func)
				echo " selected";
			echo ">".$func."</option>\n";
		}
	
		echo "</select>\n";
	
		echo "<input type=\"submit\" value=\"Go\" /></form>";
	
		if (isset($_POST['datafile']) && $_POST['datafile'] == "")
			echo "<p>This program is a gas mileage database and analyzer written in PHP. It is self-contained (has a single source code file). It stores data in a simple text file in HTTP-query format. It allows users to add new records, and add new data files for different vehicles. It creates a backup before a new record is added. It also implements password protection for users to add refueling records. </p>\n";

		echo "</div>\n";
		
	}
	
};
?>
