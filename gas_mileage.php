<!-- PHP Gas Mileage DataBase Access Interface, by Ryan Helinski -->
<?php 
list($begin_usec, $begin_sec) = explode(" ", microtime());

# Load settings and libraries
include("localSettings.php");
include("pgmdb.php");

# Initialize the database access engine
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
<style type="text/css">
	DIV {
		border: 1px solid #eee;
	}
</style>
</head>
<body>

<div id="frame">
<div id="header">
<h1>PHP Gas Mileage Database</h1>
</div>

<?php $gasMileage->print_function_chooser(); ?>
<hr>

<div>
<?php
if (isset($_POST['function'])) {

	switch ($_POST['function']) {
		case "summary":
			$gasMileage->print_summary();
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
		default:
			die ("Invalid function ".$_POST['function']);
	}
	
} else {
	echo "<p>Please use the toolbar above to get started.</p>\n";	
}


?>
</div>
<hr>
<div class="footnote">PHP Gas Mileage Database, by Ryan Helinski.
<?php 
list($end_usec, $end_sec) = explode(" ", microtime());

echo "Executed in: "
  .number_format($end_usec + $end_sec - $begin_usec - $begin_sec,3)
  ." s"; ?>
</div>

</div>

</body>
</html>
