<?php
/*
 * Created on Dec 28, 2007 by Ryan Helinski
 *
 */
$var_root = "var";
/*
$configFile = "var/datafiles.txt";
$wfmFileName = "var/fuelstat.wfm";
*/
# Change this to something specific if the address is static
# $pageAddress = "http://page.to.server/pgmdb/";
$pageAddress = $_SERVER['PHP_SELF'];
$gnuplot_path = "/opt/local/bin/gnuplot";

# Settings for flat file record storage
#$filedb_var_root = "var"; # replaced by original var root
$filedb_config_file = $var_root."/datafiles.txt";
$filedb_wfm_file = $var_root."/fuelstat.wfm";

?>
