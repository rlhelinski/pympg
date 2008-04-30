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

/**
 * Handle creation of HTML alerts to user
 */
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

/*
 * Print a message only in debug mode
 */
function print_debug($message) {
	if (!isset($_GET['debug']))
		return;
	
	echo "<div class='notice'>".$message."</div>\n";
}

/**
 * Create a 2D array from a CSV string
 * lewis [ at t] hcoms [d dot t] co [d dot t] uk
 *
 * @param mixed $data 2D array
 * @param string $delimiter Field delimiter
 * @param string $enclosure Field enclosure
 * @param string $newline Line seperator
 * @return
 */
function parse_csv($data, $delimiter = ',', $enclosure = '"', $newline = "\n"){
    $pos = $last_pos = -1;
    $end = strlen($data);
    $row = 0;
    $quote_open = false;
    $trim_quote = false;

    $return = array();

    // Create a continuous loop
    for ($i = -1;; ++$i){
        ++$pos;
        // Get the positions
        $comma_pos = strpos($data, $delimiter, $pos);
        $quote_pos = strpos($data, $enclosure, $pos);
        $newline_pos = strpos($data, $newline, $pos);

        // Which one comes first?
        $pos = min(($comma_pos === false) ? $end : $comma_pos, ($quote_pos === false) ? $end : $quote_pos, ($newline_pos === false) ? $end : $newline_pos);

        // Cache it
        $char = (isset($data[$pos])) ? $data[$pos] : null;
        $done = ($pos == $end);

        // It it a special character?
        if ($done || $char == $delimiter || $char == $newline){

            // Ignore it as we're still in a quote
            if ($quote_open && !$done){
                continue;
            }

            $length = $pos - ++$last_pos;

            // Is the last thing a quote?
            if ($trim_quote){
                // Well then get rid of it
                --$length;
            }

            // Get all the contents of this column
            $return[$row][] = ($length > 0) ? str_replace($enclosure . $enclosure, $enclosure, substr($data, $last_pos, $length)) : '';

            // And we're done
            if ($done){
                break;
            }

            // Save the last position
            $last_pos = $pos;

            // Next row?
            if ($char == $newline){
                ++$row;
            }

            $trim_quote = false;
        }
        // Our quote?
        else if ($char == $enclosure){

            // Toggle it
            if ($quote_open == false){
                // It's an opening quote
                $quote_open = true;
                $trim_quote = false;

                // Trim this opening quote?
                if ($last_pos + 1 == $pos){
                    ++$last_pos;
                }

            }
            else {
                // It's a closing quote
                $quote_open = false;

                // Trim the last quote?
                $trim_quote = true;
            }

        }

    }

    return $return;
}

// andreas dot damm at maxmachine dot de
function array_search_values( $m_needle, $a_haystack, $b_strict = false){
    return array_intersect_key( $a_haystack, array_flip( array_keys( $a_haystack, $m_needle, $b_strict)));
}

function table_find_record($table, $searchField, $fieldValue) 
{
	$i = 0;
	while ($i < count($table)) {
		if ($table[$i][$searchField] == $fieldValue) {
			return $i;
		}
		$i++;
	}
	
	return false; // not found
}
    

?>
