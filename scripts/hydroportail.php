#!/usr/bin/php
<?php
  if ( count($_SERVER['argv']) < 5 ) {
    echo 'Syntax: '.$_SERVER['argv'][0]." <STATION> <BEGIN> <END> <TYPE> [> myfile.csv]\n";
    echo "  <BEGIN> & <END>: dates DD/MM/AAAA\n";
    echo "  <TYPE>: QmnJ, HINnJ, HIXnJ ... cf. website\n";
    die(255);
  }

  $station = urlencode($_SERVER['argv'][1]); // ex: L250161001
  $start = urlencode($_SERVER['argv'][2]); // format JJ/MM/AAAA
  $stop = urlencode($_SERVER['argv'][3]); // format JJ/MM/AAAA
  $type = urlencode($_SERVER['argv'][4]); // QmnJ=débit moyen sur 1 jour, HINnJ=hauteur instantanée minimal n journalière, HIXnJ=idem maximal
  $debug = array_key_exists(5, $_SERVER['argv']) && $_SERVER['argv'][5] == "debug";

  if ( $debug ) {
    error_log(print_r($_SERVER['argv'], true));
  }

  $url = "https://www.hydro.eaufrance.fr/stationhydro/ajax/$station/series?hydro_series%5BstartAt%5D=$start&hydro_series%5BendAt%5D=$stop&hydro_series%5BvariableType%5D=daily_variable&hydro_series%5BdailyVariable%5D=$type&hydro_series%5Bstep%5D=1&hydro_series%5Brolling%5D=1&hydro_series%5BstatusData%5D=pre_validated_and_validated";
  if ( $debug ) {
    error_log($url);
  }
  
  echo $url;

  $raw = file_get_contents($url);
  if ( $debug ) {
    error_log($raw);
  }
  $data = json_decode($raw, true);

  $csv_prefix = [$data['series']['code'], $data['series']['metric'], $data['timezone']];
  $csv = $data['series']['data'];

  $out = fopen('php://output', 'w');
  foreach ( $csv as $i => $line ) {
    fputcsv($out, array_merge($csv_prefix, $line));
  }
  fclose($out);
