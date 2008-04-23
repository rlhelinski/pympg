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
	var $global_variable_names = array('var_root', 'filedb_config_file');
	
	var $configArray;
	
	var $carArray;
	var $recordArray;
	
	//var $name;

	# Constructor
	function filedb() {
		global $var_root;
		
		foreach ($this->global_variable_names as $var) {
			if (!isset($GLOBALS[$var]))
				die("Global variable $var is not set for use with filedb!");
		} 
		
		$configFile = $var_root.'/'.$GLOBALS['filedb_config_file'];
		if (file_exists($configFile)) {
			# Load the existing configuration
			$this->configArray = unserialize(file_get_contents($configFile));
			
			var_dump ($this->configArray);
		} else {
			# Write an empty configuration
			$this->configArray = array();
		}
			
			
	}
	
	/* 
	 * Standard API functions
	 */
	function newVehicle($name) {
		global $var_root;
		
		$fileName = $var_root.'/'.$name;
		
		if ( ! file_exists($fileName) )
	 	{
			$this->getConfig(); // make sure we have read any existing config
			
			// add vehicle to config
			$this->configArray['file'][] = $_POST['filename'];
			$this->configArray['password'][] = $_POST['password1'];
			$this->saveConfig();
			
			// save vehicle info in data file
			$this->vehicleArray = array();
			$this->vehicleArray['info']['year'] = $_POST['year'];
			$this->vehicleArray['info']['make'] = $_POST['make'];
			$this->vehicleArray['info']['model'] = $_POST['model'];
			$this->vehicleArray['info']['owner'] = $_POST['owner'];
			$this->vehicleArray['info']['tanksize'] = $_POST['tanksize'];
			$this->vehicleArray['records'] = array();
			
			$success = file_put_contents($fileName, serialize($this->vehicleArray));
			
			if ($success===false) {
				die("Failed to write file.");
			}
			
	 	}
	}
	
	function getVehicle ($name) {
		global $var_root;
//		$this->name; // shouldn't change within session
		$fileName = $var_root.'/'.$name;
		
		if (count($this->carArray)>0)
		// Doesn't need to be done
			return;
	
		
		if ( file_exists($fileName) )
	 	{
			$this->getConfig(); // make sure we have read any existing config
			
			$success = unserialize(file_get_contents($fileName));
			if ($success===false) {
				die("Failed to read file.");
			} else {
				$this->carArray = $success['info'];
				$this->recordArray = $success['records'];
			}
	 	}
	
		//var_dump ($this->vehicleArray);
	}
	
	function saveVehicle($name) {
		global $var_root;
		$fileName = $var_root.'/'.$name;		
		
		// make sure opened first
		$this->getVehicle($name);
		
		$success = file_put_contents($fileName, 
			serialize(array(
				'info' => $this->carArray,
				'records' => $this->recordArray)
			)
		);
		
		if ($success === false) {
			die ("Failed to save vehicle");
		}
		
		return true;
	}
	
	function getConfig () {
		// Should return the configuration record as an associative array
		// I should only keep a handle on open files 
		global $filedb_config_file;
	
		if (count($this->configArray)>0)
		// Then this need not be done
			return;
		
		if (file_exists($filedb_config_file)) {
			
			$this->configArray = unserialize(file_get_contents($filedb_config_file));

		} else {
			$this->configArray = array(); // start anew
		}
		
		//var_dump($this->configArray);
	}
	
	function saveConfig () {
		global $filedb_config_file;
		
		if (!isset($this->configArray) || count($this->configArray) == 0)
			return; // nothing need be done
		
		file_put_contents($filedb_config_file,serialize($this->configArray));
	}
	
	
	function addRecord($fileName, $record) {
		/*global $var_root;
	*/
		// Let's make sure the file is loaded
		$this->getVehicle($fileName);
		
		// Add record to array
		$this->recordArray[] = $record; 
		
		return $this->saveVehicle($fileName);
		
	}
};
 
 
?>
