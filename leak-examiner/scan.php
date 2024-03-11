<?php
$inDepthScan = in_array('--in-depth', $argv);
$url = null;

if (in_array('--url', $argv)) {
    $keypoint = 0;
    foreach ($argv as $key => $value) {
        if ($value == '--url') {
            $keypoint = $keypoint + 1;
        }
    }

    if ($keypoint > 0) {
        $url = $argv[$keypoint];
    }
}
