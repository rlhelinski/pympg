<?php
/*
 * Created on Apr 21, 2008 by Ryan Helinski
 *
 */
	
	$newArray = array();
	$fileName = "../var/ryan-matrix.txt";
	
	$filedb_config_file = "../var/datafiles.txt";
	
	$configArray = array();
	
	if (count($configArray)>0)
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
	//                      $configArray[] = $newArray;
	                $configArray = array_merge($configArray,$newArray);
	        }
	}

	var_dump ($configArray);
	
	$serialData = serialize($configArray);
	
	file_put_contents("../var/config.dat",$serialData);
	
?>
