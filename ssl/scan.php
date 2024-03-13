<?php
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
$verifyPeer = in_array('--verify-peer', $argv);
$verboseOutput = in_array('--vvv', $argv);
$red = "\033[0;31m";
$green = "\033[0;32m";
$reset = "\033[0m"; // Reset to default color

function curlReq(string $url, bool $verifyPeer): array
{
    if (str_contains($url, '://')) {
        $url = str_replace(['https://', 'http://', '://'], '', $url);
    }

    $context = stream_context_create([
        "ssl" => [
            "capture_peer_cert" => true,
            "verify_peer" => $verifyPeer
        ]
    ]);

    $stream = stream_socket_client("ssl://$url:443",
        $errno,
        $errstr,
        30,
        STREAM_CLIENT_CONNECT,
        $context
    );

    $sslContext = stream_context_get_params($stream);
    $sslCertificate = $sslContext["options"]["ssl"]["peer_certificate"];
    $sslCertDetails = openssl_x509_parse($sslCertificate);

    fclose($stream);

    return $sslCertDetails;
}

if (!isset($argv[1])) {
    exit($red . 'Missing argument <url>' . $reset . PHP_EOL);
}

$sslCertificateDetails = curlReq($argv[1], $verifyPeer);
$valid = $sslCertificateDetails['validFrom_time_t'];
$expires = $sslCertificateDetails['validTo_time_t'];
$issuer = $sslCertificateDetails['issuer']; // C, O, CN
if ($verboseOutput) {
    print_r($sslCertificateDetails);
}

$name = explode('=', $sslCertificateDetails['name']);

$json = [
    'name' => $name[1] ?? $sslCertificateDetails['name'],
    'expires' => date('h:i:s d-m-Y', $expires),
    'issued' => date('h:i:s d-m-Y', $valid),
    'primary_issuer' => $issuer['C'],
    'Secondary_issuer' => $issuer['O'],
    'CA_issuer' => $issuer['CN']
];


if (file_put_contents('report-' . $name[1] ?? $sslCertificateDetails['name'] . '.txt', json_encode($json))) {
    echo $green . PHP_EOL . 'Successfully saved to: ' . $name[1] ?? $sslCertificateDetails['name'] . '.txt' . $reset;
}

if (time() > $expires) {
    echo $red . PHP_EOL . 'SSL cert has expired' . $reset;
} else {
    echo $green . PHP_EOL .'SSL is valid' . $reset;
}

echo PHP_EOL;