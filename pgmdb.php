<!-- PHP Gas Mileage Computation Engine, by Ryan Helinski -->
<?php
/*
 * Created on Dec 22, 2007 by Ryan Helinski
 *
 * This is the object which handles the processing of data from 
 * a standard database interface (which contains the data), and
 * rendering HTML code for the controls and output. 
 *
 */
include_once('stdlib.php');
include_once('filedb.php');
 
class pgmdb {
	
	var $function_list = array('summary','record','plot','print','edit','create','import','export');
	var $export_types = array('csv');
	var $import_types = array('csv');
	
	
	var $editFunctions = array (
		"edit" => "Edit Info",
		"rename" => "Rename",
		"records" => "Edit Records"
	);
	
	var $functionDesc = array (
		"print" => "Reduced printer-friendly report",
		"summary" => "Full report with derived statistics"
	);
	
	// this data should actually stay here
	//var $configArray = array();
	var $carArray = array();
	var $recordArray = array();
	var $completeArray = array();
	var $globalStats = array();
	
	var $database;
	
	function pgmdb() {
		$this->database = new filedb();
	}
	
	// TODO move the gnuplot-controlling code to a different class
	// TODO change name to compile rather than plot
	// DEFER
	function plotWaveform($wfmFileName) {
		global $var_root;
		global $gnuplot_path;
		global $recordArray;
		
		// Check that the GNUPLOT path is correct
		echo "<!--\n";
		$output = system($gnuplot_path." --version", $retval);
		echo " -->\n";

		if ($retval != 0)
			die("GNUPLOT path variable incorrect(".$gnuplot_path."), GNUPLOT not found.");

		$descriptorspec = array(
			0 => array("pipe", "r"),  // stdin is a pipe that the child will read from
			1 => array("pipe", "w"),  // stdout is a pipe that the child will write to
			2 => array("pipe", "w") // stderr is a file to write to
		);
	
		$cwd = $var_root;
		$env = array();
		
		$recordArray = $this->database->recordArray;
	
		// Note that we've already changed the working directory to the variable root!
		//reset($recordArray);
		
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
			"set title 'Gas Mileage Statistics (plotted ".date("m/d/Y").")'\n" .
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
			"set title 'Fuel Cost Statistics (plotted ".date("m/d/Y").")'\n" .
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

		$process = proc_open($gnuplot_path, $descriptorspec, $pipes, $cwd, $env);
		
		if (is_resource($process)) {
			fwrite($pipes[0], $programme);
			fclose($pipes[0]);
		
			echo "<!-- STDOUT\n"
				. stream_get_contents($pipes[1])
				. "\nSTDERR\n"
				. stream_get_contents($pipes[2])
				. "\n";
			fclose($pipes[1]);
			fclose($pipes[2]);
			
			// It is important that you close any pipes before calling
			// proc_close in order to avoid a deadlock
			$return_value = proc_close($process);
		
			echo "GNUPLOT returned $return_value\n-->\n";
		} else {
			die( "Couldn't open pipe to GNUPLOT (".$gnuplot_path.").");
		}
	}

	// PROCESS RECORDS TO EXPAND DATA
	function process_records () {
		global $var_root;

	    # We read the file here
		$this->database->getVehicle($_POST['datafile']);
		
		$recordArray = &$this->database->recordArray;
		
		if (!isset($recordArray) || count($recordArray) == 0) {
			return false;
		}

		# Initialize global stat variables
		$this->globalStats['gals'] = 0;
		$this->globalStats['miles'] = 0;
		$this->globalStats['cost'] = 0;
		$this->globalStats['days'] = 0;
		$this->globalStats['max_range'] = 0;
		$this->globalStats['max_mpg'] = 0;
		$this->globalStats['min_mpg'] = INF;
		$records = -1;
		$format = '%m/%d/%Y';

		foreach ($recordArray as $record)
		{
			$records++;

			// Update global stats
			if ($records > 0)
			{
				$this->globalStats['gals'] = $this->globalStats['gals'] + $record['gals'];
				$travelled = $record['odo'] - $this->globalStats['last_odo'];
			
				if ($this->globalStats['max_range'] < $travelled) 
					$this->globalStats['max_range'] = $travelled;
			
				$mpg = ($record['odo']-$this->globalStats['last_odo'])/$record['gals'];
				if ($record['topd'][0] == "Y")
				{
					if ($this->globalStats['max_mpg'] < $mpg) $this->globalStats['max_mpg'] = $mpg;
					if ($this->globalStats['min_mpg'] > $mpg) $this->globalStats['min_mpg'] = $mpg;
				}
			
				$time_elap = strtotime($record['date']) - strtotime($this->globalStats['last_date']);
				$days_elap = round ($time_elap / 86400);
				$this->globalStats['days'] = $this->globalStats['days'] + $days_elap;
				$this->globalStats['miles'] = $this->globalStats['miles'] + $travelled; 
				$tank_cost = round($record['price']*$record['gals'],2);
				$this->globalStats['cost'] = $this->globalStats['cost'] + $tank_cost;
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
					isset($this->globalStats['last_gals']) && isset($odo) && isset($this->globalStats['last_last_odo']) &&  
					($record['gals']+$this->globalStats['last_gals'] > 0) ? 
					($odo-$this->globalStats['last_last_odo'])/($record['gals']+$this->globalStats['last_gals']) :
					"N/A" )
			);
		
			// Save Some Data for Next Iteration
			if (isset($this->globalStats['last_odo'])) $this->globalStats['last_last_odo'] = $this->globalStats['last_odo'];
			$this->globalStats['last_odo'] = $record['odo'];
			$this->globalStats['last_date'] = $record['date'];
			$this->globalStats['last_gals'] = $record['gals'];
			$this->globalStats['last_topd'] = $record['topd'];
		} // end foreach
		
//		echo "<pre>";
//		print_r($this->completeArray);
//		print_r($this->globalStats);
//		echo "</pre>";

		# Full table is now available at $this->completeArray 

	}
		
	// PRINT DETAILED RECORD CODE
	function print_summary () {
		global $var_root;
		$records = -1;

	    # Call to produce the big table
		$this->process_records();
		
		$carArray = &$this->database->carArray;
		$recordArray = &$this->database->recordArray;
		
//var_dump($this->database->vehicleArray);
		echo "<h1>".$carArray['make']." ".$carArray['model']." Gas Mileage Records</h1>\n";

		
		$this->print_vehicle_info();

		if (count($recordArray)==0) {
			echo "<p>This file contains no records. Please use the 'record'" .
					" function and add at least two fuel records.</p>\n";
			return false;
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

			# TODO make sure that addslashes() is the func used to add
			# strings to the file, since I'm using stripslashes() here!

			// Print Table Row
			echo "<tr$opts>"
				."<td>"
				.(isset($record['note']) && chop($record['note']) != "" ? 
					"<a href='#' class='info'>".$record['date']
					."<span>".stripslashes(chop($record['note']))."</span>" 
					: $record['date'] )
				."</td>"
				."<td align=right>".$record['days_elap']."</td>"
				."<td align=right>".number_format($record['odo'])."</td>"
				."<td align=right>".$record['travelled']."</td>"
				."<td align=right>".number_format($record['gals'],3)."</td>"
				."<td align=right>".number_format($record['price'],3)."</td>"
				."<td align=right>".number_format($record['tank_cost'],2)."</td>"
				."<td align=right>".number_format($record['miles_per_day'],2)."</td>"
				."<td>".stripslashes($record['loc'])."</td>"
				."<td>".stripslashes($record['name'])."</td>"
				."<td>".$record['topd']."</td>"
				."<td align=right>"
				.(strtolower($record['topd'])=="yes"?"":"(")
				.number_format($record['mpg'],1)
				.(strtolower($record['topd'])=="yes"?"":")")
				."</td>"
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
	
		
		
		return true;
	}


	// PRINT PRINTER-FRIENDLY RECORD CODE
	function print_friendly_records () {
		global $var_root;
		$records = -1;
		$carArray = &$this->database->carArray;
		$recordArray = &$this->database->recordArray;
		
	    # Call to produce the big table
		$this->process_records();
		
		echo "<h2>".$carArray['make']." ".$carArray['model']." Gas Mileage Summary</h2>\n";
		
		$this->print_vehicle_info();

		if (count($recordArray)==0) {
			echo "<p>This file contains no records. Please use the 'record'" .
					" function and add at least two fuel records.</p>\n";
			return false;
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
		$carArray = &$this->database->carArray;
		$recordArray = &$this->database->recordArray;
		
		echo "<h2>Gas Mileage Summary</h2>\n";
		
		echo "<table class=\"summary\">\n"
			."<tr><td>Number of Records: </td><td><b>".count($recordArray)."</b></td><td>records</td></tr>\n"
			."<tr><td>Total Gallons Consumed: </td><td><b>".number_format(round($this->globalStats['gals']))."</b> </td><td>gallons<td></td></tr>\n"
			."<tr><td>Total Miles Travelled: </td><td><b>".number_format($this->globalStats['miles'])."</b> </td><td>miles<td></td></tr>\n"
			."<tr><td>Total Days on Record: </td><td><b>".$this->globalStats['days']."</b> (<b>".round($this->globalStats['days']/365.25,2)."</b>) </td><td>days (years)</td></tr>\n"
			."<tr><td>Total Gas Cost: </td><td><b>$".number_format(round($this->globalStats['cost']))."</b> </td><td>US dollars<td></td></tr>\n"
//			."Latest Gas Mileage: <b>".round(($this->globalStats['last_odo']-$this->globalStats['last_last_odo'])/$this->globalStats['last_gals'],2)."</b> mpg<br>\n"
			."<tr><td>Average Gas Mileage: </td><td><b>".round($this->globalStats['miles']/($this->globalStats['gals']),1)."</b> </td><td>mpg<td></td></tr>\n"
			."</table>\n"
			;
//			$estimated_mileage = $this->globalStats['last_odo']+($this->globalStats['miles']/$this->globalStats['days'])*(time()-strtotime($this->globalStats['last_date']))/86400;
//			$days_to_service = round((5000-(fmod($estimated_mileage,5000)))/($this->globalStats['miles']/$this->globalStats['days']),1)
//			;
//
//		echo "Estimated Current Milage: <b>"
//			.round($estimated_mileage)
//	        ."</b> miles<br>\n"
//			."Days until next 5k-mile service interval: <b>"
//			//.round(($time_to_service*86400-time()+strtotime($date))/86400,2)
//			.round($days_to_service)
//			."</b> days, on or before <b>"
//			.strftime('%m/%d/%Y',$days_to_service*86400+strtotime($this->globalStats['last_date']))."</b><br>\n"
//	      	;
		return true;
	} 
	
	// PRINT GAS MILEAGE STATISTICS
	function print_stats_detailed () {
		# Create references for easy access
		$carArray = &$this->database->carArray;
		$recordArray = &$this->database->recordArray;
		
		echo "<h2>Detailed Statistics</h2>\n";
		
		echo "<table>\n<tr>\n<th></th><th>Minimum</th><th>Average</th><th>Maximum</th><th>Latest</th><th>Units</th></tr>\n";
		
		$stats = array(
			// name, min, avg, max, latest, units
			array("Gas Mileage", 
				round($this->globalStats['min_mpg'],1), 
				round($this->globalStats['miles']/($this->globalStats['gals'])),
				round($this->globalStats['max_mpg'],1),
				round(($this->globalStats['last_odo']-$this->globalStats['last_last_odo'])/$this->globalStats['last_gals'],2), 
				"mi/gal"),
			array(
				"Days Between",
				"",
				round($this->globalStats['days']/(count($recordArray)-1)),
				"",
				"",
				"days"
				),
			array(
				"Miles/Day",
				"",
				round($this->globalStats['miles']/$this->globalStats['days']),
				"",
				"",
				"mi"
				),
			array(
				"Miles/Year",
				"",
				number_format(round(365.25*$this->globalStats['miles']/$this->globalStats['days'],-2),0,'.',','),
				"",
				"",
				"mi"
				),
			array(
				"Gallons/Year",
				"",
				round(365.25*$this->globalStats['gals']/$this->globalStats['days']),
				"",
				"",
				"gal/year"
				),
			array(
				"Cost/Day",
				"",
				round($this->globalStats['cost']/$this->globalStats['days'],2),
				"",
				"",
				"USD/day"
				),
			array(
				"Cost/Year",
				"",
				round(365.25*$this->globalStats['cost']/$this->globalStats['days']),
				"",
				"",
				"USD/day"
				),
			array(
				"Tank Range",
				"",
				round($this->globalStats['miles']/(count($recordArray))),
				$this->globalStats['max_range'],
				"",
				"mi"
				)
		);
//			."Average Days Between Refeuling: <b>".round($this->globalStats['days']/(count($recordArray)-1))."</b> days<br>\n"
//			."Average Miles per Day: <b>".round($this->globalStats['miles']/$this->globalStats['days'])
//			."</b> miles/day<br>\n"
//			."Estimated Miles per Year: <b>"
//			.
//			."</b> miles/year<br>\n"
//			."Estimated Gallons per Year: <b>".round(365.25*$this->globalStats['gals']/$this->globalStats['days'])."</b> gallons"
//			." per day <b>".round($this->globalStats['gals']/$this->globalStats['days'],2)."</b> gallons<br>\n"
//			."Estimated Annual Gas Cost: <b>$".round(365.25*$this->globalStats['cost']/$this->globalStats['days'])."</b> US dollars"
//			." per day <b>$".round($this->globalStats['cost']/$this->globalStats['days'],2)."</b> US dollars<br>\n"
//			// The actual maximum range is the maximum distance between fueling
//			// The theoretical maximum range is the range one could drive with 
//			// average or maximum gas mileage with 100% of the tank's fuel.
//			."Average Range: <b>".round($this->globalStats['miles']/(count($recordArray)))
//			."</b> miles<br>\n"
//			."Maximum Range: <b>".."</b> miles<br>\n"
//			."Theoretical Range: <b>".round($carArray['tanksize']*$this->globalStats['miles']/$this->globalStats['gals'])
//			." - ".round($carArray['tanksize']*$this->globalStats['max_mpg'])."</b> miles<br>\n";

		foreach($stats as $stat) {
			echo "<tr><th>".$stat[0]."</th><td>".$stat[1]."</td><td>".$stat[2]."</td><td>".$stat[3]."</td><td>".$stat[4]."</td><td>".$stat[5]."</td></tr>\n";
		}
		
		echo "</table>\n";
	}
	
	// MODIFY VEHICLE CODE
	function print_edit_form() {
		global $filedb_config_file;
		global $var_root;
		
		// Stuff we need in both steps
	    $datafile = $var_root.'/'.$_POST['datafile'];
		$this->database->getConfig();
		
		$password_hash = $this->database->getPassHash($_POST['datafile']);
	    
	    $this->database->getVehicle($_POST['datafile']);
	    
	    echo "<h2>Modify Vehicle</h2>\n";
	    echo "<p>Data File Name: <tt><a href=\"".$datafile."\">"
	      .$_POST['datafile']."</a></tt></p>\n";
	
		$record = array();
	
/*	    //I'm assuming if the date is empty, the user hasn't filled out any of the form. 
	    if ( isset($_POST['date']) && $_POST['date'] != "" )
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
*/	

		if ( isset($_POST['step']) && $_POST['step'] == "save" ) {
			// Update data if password is valid
		    if ( md5(rtrim($_POST['password'])) == rtrim($password_hash) ) {
				if ( $_POST['subfunction'] == "edit") {
					// change array
					foreach ($_POST as $key => $val) {
						if (preg_match("/^new_(.+)/",$key,$matches)) {
							var_dump($matches);
							$this->database->carArray[$matches[1]] = $val;
						}
					}
					// save array
					$this->database->saveVehicle($_POST['datafile']);
				} elseif ( $_POST['subfunction'] == "rename") {
					// rename the file
					$this->database->renameVehicle($_POST['datafile'], $_POST['newname']);
											
				} else {
					echo "Subfunction not recognized.\n";
				}
				
				echo "<div class='notice'>Successfully updated <tt>".$_POST['datafile']."</tt></div>\n";
				
			} else {
				echo "<div class='alert'>Error: Password does not match that on file.</div>\n";
				// don't print this unless you need to
				//echo "submitted: ". md5($_POST['password'])." on file: ".$password_hash." ".$index."<br>\n";
			}
		}

		// Print the different edit forms
		elseif ( isset($_POST['subfunction']) ) {
			if ($_POST['subfunction'] == "edit") {
			    echo "<form action=\"".$_SERVER['PHP_SELF']."\" method=\"post\">\n"
			      ."<input type=\"hidden\" name=\"step\" value=\"save\" >\n"
			      ."<input type=\"hidden\" name=\"subfunction\" value=\"edit\" >\n"
			      ."<input type=\"hidden\" name=\"function\" value=\"edit\">\n"
			      ."<input type=\"hidden\" name=\"datafile\" value=\"".$_POST['datafile']."\" >\n"
			      ."<table>\n";
			      
			    echo "<tr><td>Password:</td><td><input type='password' name='password'></td></tr>\n";
			      
			    foreach ($this->database->carArray as $field => $value) {
			    	echo "<tr><td>$field</td><td><input type=\"text\" name=\"new_$field\" value=\"$value\"></td></tr>\n";
			    }
			    
			    echo "</table>\n<hr>\n";		
				echo "<input type=\"submit\">\n"
			      ."</pre>\n"
			      ."</form>\n";
				
			} elseif ($_POST['subfunction'] == "rename") {
			    echo "<form action=\"".$_SERVER['PHP_SELF']."\" method=\"post\">\n"
			      ."<input type=\"hidden\" name=\"step\" value=\"save\" >\n"
			      ."<input type=\"hidden\" name=\"subfunction\" value=\"rename\" >\n"
			      ."<input type=\"hidden\" name=\"function\" value=\"edit\">\n"
			      ."<input type=\"hidden\" name=\"datafile\" value=\"".$_POST['datafile']."\" >\n"
			      ."<table>\n";
			      
			    echo "<tr><td>Password:</td><td><input type='password' name='password'></td></tr>\n";
			      
			    echo "<tr><td>New name:</td><td><input type='text' name='newname' value='".$_POST['datafile']."'></td></tr>\n";
			    
			    echo "</table>\n<hr>\n";		
				echo "<input type=\"submit\">\n"
			      ."</pre>\n"
			      ."</form>\n";
			}
		} else {
			// Print a form to choose subfunction
		    echo "<form action=\"".$_SERVER['PHP_SELF']."\" method=\"post\">\n"
		      ."<input type=\"hidden\" name=\"step\" value=\"input\">\n"
		      ."<input type=\"hidden\" name=\"function\" value=\"edit\">\n"
		      ."<input type=\"hidden\" name=\"datafile\" value=\"".$_POST['datafile']."\" >\n"
		      ;
			
			echo "<select name=\"subfunction\">\n";
	
			foreach ( $this->editFunctions as $func => $text ) {
				echo "<option value=\"$func\">".$text."</option>\n";
			}
		
			echo "</select>\n";
		    
			echo "<input type=\"submit\">\n"
		      ."</pre>\n"
		      ."</form>\n";
		}

		// This part should be optional
/*		echo "<table>\n";
	    
	    foreach ($this->database->recordArray as $index => $record) {
	    	echo "<tr>\n";
	    	
	    	foreach ($record as $field => $value) {
	    		echo "<td><input type='text' name='record:$index:$field' value='$value'></td>\n";
	    	}
	    	
	    	echo "</tr>\n";
	    }
	    
		echo "</table>\n";*/

	
	
	}
	
	
	// ADD RECORD CODE
	function print_add_record_form () {
		global $filedb_config_file;
		global $var_root;
		
	    $datafile = $var_root.'/'.$_POST['datafile'];
		$this->database->getConfig();

		$password_hash = $this->database->getPassHash($_POST['datafile']);
	    
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
			if (md5(rtrim($_POST['password'])) != rtrim($password_hash))
			{
				echo "<div class='alert'>Error: Password does not match that on file.</div>\n";
				// don't print this unless you need to
				echo "submitted: ". md5($_POST['password'])." on file: ".$password_hash." ".$index."<br>\n";
				
			} else {
				$this->database->addRecord($_POST['datafile'],$record);
		        echo "<div class='notice'>Successfully added record to <tt>".$_POST['datafile']."</tt></div>\n";
        
/*				# Empty the fields to be printed in the form (not working)
				$date = $odo = $gals = $price = $loc = $name = $topd = $note = "";
*/				
		        $this->process_records();
		        
		        echo "<P>New miles/gallon estimate: <b>"
		                .number_format($this->completeArray[count($this->completeArray)-1]['mpg'],2)
		                ." mpg</b></P>\n";
			}
	
		} else {
			if (!isset($_POST['date']) || $_POST['date'] == "") 
				echo "<div class='notice'>Please fill out the form completely and click submit.</div>\n";
			else if (strtotime($_POST['date']) === false) 
				echo "<div class='alert'>ERROR: Couldn't understand your date entry \"".$_POST['date']."\" \"".$date_UTC."\".</div>\n";
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
	// TODO this funcion needs to be split up 
	function print_new_file_form() {
		global $var_root;
		global $filedb_config_file; // $configFile;
		global $pageAddress;

	   echo "<h2>Create New File</h2>\n";
	
	   if ( isset($_POST['filename']) && $_POST['filename'] != "" )
	     {
	       if ( $_POST['password1'] != $_POST['password2'] )
			 {
			   echo "<div class='alert'>Error: Password repetition does not match.</div>\n";
			 // should not continue
			 }
			else 
			# begin file-oriented stuff
	       $this->database->newVehicle($_POST['filename'], $_POST);
	       
	       print_alert("New file ".$_POST['filename']." created. Use the menu above to continue.");
	     }   
	
	   echo "<p>Create a new (empty) file for storing vehicle gas mileage data. </p>\n"
	     ."<form action=\"".$_SERVER['PHP_SELF']."\" method=\"post\">"
	     ."<input type=\"hidden\" name=\"function\" value=\"create\" />\n"
	     ."<pre>"
	     ."Filename:  <input name=\"filename\" type=\"text\" /> (ex: F-J Cruiser)\n"
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
	# can't link to the file for compatibility
	function print_vehicle_info () {
		global $var_root;
		$carArray = &$this->database->carArray;
		
		echo "<p>Data File Name: <tt>";
		#if ($_POST['function'] != "print")
		#	echo "<a href=\"".$var_root.'/'.$_POST['datafile']."\">".$_POST['datafile']."</a>";
		#else 
		echo $_POST['datafile'];
			
		echo "</tt>, Report Format: <b>Data Waveforms</b>"
			."</p>\n";
		
		echo "<p>Year: <b>".$carArray['year']."</b>, Make: <b>".$carArray['make']
			."</b>, Model: <b>".$carArray['model']."</b>, Owner: <b>".$carArray['owner']
			."</b>, Tank Size: <b>".$carArray['tanksize']."</b></p>\n";
			
	}
	
	// WRITE WAVEFORM AND PLOT CODE
	function display_waveform () {
		global $wfm_file;
		global $var_root;
		
		$carArray = &$this->database->carArray;
		$recordArray = &$this->database->recordArray;
		
		$records = 0;
				
	    if (($wfmHandle = fopen($wfm_file,"w"))!==FALSE)
	      {
			if (file_exists($var_root.'/'.$_POST['datafile']))
			  {
//				$this->readDataFile($_POST['datafile']);
				$this->process_records();
								
				echo "<h2>".$carArray['make']." ".$carArray['model']." Gas Mileage Trends</h2>\n";
				
				$this->print_vehicle_info();

				if (count($recordArray)==0) {
					echo "<div class='notice'>This file contains no records. Please use the 'record'" .
						" function and add at least two fuel records.</div>\n";
					return;
				}
				
			    $heading = "# time\t\tmiles\tgals\t$/gal\t$/tank\tmi/day\tmpg\n";
				  
			    if (fwrite ( $wfmHandle, $heading )===FALSE) {
			    	//debug_print_backtrace();
			    	debug_print_backtrace();
			    	die ("I/O error.");
			    }
				
				echo "<p>Waveform file: <tt><a href=\"".$wfm_file."\">".$wfm_file."</a></tt></p>\n";
		
				foreach ($this->completeArray as $record) 
				{
			      $records = $records + 1;
		
			      if ($records > 1)
					{
					  // Print Waveforms
					  $fileLine = 
					    round(strtotime($record['date']))."\t"
					    .$record['travelled']."\t"
					    .$record['gals']."\t"
					    .$record['price']."\t"
					    .$record['tank_cost']."\t"
					    .round($record['travelled']/$record['days_elap'],3)."\t"
					    .round($record['mpg'],3)."\n";
			
					  if (fwrite ( $wfmHandle, $fileLine )===FALSE)
					    {
					      echo "I/O error.\n";
					      exit();
					    }
					  
					}
			      else {
					$starttime = strtotime($record['date']);
			      }
		
			    }
		
			    fclose($wfmHandle);
		
				$this->plotWaveform($wfm_file);
			    		
			  }
			else {
			  echo "Couldn't open ".$_POST['datafile']." for reading.\n";
			}
	
	      }
	    else {
	      echo "Couldn't open '".$wfm_file."' for writing.\n";
	    }

	    echo "<img src=\"var/mpg.png\" alt=\"Gas Mileage\">\n";
        echo "<img src=\"var/fuelcost.png\" alt=\"Fuel Cost\">\n";

	}
		
	// PRINT DATABASE QUERY TOOL CODE
	function print_function_chooser () {
		$this->database->getConfig();
		
		echo "<form action=\"".$GLOBALS['pageAddress']."\" method=\"post\">\n";
		echo "<strong>Database Query: </strong>\n";
	
		if ( count($this->database->configArray) > 0 )
		{
			echo "Data File: ";
			echo "<select name=\"datafile\">";
			foreach ($this->database->configArray as $car) {
				echo "<option value='".$car['file']."'";
				if (isset($_POST['datafile']) && $_POST['datafile']==$car['file'])
					echo " selected";
				echo ">".$car['name']."</option>\n";
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

		echo "\n";
		
	}
	
	// TODO move all this to an export class
	// PRINT AN EXPORT FORMAT CHOOSER
	function print_export_form () {
		global $var_root;
		
		echo "<form action=\"".$GLOBALS['pageAddress']."\" method=\"post\">\n";
		echo "<input type=\"hidden\" name=\"function\" value=\"export\">\n";
		echo "<input type=\"hidden\" name=\"datafile\" value=\"".$_POST['datafile']."\">\n";
		echo "<strong>Choose Export Format: </strong>\n";
		
		echo "<select name=\"type\">\n";
		foreach ($this->export_types as $type) {
			echo "<option>" . $type . "</option>\n";
		}
		echo "</select>\n";
		
		echo "<input type=\"submit\" value=\"go\" />\n</form>\n";
	}

	// PRINT AN IMPORT FORMAT CHOOSER
	function print_import_form () {
		global $var_root;
		
//		print_alert("EXPERIMENTAL!");
		
		echo "<form enctype='multipart/form-data' action=\"".$GLOBALS['pageAddress']."\" method=\"post\">\n";
		echo "<input type=\"hidden\" name=\"function\" value=\"import\">\n";
//		echo "<input type=\"hidden\" name=\"datafile\" value=\"".$_POST['datafile']."\">\n";
     	echo "<input type='hidden' name='MAX_FILE_SIZE' value='1000000000' >\n";

		echo "<table>\n";
		echo "<tr><td>File Format: </td>\n<td>";
		
		echo "<select name=\"type\">\n";
		foreach ($this->import_types as $type) {
			echo "<option>" . $type . "</option>\n";
		}
		echo "</select></td></tr>\n";
		
		echo "<tr><td>File:</td><td><input type=\"file\" name=\"import_file\"></td></tr>\n";

		echo "<tr><td>Name:</td><td><input type=\"text\" name=\"name\"></td></tr>\n";
		
		echo "<tr><td>Password: </td><td><input type='password' name='password1'></td></tr>\n";
		echo "<tr><td>Repeat: </td><td><input type='password' name='password2'></td></tr>\n";
		
		echo "<tr><td></td><td><input type=\"submit\" value=\"go\" /></td></tr>\n";

		echo "</table>\n</form>\n";
	}
	
	
	// Cleanup old export temporary files
	function export_cleanup() {
		
		return; // skip this for now
		global $var_root;
		$files = glob($var_root."/export*");
		//var_dump($files);
		foreach ($files as $file) {
			$oldesttime = 10*60; // ten minutes
			if (filemtime($file) < time() - $oldesttime) {
				echo "<!-- Unlinking ".$file." -->\n";
				unlink($file);
			} else {
				echo "<!-- Allowing ".$file." to linger -->\n";
			}
			
		}
	}
	
	// Write export files
	function export ($type) {
		global $var_root;
		
		$this->export_cleanup();
		
		// load data ...
		$this->process_records();
		
		$tempfile = tempnam($var_root,"export");
		$temphandle = fopen($tempfile,'w');
		$exportFile = $tempfile.'.csv';
		
		echo "<p>Writing " . count($this->completeArray) . " records to " . $exportFile . "</p>\n";
		
		switch ($type) {
			case "csv":
				// Print Heading Row
				//var_dump($this->database->carArray);

				// This needs to be replaced with iterating over the default field array

				fwrite($temphandle, 
					"YEAR,\"".$this->database->carArray['year']
					."\",MAKE,\"".$this->database->carArray['make']
					."\",MODEL,\"".$this->database->carArray['model']
					."\",OWNER,\"".$this->database->carArray['owner']
					."\",TANKSIZE,\"".$this->database->carArray['tanksize']
					."\",SERV_INTERVAL,\"".$this->database->carArray['serv_int']
					."\",SERV_OFFSET,\"".$this->database->carArray['serv_offset']
					."\"\n"
					);
				
				fwrite($temphandle, '"Date","odo.","gal","$/gal","cost","Location","Station","Fill?","MPG","Notes"'."\n");
				
				foreach ($this->completeArray as $record)
				{
					// Print File Row
					fwrite( $temphandle, 
						$record['date'].","
						.$record['odo'].","
						.round($record['gals'],3).","
						.round($record['price'],3).","
						.round($record['tank_cost'],2).","
						.'"'.$record['loc']."\","
						.'"'.$record['name']."\","
						.'"'.$record['topd']."\","
						.round($record['mpg'],1).","
						);
				
					// In the printer-friendly case, print a row with the note on file
					if (isset($record['note']) && chop($record['note']) != "")
						fwrite ($temphandle, "\"".chop($record['note'])."\"");

					fwrite ($temphandle, "\n");
				
				}
			
				// Print units row / table footer
				fwrite ($temphandle, "mm/dd/yyyy,,miles,gallons,USD,USD,,yes/no,MPG\n");
			
				fclose ($temphandle);
				
				echo "<p><a href=\"".$var_root.'/'.basename($exportFile)."\">Click here to download...</a></p>\n";
				
				//unlink($tempfile);
				
				break;
			default:
				echo "Export type not yet implemented.";
		}
		
		if (rename ($tempfile,$exportFile) === false )
			die ("Failed to rename temp file");
	}


	// Write export files
	function import ($type) {
		global $var_root;
		
		$this->export_cleanup();
		
		
//		if (array_search($filename,$this->database->configArray)!==false)
//			die ("Name exists, please choose a different name.");
	   
		$inputName = $_FILES['import_file']['tmp_name'];
		if (is_readable($inputName)) {
			print_debug("File ".$inputName." opened for reading.");
		} else {
			die ("Couldn't open temp file.");
		}
		
//		$outputName = $var_root . '/' . $filename;
//		if (!file_exists($outputName) || is_writable($outputName))
//			print_debug("File $outputName opened for writing.");
//		else
//			die ("Couldn't open $outputName for writing.");
		
		
		switch ($type) {
			case "csv":
				// Print Heading Row
				$tmpline = file_get_contents($inputName /*, FILE_TEXT */); //fread($inputHandle, 1024);
				//echo $tmpline;
				
				$inputArray = parse_csv($tmpline);
				
				$importArray = array();
				
				foreach ($inputArray as $row) {
					// if the first column is not a date
					 if ($row[0] == "YEAR") {
					 	print_debug("this is the vehicle information row");
					 	
					 	$carArray = array(
					 		//'filename' => $_FILES['import_file']['name'],
					 		'name' => $_POST['name'],
					 		'password1' => $_POST['password1'],
					 		'year' => $row[1],
					 		'make' => $row[3],
					 		'model' => $row[5],
					 		'owner' => $row[7],
					 		'tanksize' => $row[9],
					 		'serv_interval' => $row[11],
					 		'serv_offset' => $row[13]
					 	);
					 } elseif (strtotime($row[0]) === false) {
					 	print_debug("skipping row beginning with ".$row[0]);
					 
					 } else {
						// this order MUST match the export order since we are ignoring the column headings
					 	$importArray[] = array (
					 		'date' => $row[0],
					 		'odo' => $row[1],
					 		'gals' => $row[2],
					 		'price' => $row[3],
					 		// ignore row 4
					 		'loc' => $row[5],
					 		'name' => $row[6],
					 		'topd' => $row[7],
					 		// ignore row 8
					 		'note' => $row[9]
					 	);
					 }
				}
				
				// get a new database object
				$importObject = new filedb();
				
				//var_dump($filename);
				
				// create a new vehicle and stuff it with the vehicle information
				$fileName = $importObject->newVehicle($_POST['name'], $carArray);
				
				// stuff it with the table we have put together
				$importObject->recordArray = $importArray;
				
				//var_dump($importObject);
				
				// write it to the file we have reserved
				$importObject->saveVehicle($fileName);
				
				print_alert("New vehicle ".$_POST['name']." ($fileName) created.");
				
				break;
			default:
				print_alert("Export type not yet implemented.", ERROR);
		}
	}
	
};
?>
