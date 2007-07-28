<?php list($begin_usec, $begin_sec) = explode(" ", microtime()); ?>
<!-- Gas Mileage PHP Database, by Ryan Helinski
gas_mileage.php, version 0.7

Coming Soon: Export to spreadsheet format

since 0.6:
* Fixed all the warnings/notices that were being generated but not printed
  unless enabled by the PHP server. This just makes the code more robust,
  and may have fixed a few potential bugs.

* This also included adding defaults for the add record form a format
  which allows the fields to be non-empty in the case there was no 
  corresponding post data. In other words, the fields could have example
  values by default and a javascript could clear that value upon a click
  so the user doesn't have to erase anything. Not interesting to me yet.

    since 0.5:
    Added a new plot function, which calls a gnuplot script and converts the 
    eps to png for display. Requires "gnuplot" and libgp.

    since 0.4: 
	added data conversion/formatting for form input
	various bug fixes and added statistics

    since 0.3: added prediction of next service interval and fixed bugs,
               added Station field
    since 0.2: added date conversion to UTC and math for time
               validated math with spreadsheet
    since 0.1: added password protection for adding records
-->
<html>
<head>
<title>PHP Gas Mileage Database</title>
<style type="text/css">
   pre {
   font-size: 10pt;
 }
   
   .code {
     font-size: 10pt;
     font-family: Courier New,monospace;
   }
   
   .footnote {
     font-size: 10pt;
     font-style: Italic;
   }
</style>
</head>
<body>

<?php

if (isset($_GET['filename']))
  $filename = $_GET['datafile'];
else if (isset($_POST['datafile']))
  $filename = $_POST['datafile'];
else $filename = "";	 

if ($_SERVER['PHP_SELF'])
  $page_address = $_SERVER['PHP_SELF'];
	
$global_gals = 0;
$global_miles = 0;
$global_cost = 0;
$global_days = 0;
$max_range = 0;
$max_mpg = 0;
$min_mpg = INF;
$records = -1;
$format = '%m/%d/%Y';

// SUMMARY / PRINT CODE
if ($filename != "" && 
 	(isset($_POST['function']) && $_POST['function'] == "summary") 
   || (isset($_POST['function']) && $_POST['function'] == "print"))
  {
    # We only read the file here
    $handle = fopen($filename, "r");

    if ($handle) {
      // Get header from file
      $buffer = fgets($handle, 4096);
      parse_str($buffer);

      echo "<h1>".$make." ".$model." Gas Mileage Records</h1>\n";

      echo "<p>Data File Name: <span class=\"code\">";
      if ($_POST['function'] != "print")
	echo "<a href=\"".$filename."\">".$filename."</a>";
      else echo $filename;
      echo "</span>, Table Format: <b>"
	.($_POST['function']=="print"?
	"Reduced printer-friendly report"
	:"Full report with derived statistics")
	."</b></p>\n"; 

      echo "<p>Year: <b>".$year."</b>, Make: <b>".$make."</b>, Model: <b>"
	.$model."</b>, Owner: <b>".$owner . "</b>, Tank Size: <b>".$tanksize
	."</b></p>\n";

      if ($_POST['function'] == "print")
	echo "<table border=1 width=100%>\n";
      else
	echo "<table border=0 width=100%>\n";

      // Print Heading Row
      echo "<tr bgcolor=\"#F0F0F0\">"
	."<td><b>Date</b></td>"
	.($_POST['function']=="summary" ?
		"<td align=right><b>Days</b></td>" : "")
	."<td align=right><b>Odo.</b></td>"
	.($_POST['function']=="summary" ?
		"<td align=right><b>Trvl'd</b></td>" : "")
	."<td align=right><b>Gallons</b></td>"
	."<td align=right><b>$/gal</b></td>"
	."<td align=right><b>cost</b></td>"
	.($_POST['function']=="summary" ?
		"<td align=right><b>mi/day</b></td>" : "")
	."<td><b>Location</b></td>"
	."<td><b>Station</b></td>"
	."<td><b>Filled?</b></td>"
	.($_POST['function']=="summary" ? 
		"<td align=right><b>Miles/Gal</b></td>" : "")
	.(isset($prnt_rng_avg) ? "<td align=right><b>Rng.Avg.</b></td>" : "")
	."</tr>\n";

      while (!feof($handle)) {
	$records = $records + 1;

	// Get Record From File
	if ( $records % 2 == 1 && $_POST['function'] != "print" ) 
	  { $opts = "bgcolor=\"#ffffb0\""; } 
	else { $opts = ""; }

	$buffer = fgets($handle, 4096);
	if ( $buffer == "" ) break;
	
	$note = "";

	parse_str($buffer);

	// Update global stats
	if ($records > 0)
	  { 
	    $global_gals = $global_gals + $gals;
	    $travelled = $odo - $last_odo;

	    if ($max_range < $travelled) 
	      { $max_range = $travelled; }

	    $mpg = ($odo-$last_odo)/$gals;
	    if ($topd{0} == "Y")
	      {
		if ($max_mpg < $mpg) $max_mpg = $mpg;
		if ($min_mpg > $mpg) $min_mpg = $mpg;
	      } 

	    $time_elap = strtotime($date) - strtotime($last_date);
	    $days_elap = round ($time_elap / 86400);
	    $global_days = $global_days + $days_elap;
	    $global_miles = $global_miles + $travelled; 
	    $tank_cost = round($price*$gals,2);
	    $global_cost = $global_cost + $tank_cost;
	    $miles_per_day = $travelled/$days_elap;

	  }
	else { 
	  $first_gals = $gals;
	  $travelled = $days_elap = "N/A";
	  $tank_cost = 0;
	  $travelled = 0;
	  $days_elap = 0; 
	  $miles_per_day = 0;
	  $mpg = 0;
	}

	// Print Table Row
	echo "<tr $opts>"
	."<td>".$date
	.(chop($note) != "" && $_POST['function'] == "summary" ?
		" <img src=\"fat_pen.png\" alt=\"".chop($note)
		."\" title=\"".chop($note)."\">" : "" )
	."</td>"
	.($_POST['function']=="summary" ?
		"<td align=right>".$days_elap."</td>" : "")
	."<td align=right>".number_format($odo)."</td>"
	.($_POST['function']=="summary" ?
		"<td align=right>".$travelled."</td>" : "")
	."<td align=right>".number_format($gals,3)."</td>"
	."<td align=right>".number_format($price,3)."</td>"
	."<td align=right>".number_format($tank_cost,2)."</td>"
	.($_POST['function']=="summary" ?
		"<td align=right>".number_format($miles_per_day,2)."</td>"
		: "")
	."<td>".$loc."</td>"
	."<td>".$name."</td>"
	."<td>".$topd."</td>";

	if ($_POST['function']=="summary") {
	if (isset($last_topd) && $topd{0} == "Y" && $last_topd != "") { 
	  echo "<td align=right>".number_format($mpg,1)."</td>"; }
	else { echo "<td align=right>(".number_format($mpg,1).")</td>"; }
	}

	if (isset($prnt_rng_avg))
	{
	  if ($gals+$last_gals > 0)
	    $rng_avg = number_format(($odo-$last_last_odo)/($gals+$last_gals),1);
	  else 
	    $rng_avg = "N/A";
	

	  if ($last_last_odo != "" && $topd{0} == "Y" && $last_topd{0} == "Y" ) {
	    echo "<td align=right>".$rng_avg."</td>";
	  } else { echo "<td align=right>(".$rng_avg.")</td>"; }	  
	}
	echo "</tr>\n";

	// In the printer-friendly case, print a row with the note on file
	if ($_POST['function']=="print" && chop($note) != "")
		#echo "<tr><td><i>Note -></i></td><td colspan=7><i>"
		echo "<tr><td></td><td colspan=7><i>"
		.chop($note)."</i></td></tr>";

	// Save Some Data for Next Iteration
	if (isset($last_odo)) $last_last_odo = $last_odo;
	$last_odo = $odo;
	$last_date = $date;
	$last_gals = $gals;
	$last_topd = $topd;
      }
      fclose($handle);

	// Print units row / table footer
      echo "<tr bgcolor=\"#F0F0F0\">"
	."<td><i>mm/dd/yyyy</i></td>"
	.($_POST['function']=="summary" ?
		"<td align=right><i>days</i></td>" : "")
	."<td align=right><i>miles</i></td>"
	.($_POST['function']=="summary" ?
		"<td align=right><i>miles</i></td>" : "")
	."<td align=right><i>gallons</i></td>"
	."<td align=right><i>USD</i></td>"
	."<td align=right><i>USD</i></td>"
	.($_POST['function']=="summary" ?
		"<td align=right><i>miles</i></td>" : "")
	."<td></td>"
	."<td></td>"
	."<td><i>yes/no</i></td>"
	.($_POST['function']=="summary" ?
		"<td align=right><i>miles/gal</i></td>" : "")
	.(isset($prnt_rng_avg) ? "<td align=right><i>miles/gal</i></td>" : "")
	."</tr>\n";

      echo "</table>\n";

      echo "<blockquote>\n"
	."<h2>Gas Mileage Summary</h2>\n"
	."Number of Records: <b>".$records."</b><br>\n"
	."Total Gallons Consumed: <b>".number_format(round($global_gals))."</b> gallons<br>\n"
	."Total Miles Travelled: <b>".number_format($global_miles)."</b> miles<br>\n"
	."Total Days on Record: <b>".$global_days."</b> days, <b>".round($global_days/365.25,2)."</b> years<br>\n"
      	."Total Gas Cost: <b>$".number_format(round($global_cost))."</b> US dollars<br>\n"
	."Latest Gas Mileage: <b>".round(($last_odo-$last_last_odo)/$last_gals,2)."</b> mpg<br>\n";
	


      echo "<h2>Estimated Statistics</h2>\n"
	."Minimum Gas Mileage: <b>".round($min_mpg,1)."</b> miles/gallon<br>\n"
        ."Average Gas Mileage: <b>".round($global_miles/($global_gals),1)
	."</b> miles/gallon<br>\n"
	."Maxiumum Gas Mileage: <b>".round($max_mpg,1)."</b> miles/gallon<br>\n"
	."Average Days Between Refeuling: <b>".round($global_days/($records-1))."</b> days<br>\n"
	."Average Miles per Day: <b>".round($global_miles/$global_days)
	."</b> miles/day<br>\n"
	."Estimated Miles per Year: <b>"
	.number_format(round(365.25*$global_miles/$global_days,-2),0,'.',',')
	."</b> miles/year<br>\n"
	."Estimated Gallons per Year: <b>".round(365.25*$global_gals/$global_days)."</b> gallons"
	." per day <b>".round($global_gals/$global_days,2)."</b> gallons<br>\n"
	."Estimated Annual Gas Cost: <b>$".round(365.25*$global_cost/$global_days)."</b> US dollars"
	." per day <b>$".round($global_cost/$global_days,2)."</b> US dollars<br>\n"
      // The actual maximum range is the maximum distance between fueling
      // The theoretical maximum range is the range one could drive with 
      // average or maximum gas mileage with 100% of the tank's fuel.
	."Average Range: <b>".round($global_miles/($records))
	."</b> miles<br>\n"
	."Maximum Range: <b>".$max_range."</b> miles<br>\n"
	."Theoretical Range: <b>".round($tanksize*$global_miles/$global_gals)
	." - ".round($tanksize*$max_mpg)."</b> miles<br>\n";
	$estimated_mileage = $odo+($global_miles/$global_days)*(time()-strtotime($date))/86400;
	$days_to_service = round((5000-(fmod($estimated_mileage,5000)))/($global_miles/$global_days),1);
      	echo "Estimated Current Milage: <b>"
	.round($estimated_mileage)
        ."</b> miles<br>\n"
	."Days until next 5k-mile service interval: <b>"
	//.round(($time_to_service*86400-time()+strtotime($date))/86400,2)
	.round($days_to_service)
	."</b> days, on or before <b>"
	.strftime('%m/%d/%Y',$days_to_service*86400+strtotime($date))."</b><br>\n"
      	."</blockquote>\n";

    }
    else {
      echo "Error: couldn't open ".$filename."!<br>\n";
    }

    //echo "<p><a href=\"add_form.php?datafile=".$filename
    //."\">Add Refueling Record</a></p>";
    //echo "<p><a href=\"index.php?\">Change Vehicle</a></p>";
  }

// ADD RECORD CODE
if ((isset($_POST['datafile']) && $_POST['datafile'] != "") 
  && (isset($_POST['function']) && $_POST['function'] == "add record"))
  {
    $datafile = $_POST['datafile'];
    $index = 0;

    // Retrieve the password hash
    $handle = fopen("./datafiles.txt", "r");
    $buffer = fgets($handle, 4096);
    parse_str($buffer);
    foreach ($file as $value)
      {
	if (rtrim($datafile) == rtrim($value))
	  break;
	$index = $index + 1;
      }
    $buffer = fgets($handle, 4096);
    parse_str($buffer);
    fclose($handle);
    $password_hash = $password[$index];
    
    echo "<h1>Add Refueling Record</h1>\n";
    echo "<p>Data File Name: <span class=\"code\"><a href=\"".$filename."\">"
      .$filename."</a></span></p>\n";

    //I'm assuming if the date is empty, the user hasn't filled out any of the form. 
    if (isset($_POST['date']) && $_POST['date'] != "" )
      {
        $date = date("m/d/Y",strtotime($_POST['date'])); // USA style
        $odo = number_format($_POST['odo'], 0, '.', '');
        $gals = number_format($_POST['gals'], 3, '.', '');
        $price = number_format($_POST['price'], 3, '.', '');
        $loc = $_POST['loc'];
        $name = $_POST['name'];
        $topd = $_POST['topd'];
        $note = $_POST['note'];
      }

    if ( isset($_POST['date']) &&($date_UTC = strtotime($_POST['date']))!==false )
      {
	if (md5($_POST['password']) != rtrim($password_hash))
	  {
	    echo "Error: Password doesn't match that on file.<br>\n";
	    //echo "submitted: ". md5($_POST['password'])." on file: ".$password_hash." ".$index."<br>\n";
	    exit;
	  }
	
	$newstring = "date=".$date."&odo=".$odo."&gals=".$gals."&price="
	  .$price."&loc=".$loc."&name=".$name."&topd=".$topd."&note=".$note."\n";

	// Let's make sure the file exists and is writable first.
	if (is_writable($filename)) {
	 
	  // Create a backup copy. This is not critical
	  if (!copy($filename, $filename."~"))
	    { echo "Failed to create backup.\n"; }

	  // In our example we're opening $filename in append mode.
	  // The file pointer is at the bottom of the file hence
	  // that's where $somecontent will go when we fwrite() it.
	  if (!$handle = fopen($filename, 'a')) {
	    echo "Cannot open file ($filename)";
	    exit;
	  }

	  // Write $somecontent to our opened file.
	  if (fwrite($handle, $newstring) === FALSE) {
	    echo "Cannot write to file ($filename)";
	    exit;
	  }
	 
	  echo "Successfully added record to ".$filename."<br>\n";
          $date = $odo = $gals = $price = $loc = $name = $topd = $note = "";

	  fclose($handle);

	} else {
	  echo "The file $filename is not writable";
	}
      }
    else {
      if (!isset($_POST['date']) || $_POST['date'] == "") 
        echo "Please fill out the form and click submit.<br>\n";
      else if (strtotime($_POST['date']) === false) echo "ERROR: Couldn't understand your date entry.<br>\n";
      else echo "Failed to convert date entry \"".$_POST['date']."\" \"".$date_UTC."\".\n";
    }
    
    echo "<form action=\"".$_SERVER['PHP_SELF']."\" method=\"post\">\n"
      ."<input type=\"hidden\" name=\"function\" value=\"add record\" />\n"
      ."<input type=\"hidden\" name=\"datafile\" value=\"".$datafile."\" />\n"
      ."<pre>\n"
      ."Password:         <input name=\"password\" type=\"password\" />\n"
      ."Date:             <input name=\"date\" type=\"text\" value=\"".
      (isset($date)?$date:"")."\" /> (ex.: 09/07/2006)\n"
      ."Odometer Reading: <input name=\"odo\" type=\"text\" value=\"".
      (isset($odo)?$odo:"")."\" /> (ex.: 210512)\n"
      ."Gallons:          <input name=\"gals\" type=\"text\" value=\"".
      (isset($gals)?$gals:"")."\"/> (ex.: 10.596)\n"
      ."Price per Gallon: <input name=\"price\" type=\"text\" value=\"".
      (isset($price)?$price:"")."\" /> (ex.: 2.199)\n"
      ."Station:          <input name=\"name\" type=\"text\" value=\"".
      (isset($price)?$name:"")."\" /> (ex.: Enron)\n"
      ."Location:         <input name=\"loc\" type=\"text\" value=\"".
      (isset($loc)?$loc:"")."\" /> (ex.: Clarksville)\n"
      ."Topped Off:       <select name=\"topd\">\n"
      ."<option>Yes</option>"
      ."<option>No</option>"
      ."</select>\n"
      ."Notes:\n"
      ."<textarea name=\"note\" rows=\"2\" cols=\"40\" />"
      .(isset($note)?$note:"")."</textarea>\n"
      ."<input type=\"submit\" />"
      ."</pre>"
      ."</form>";


   echo "<p>NOTES: The gas mileage calculation scheme assumes that you top-off each time you fill. If you do not top off, the gas mileage cannot be accurately calculated. Do not use commas in numerical fields. Do not use the ampersand (&) character. The database file (plain text) can be stored for off-line backup or modification purposes via the link above. </p>";

  }

// ADD NEW DATA STORAGE FILE CODE
if (isset($_POST['function']) && $_POST['function'] == "create")
  {
   echo "<h2>Create New File</h2>\n";

   if ( isset($_POST['filename']) && $_POST['filename'] != "" )
     {
       if ( $_POST['password1'] != $_POST['password2'] )
	 {
	   echo "Error: Passwords don't match.<br>\n";
	 }

       if ( ! file_exists($_POST['filename']) )
	 {
	   $handle = fopen($_POST['filename'],"x");
	   $headerstring = "year=".$_POST['year']."&make=".$_POST['make']
	   ."&model=".$_POST['model']."&owner=".$_POST['owner']."&tanksize="
	   .$_POST['tanksize']."\n";

	   if (fwrite($handle, $headerstring) === FALSE) {
	     echo "Cannot write to file (".$_POST['filename'].")";
	     exit;
	   }
	   
	   echo "Successfully created data file ".$_POST['filename']."<br>\n";
	   
	   fclose($handle);

	   // Create a backup copy. Failure of this is not fatal.
	   if (!copy("./datafiles.txt", "./datafiles.txt~"))
	     { echo "Failed to create backup.\n"; }
	   $handle = fopen("./datafiles.txt","r");
	   $oldstr = rtrim(fgets($handle, 4096));
	   //$oldstr = substr($oldstr,0,strlen($oldstr)-1);
	   //$oldstr = rtrim($oldstr);
	   $oldpasswds = rtrim(fgets($handle, 4096));
	   fclose($handle);

	   $handle = fopen("./datafiles.txt","w");
	   if (
	       (fwrite($handle, $oldstr."&file[]="
		       .$_POST['filename']."\n") === FALSE)
	       ||
	       (fwrite($handle, $oldpasswds."&password[]="
		       .md5($_POST['password1'])."\n") === FALSE)
	       )
	     {
	       echo "Couldn't add the new file to the list of data files.<br>\n";
	       exit;
	     }
	   echo "Successfully added new file to list of data files.<br>\n";
	   fclose($handle);
	 }
       else { echo "File already exists.<br>\n"; }
     }   

   echo "<p>Create a new (empty) file for storing vehicle gas mileage data. </p>\n"
     ."<form action=\"".$_SERVER['PHP_SELF']."\" method=\"post\">"
     ."<input type=\"hidden\" name=\"function\" value=\"create\" />\n"
     ."<pre>"
     ."Filename:  <input name=\"filename\" type=\"text\" /> (ex: ryan.txt)\n"
     ."Password:  <input name=\"password1\" type=\"password\" />\n"
     ."  repeat:  <input name=\"password2\" type=\"password\" />\n"
     ."Year:      <input name=\"year\" type=\"text\" /> (ex: 1984)\n"
     ."Make:      <input name=\"make\" type=\"text\" /> (ex: Honda)\n"
     ."Model:     <input name=\"model\" type=\"text\" /> (ex: Accord)\n"
     ."Owner:     <input name=\"owner\" type=\"text\" /> (ex: Ryan Helinski)\n"
     ."Tank Size: <input name=\"tanksize\" type=\"text\" /> (ex: 12.1)\n"
     ."<input type=\"submit\" /></pre></form>";

  }

// WRITE WAVEFORM AND PLOT CODE
if (isset($_POST['function']) && $_POST['function'] == "plot")
  {
    $wfmFileName = "fuelstat.wfm";
    if (($wfmHandle = fopen($wfmFileName,"w"))!==FALSE)
      {
	if (($dataHandle = fopen($filename, "r"))!==FALSE)
	  {

	    #echo "<pre>";
	    $heading = "# time\t\tmiles\tgals\t$/gal\t$/tank\tmi/day\tmpg\n";
	    #echo $heading;
		  
	    if (fwrite ( $wfmHandle, $heading )===FALSE)
		echo "I/O error.\n";

	    // Read line with car data
	    $buffer = fgets($dataHandle, 4096);
	    parse_str($buffer);

      echo "<h1>".$make." ".$model." Gas Mileage Records</h1>\n";

      echo "<p>Data File Name: <span class=\"code\">";
      if ($_POST['function'] != "print")
        echo "<a href=\"".$filename."\">".$filename."</a>";
      else echo $filename;
      echo "</span>, Report Format: <b>Data Waveforms</b>"
        ."</p>\n";

      echo "<p>Year: <b>".$year."</b>, Make: <b>".$make."</b>, Model: <b>"
        .$model."</b>, Owner: <b>".$owner . "</b>, Tank Size: <b>".$tanksize
        ."</b></p>\n";

	    while (!feof($dataHandle)) {
	      $records = $records + 1;

	      $buffer = fgets($dataHandle, 4096);
	      if ( $buffer == "" ) break;
	
	      parse_str($buffer);

	      if ($records > 1)
		{ 
		  $travelled = $odo - $last_odo;
		  $mpg = ($odo-$last_odo)/$gals;
		  $time_elap = strtotime($date) - strtotime($last_date);
		  $days_elap = round ($time_elap / 86400);
		  $tank_cost = round($price*$gals,2);
		  
		  
		  // Print Waveforms

		  $fileLine = 
#		    round((strtotime($date)-$starttime)/86400,1)."\t\t"
		    round(strtotime($date))."\t"
		    .$travelled."\t"
		    .$gals."\t"
		    .$price."\t"
		    .$tank_cost."\t"
		    .round($travelled/$days_elap,3)."\t"
		    .round($mpg,3)."\n";


		  #echo $fileLine;

		  if (fwrite ( $wfmHandle, $fileLine )===FALSE)
		    {
		      echo "I/O error.\n";
		      exit();
		    }
		  
		}
	      else {
		$starttime = strtotime($date);
	      }

	      $last_odo = $odo;
	      $last_date = $date;
	    }

	    #echo "</pre>";
	    fclose($wfmHandle);
	    fclose($dataHandle);

	    echo system("gnuplot plot.gp");
	    
	    echo "<img src=\"mpg.png\" alt=\"Gas Mileage\">\n";
            echo "<img src=\"fuelcost.png\" alt=\"Fuel Cost\">\n";

	    ##echo "<p><a href=\"mpg.eps\">mpg.eps</a></p>\n";
	  }
	else {
	  echo "Couldn't open ".$filename." for reading.\n";
	  exit();
	}

      }
    else {
      echo "Couldn't open ".$wfmFileName." for writing.\n";
      exit();
    }

  }

// PRINT DATABASE QUERY TOOL CODE
if (!isset($_POST['function']) || $_POST['function'] != "print") {
  if (!(isset($_POST['function']) && $_POST['function'] == "add record"))
    {
      //This will already have been done at this point
      $handle = fopen("./datafiles.txt","r");
      $buffer = fgets($handle, 4096);
      parse_str ($buffer);
      fclose($handle);
    }  

  if (!isset($_POST['datafile'])&&!isset($_GET['datafile']))
    echo "<h1>PHP Gas Mileage Database</h1>\n";
  else
    echo "<hr><h2>New Database Query</h2>\n";
  echo "<form action=\"".$page_address."\" method=\"post\">\n";
  if ( count($file) > 0 )
    {
# MAKE THIS CODE LIKE NEXT CODE
      echo "<p>Select Existing Data File: ";
      echo "<select name=\"datafile\">";
      if ($_POST['datafile'] != "")
	echo "<option>".$_POST['datafile']."</option>\n";
      foreach ($file as $value) {
	if ($_POST['datafile'] != rtrim($value))
	  echo "<option>".rtrim($value)."</option>\n";
      }
      echo "</select></p>\n";
    }

  # MOVE THIS DECLARATION TO TOP
  $function_list = array('summary','print','add record',"plot",'create');

  echo "<p>Select Database Function: "
    ."<select name=\"function\">\n";

  foreach ( $function_list as $func ) {
    if ($_POST['function'] == $func) {
      echo "<option selected>".$func."</option>\n";
    } else {
      echo "<option>".$func."</option>\n";
    }
  }
  echo "</select>\n</p>\n";
/*
    ."<select name=\"function\">\n"
    ."<option>summary</option>\n"
    ."<option>print</option>\n"
    ."<option>add record</option>\n"
    ."<option>plot</option>\n"
    ."<option>create</option>\n"
    ."</select></p>\n";
*/
  echo "<input type=\"submit\" /></form>";

  if (isset($_POST['datafile']) && $_POST['datafile'] == "")
    echo "<p>This program is a gas mileage database and analyzer written in PHP. It is self-contained (has a single source code file). It stores data in a simple text file in HTTP-query format. It allows users to add new records, and add new data files for different vehicles. It creates a backup before a new record is added. It also implements password protection for users to add refueling records. </p>\n";
  
 }

?>

<p>
<span class="footnote">PHP Gas Mileage Database, by Ryan Helinski.
<?php 
list($end_usec, $end_sec) = explode(" ", microtime());

echo "Rendered in: "
  .number_format($end_usec + $end_sec - $begin_usec - $begin_sec,3)
  ." s"; ?></span>
</p>

</body>
</html>
