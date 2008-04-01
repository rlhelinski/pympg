<!-- localSettings.php -->
<?php
/*
 * Created on Dec 28, 2007 by Ryan Helinski
 *
 */
$var_root = "var";

# Change this to something specific if the address is static
# $pageAddress = "http://page.to.server/pgmdb/";
$pageAddress = $_SERVER['PHP_SELF'];

# Change this to a specific path if GNUPLOT is not found
# $gnuplot_path = "/opt/local/bin/gnuplot";
$gnuplot_path = exec('which gnuplot');

# Settings for flat file record storage
# TODO change this to $filedb_config = $var_root."/datafiles";
$filedb_config_file = $var_root."/datafiles.txt";
$wfm_file = $var_root."/fuelstat.wfm";

?>
