<!-- PHP Gas Mileage DataBase Access Engine, by Ryan Helinski -->
<?php
/*
 * Created on Dec 22, 2007 by Ryan Helinski
 *
 * This class will provide a standard interface to some form of database, 
 * depending on the configuration file and those supported in this class. 
 * 
 * Functions will be called to get and add records, and the results will
 * be associative "record" arrays that can be returned. 
 *
 */
 
class filedb {
	
	# A list of variables which _must_ be defined before construction
	var $global_variable_names = array('filedb_config_file', 'filedb_wfm_file', 'var_root');
	
	# File handles so we can keep track of open ones
	var $files_handles = array();

	# Constructor
	function filedb() {
		global $var_root;
		
		foreach ($this->global_variable_names as $var) {
			if (!isset($GLOBALS[$var]))
				die("Global variable $var is not set for use with filedb!");
		} 
		
		if (file_exists($var_root.'/'.$GLOBALS['filedb_config_file'])) {
			# Load the dynamic configuration
			
		} else {
			# Write an empty configuration
			
		}
			
			
	}
	
	/* 
	 * Standard API functions
	 */
	function newVehicle() {
		global $var_root;
		
		 if ( ! file_exists($var_root.'/'.$_POST['filename']) )
		 	{
			   $handle = fopen($var_root.'/'.$_POST['filename'],"x");
			   $headerstring = "year=".$_POST['year']."&make=".$_POST['make']
			   ."&model=".$_POST['model']."&owner=".$_POST['owner']."&tanksize="
			   .$_POST['tanksize']."\n";
	
			   if (fwrite($handle, $headerstring) === FALSE) {
			     die( "Cannot write to file (".$var_root.'/'.$_POST['filename'].")");
			   }
			   
			   echo "<div class='notice'>Successfully created data file ".$var_root.'/'.$_POST['filename']."</div>\n";
			   
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
					die( "Couldn't add the new file to the list of data files" );
				}
			     
			   echo "<div class='notice'>Successfully added new file to list of data files, "
			   	."<a href=\"$pageAddress?datafile=".$_POST['filename']
			   	."&function=record\">Start adding records for this vehicle</a>.</div>\n";
			   fclose($handle);
			   
			   // TODO should switch to 'record' function at this point.
		 	}
	       else { 
	       	echo "<div class='alert'>File already exists.</div>\n";
	       }
	}
	
	function getConfig () {
		// Should return the configuration record as an associative array
		// I should only keep a handle on open files 
		$newArray = array();
		global $filedb_config_file;
	
		if (count($this->configArray)>0)
			return;
		
		if (($handle = fopen($filedb_config_file, "r"))===false) {
			debug_print_backtrace();
			die( "Couldn't open ".$filedb_config_file);
		}
			
		while(!feof($handle)) {
			if (($buffer = fgets($handle, 4096))!==false)
			{
				$buffer = rtrim ($buffer);
				parse_str($buffer,$newArray);
		//		$configArray[] = $newArray;
				$this->configArray = array_merge($this->configArray,$newArray);
			}
		}
		//echo "<pre>";
		//print_r($configArray);
		//echo "</pre>";
	}
	
	function getVehicleData () {
		$fileName = $_POST['filename'];
		
		if (count($this->carArray)>0)
			return;
	
		if (($handle = fopen($fileName, "r"))===false) {
			debug_print_backtrace();
			die ("Couldn't open ".$fileName);
		}
	
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
	
	/*
	 * Implementation-specific functions
	 */
	function writeConfigFile() {
		
	}
	
	function addRecord($record) {
		$newstring = http_build_query($record)."\n";
		$filename = $_POST['filename'];
	
		// Let's make sure the file exists and is writable first.
		if (is_writable($filename)) {
			// Create a backup copy. This is not critical
		 
			if (!copy($filename, $filename."~"))
			    echo "<div class='alert'>Failed to create backup.</div>\n";
	
			if (!$handle = fopen($filename, 'a')) {
				echo "<div class='alert'>Cannot open file ($filename)</div>\n";
				exit;
			}
	
			if (fwrite($handle, $newstring) === FALSE) {
				echo "<div class='alert'>Cannot write to file ($filename)</div>\n";
				exit;
			}
		 
			echo "<div class='notice'>Successfully added record to <tt>".$filename."</tt></div>\n";
			
			$this->process_records();
			
			echo "<P>New miles/gallon estimate: <b>"
				.number_format($this->completeArray[count($this->completeArray)-1]['mpg'],2)
				." mpg</b></P>\n";
			
			# Empty the fields to be printed in the form (not working)
			$date = $odo = $gals = $price = $loc = $name = $topd = $note = "";
	
			fclose($handle);
	
		} else {
			echo "<div class='alert'>The file $filename is not writable</div>\n";
		}
	}
};
 
 
?>
