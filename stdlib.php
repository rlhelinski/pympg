<?php
/*
 * Created on Apr 24, 2008 by Ryan Helinski
 *
 * standard functions
 *
 */

define("NOTICE",0);
define("WARNING",0);
define("ERROR",0);

function print_alert($message, $severity=NOTICE) {
	if ($severity == NOTICE) {
		$class = "notice";
	} elseif ($severity == WARNING) {
		$class = "warning";
	} elseif ($severity == ERROR) {
		$class = "error";
	}
	
	echo "\n<div class='$class'>$message</div>\n";
}

?>
