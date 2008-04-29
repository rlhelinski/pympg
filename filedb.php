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
			
//			var_dump ($this->configArray);
		} else {
			# Write an empty configuration
			$this->configArray = array();
		}
			
			
	}
	
	/* 
	 * Standard API functions
	 */
	function newVehicle($name, $table) {
		global $var_root;
		
		#$fileName = $var_root.'/'.$name;
		$filePath = tempnam($var_root,"veh-");
		$fileName = basename($filePath);
		
		$this->getConfig(); // make sure we have read any existing config
		
		// add vehicle to config
		$this->configArray[] = array(
			'file' => $fileName,
			'name' => $name,
			'password' => $table['password1']
		);
		$this->saveConfig();
		
		// save vehicle info in data file
		$this->carArray = array();
		$this->carArray['year'] = $table['year'];
		$this->carArray['make'] = $table['make'];
		$this->carArray['model'] = $table['model'];
		$this->carArray['owner'] = $table['owner'];
		$this->carArray['tanksize'] = $table['tanksize'];
		
		if ($this->saveVehicle($fileName)===false) {
			die("Failed to write file.");
		}
		
		return $fileName;
	}
	
	
	function getVehicle ($fileName) {
		global $var_root;
		
		$filePath = $var_root.'/'.$fileName;
		
//		foreach ($this->configArray as $tmp) {
//			if ($tmp['name'] == $name) { 
//				$car = $tmp;
//				break;
//			}
//		}
//		
//		$fileName = $car['file'];
		
		if (count($this->carArray)>0)
		// Doesn't need to be done ??
			return;
	
		
		if ( file_exists($filePath) )
	 	{
			$this->getConfig(); // make sure we have read any existing config
			
			$success = unserialize(file_get_contents($filePath));
			if ($success===false) {
				die("Failed to read file $fileName.");
			} else {
				$this->carArray = $success['info'];
				$this->recordArray = $success['records'];
			}
	 	}
	
		//var_dump ($this->vehicleArray);
	}
	
	function saveVehicle($fileName) {
//		var_dump($fileName);
		global $var_root;
		$filePath = $var_root.'/'.$fileName;
		
		$success = file_put_contents($filePath, 
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
	
	function renameVehicle($oldname, $newname) {
		global $var_root;
		
		$oldFileName = $var_root . '/' . $oldname;
		$newFileName = $var_root . '/' . $newname;

		if (!file_exists($newFileName)) {
			rename ($oldFileName, $newFileName) || die("Couldn't rename file");		
		} else {
			die ("File already exists at $newname");
		}
		
		// update the config array
	    $index = array_search($oldname,$this->configArray['file']);
	    if ($index === false) die ("No existing file found.");
	    
	    $this->configArray['file'][$index] = $newname;
	    
	    $this->saveConfig();
	    
		
		// save the config array
		
		
					
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
