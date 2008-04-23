<!-- PHP Gas Mileage DataBase Access Interface, by Ryan Helinski -->
<?php 
list($begin_usec, $begin_sec) = explode(" ", microtime());

# Load settings and libraries
include("localSettings.php");
include("pgmdb.php");

# Initialize the statistics and data engine
$gasMileage = new pgmdb();

# Transform GET arguments to POST arguments for flexibility
foreach ($_GET as $key => $val) {
	$_POST[$key] = $val;
}

?>
<html>
<head>
<title>PHP Gas Mileage Database</title>
<link rel="stylesheet" type="text/css" href="spreadsheet.css">
</head>
<body>

<div id="frame">
<div id="header">
<h1>PHP Gas Mileage Database</h1>
</div>

<div id="toolbar">
<?php $gasMileage->print_function_chooser(); ?>
</div>

<div id="content">

<?php
if (isset($_POST['function'])) {

	switch ($_POST['function']) {
		case "summary":
			$gasMileage->print_summary() &&
			$gasMileage->print_stats_summary() &&
			$gasMileage->print_stats_detailed();
			
			break;
		case "print":
			$gasMileage->print_friendly_records();
			break;
		case "export":
			if (isset($_POST['type'])) {
				$gasMileage->export($_POST['type']);
			} else {
				$gasMileage->print_export_form();
			}
			break;
		case "plot":
			$gasMileage->display_waveform();
			break;
		case "record":
			$gasMileage->print_add_record_form();
			break;
		case "create":
			$gasMileage->print_new_file_form();
			break;
		case "test":
			$gasMileage->process_records();
			break;
		default:
			die ("Invalid function ".$_POST['function']);
	}
	
} else {
	echo "<p>Please use the toolbar above to get started.</p>\n";	
}


?>
</div>

<div id="footer">PHP Gas Mileage Database, by Ryan Helinski.
<?php 
list($end_usec, $end_sec) = explode(" ", microtime());

echo "Execution time: "
  .number_format($end_usec + $end_sec - $begin_usec - $begin_sec,3)
  ." s"; ?>
</div>

</div>

</body>
</html>
