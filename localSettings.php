<!-- localSettings.php -->
<?php
/*
 * Created on Dec 28, 2007 by Ryan Helinski
 *
 */
$RelVersion = "2.0b";
$SiteName = "PHP Gas Mileage Database (Version $RelVersion)";
$var_root = "var";

# Change this to something specific if the address is static
# $pageAddress = "http://page.to.server/pgmdb/";
$pageAddress = $_SERVER['PHP_SELF'];

# Change this to a specific path if GNUPLOT is not found
# $gnuplot_path = "/opt/local/bin/gnuplot";
$gnuplot_path = exec('which gnuplot');

# Settings for flat file record storage
# TODO change this to $filedb_config = $var_root."/datafiles";
$filedb_config_file = $var_root."/config.dat";
$filedb_record_ext = 'dat'; # kind of arbitrary

$wfm_file = $var_root."/fuelstat.wfm";

# To bring date formatting up to standards
date_default_timezone_set('America/New_York');
?>
