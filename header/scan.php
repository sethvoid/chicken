<?php
//types of value
/**
 * value = strictsomething: value
 * multivalue = something: value1, value2, value3
 * matching-type: contain should-not-contain, should-not-be-set
 */
$text_art = '
                ▒▒▒▒▒▒▒█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
                ▒▒▒▒▒▒▒█░▒▒▒▒▒▒▒▓▒▒▓▒▒▒▒▒▒▒░█
                ▒▒▒▒▒▒▒█░▒▒▓▒▒▒▒▒▒▒▒▒▄▄▒▓▒▒░█░▄▄
                ▒▒▄▀▀▄▄█░▒▒▒▒▒▒▓▒▒▒▒█░░▀▄▄▄▄▄▀░░█
                ▒▒█░░░░█░▒▒▒▒▒▒▒▒▒▒▒█░░░░░░░░░░░█  <HOLD ON! HERE WE GO!
                ▒▒▒▀▀▄▄█░▒▒▒▒▓▒▒▒▓▒█░░░█▒░░░░█▒░░█
                ▒▒▒▒▒▒▒█░▒▓▒▒▒▒▓▒▒▒█░░░░░░░▀░░░░░█
                ▒▒▒▒▒▄▄█░▒▒▒▓▒▒▒▒▒▒▒█░░█▄▄█▄▄█░░█
                ▒▒▒▒█░░░█▄▄▄▄▄▄▄▄▄▄█░█▄▄▄▄▄▄▄▄▄█
                ▒▒▒▒█▄▄█░░█▄▄█░░░░░░█▄▄█░░█▄▄█
';

echo  $text_art . PHP_EOL;
$target = $argv[1];
$configFile = $argv[2];
$red = "\033[0;31m";
$green = "\033[0;32m";
$reset = "\033[0m"; // Reset to default color

function curReq($target)
{
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $target);
    curl_setopt($ch, CURLOPT_HEADER, true);
    curl_setopt($ch, CURLOPT_NOBODY, true);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    $response = curl_exec($ch);

    if ($response === false) {
        echo 'cURL error: ' . curl_error($ch);
        exit();
    }
    curl_close($ch);

    return $response;
}

$response = curReq($target);
$headerContentArray = [];
foreach(preg_split("/((\r?\n)|(\r\n?))/", $response) as $line){
    if (str_contains($line, ':')) {
        $headerArray = explode(':', $line);
        if (isset($headerArray[0]) && isset($headerArray[1])) {
            $headerArray[0] = strtolower($headerArray[0]);
            $headerArray[1] = strtolower($headerArray[1]);
            $multiValues = null;
            $singleValueKeyPair = null;
            if (str_contains($headerArray[1], ',') || str_contains($headerArray[1], ';')) {
                $headerArray[1] = preg_replace('/\s+/', '', $headerArray[1]);
                $splitChar = str_contains($headerArray[1], ',') ? ',' : ';';
                $multiValues = explode($splitChar, $headerArray[1]);
            }

            if (!empty($multiValues)) {
                foreach ($multiValues as $value) {
                    $headerContentArray[$headerArray[0]][] = $value;
                }
            } else {
                $headerContentArray[$headerArray[0]] = preg_replace('/\s+/', '', $headerArray[1]);
            }
        }
    }
}

$configArray = json_decode(file_get_contents($configFile), true);
$pass  = [];
$fail = [];
foreach ($configArray as $testName => $test) {
    $test['key'] = strtolower($test['key']);

    // Key shouldn't exist logic.
    if ($test['matching-type'] == 'should-not-be-set') {
        if (isset($headerContentArray[$test['key']])) {
            $fail[] = [
                'name' => $test['key'],
                'result' => 'Prohibited header set ' . $test['key'],
                'help_link' => $test['link'] ?? ''
            ];
            continue;
        } else {
            $pass[] = [
                'name' => $test['key'],
                'result' => 'Header ' . $test['key'] . ' does not contain prohibited header',
                'help_link' => $test['link'] ?? ''
            ];
            continue;
        }
    }

    // Check key does exist logic
    if (!isset($headerContentArray[$test['key']])) {
        $fail[] = [
            'name' => $test['key'],
            'result' => 'Header is not set.',
            'help_link' => $test['link']
        ];
        continue;
    }

    if ($test['type'] == 'value') {
        $headerCont = $headerContentArray[$test['key']];
        if (is_array($headerCont)) {
            $headerCont = implode(' ', $headerCont);
        }
        if ($test['matching-type'] == 'should-not-contain') {
            if (str_contains($headerCont, strtolower($test['value']))) {
                $fail[] = [
                    'name' => $test['key'],
                    'result' => 'Header ' . $test['key'] . ' contains invalid value ' .$test['value'],
                    'help_link' => $test['link'] ?? ''
                ];
                continue;
            }
        } else {
            if (str_contains($headerCont, strtolower($test['value']))) {
                $pass[] = [
                    'name' => $test['key'],
                    'result' => 'Header ' . $test['key'] . ' contains correct value ' .$test['value'],
                    'help_link' => $test['link'] ?? ''
                ];
                continue;
            }
        }

        $fail[] = [
            'name' => $test['key'],
            'result' => 'Header ' . $test['key'] . ' contains invalid value ' .$test['value'],
            'help_link' => $test['link'] ?? ''
        ];
    } else if ($test['type'] == 'multivalue') {
        $passCount = 0;
        $count = count($test['value']);
        foreach($test['value'] as $val) {
            $val = strtolower($val);
            if ($test['matching-type'] == 'should-not-contain') {
                if (in_array($val, $headerContentArray[$test['key']])) {
                    $fail[] = [
                        'name' => $test['key'],
                        'result' => 'Header ' . $test['key'] . ' contains invalid value ' .$val,
                        'help_link' => $test['link'] ?? ''
                    ];
                    continue;
                }
                $passCount ++;
            } else {
                if (is_array($headerContentArray[$test['key']])) {
                    if (in_array($val, $headerContentArray[$test['key']])) {
                        $pass[] = [
                            'name' => $test['key'],
                            'result' => 'Header ' . $test['key'] . ' contains correct value ' .$val,
                            'help_link' => $test['link'] ?? ''
                        ];
                        $passCount++;
                    }
                } else {
                    if (str_contains($val, $headerContentArray[$test['key']])) {
                        $pass[] = [
                            'name' => $test['key'],
                            'result' => 'Header ' . $test['key'] . ' contains correct value ' .$val,
                            'help_link' => $test['link'] ?? ''
                        ];
                        $passCount++;
                    }
                }
            }
        }

        if ($passCount < $count) {
            $fail[] = [
                'name' => $test['key'],
                'result' => 'Header ' . $test['key'] . ' is missing some values ',
                'help_link' => $test['link'] ?? ''
            ];
        }
    }
}
$fileName = date('His-d-m-Y') . '-results.log';
$log = "SCRIPT:,scan.php,,";
$logFile = file_put_contents($fileName, $log.PHP_EOL , FILE_APPEND | LOCK_EX);
$log = "TARGET:,'.$target.',,";
$logFile = file_put_contents($fileName, $log.PHP_EOL , FILE_APPEND | LOCK_EX);
$log = "result,header-name,error,information-link";
$logFile = file_put_contents($fileName, $log.PHP_EOL , FILE_APPEND | LOCK_EX);

echo $green . ' ------------------------------------ PASS --------------------------------------- ' . $reset . PHP_EOL;
foreach ($pass as $p) {
    echo  $green .  $p['name'] . ' ' . $p['result'] . $reset . PHP_EOL;
    $log = 'PASS,' . $p['name'] . ',"' . $p['result'] . '","' . $p['help_link'] . '"';
    $logFile = file_put_contents($fileName, $log.PHP_EOL , FILE_APPEND | LOCK_EX);
}
echo PHP_EOL;

if(!empty($fail)) {
    echo $red . ' ------------------------------------ FAIL --------------------------------------- ' . $reset . PHP_EOL;
    foreach ($fail as $f) {
        echo $red . $f['name'] . ' ' . $f['result'] . $reset . PHP_EOL;
        $log = 'FAIL,' . $f['name'] . ',"' . $f['result'] . '","' . $f['help_link'] . '"';
        $logFile = file_put_contents($fileName, $log.PHP_EOL , FILE_APPEND | LOCK_EX);
    }
}

if (in_array('-vvv', $argv)) {
    print_r($headerContentArray);
}