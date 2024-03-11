<?php

$text_art = '
                ▒▒▒▒▒▒▒█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
                ▒▒▒▒▒▒▒█░▒▒▒▒▒▒▒▓▒▒▓▒▒▒▒▒▒▒░█
                ▒▒▒▒▒▒▒█░▒▒▓▒▒▒▒▒▒▒▒▒▄▄▒▓▒▒░█░▄▄
                ▒▒▄▀▀▄▄█░▒▒▒▒▒▒▓▒▒▒▒█░░▀▄▄▄▄▄▀░░█
                ▒▒█░░░░█░▒▒▒▒▒▒▒▒▒▒▒█░░░░░░░░░░░█  <lets go!
                ▒▒▒▀▀▄▄█░▒▒▒▒▓▒▒▒▓▒█░░░█▒░░░░█▒░░█
                ▒▒▒▒▒▒▒█░▒▓▒▒▒▒▓▒▒▒█░░░░░░░▀░░░░░█
                ▒▒▒▒▒▄▄█░▒▒▒▓▒▒▒▒▒▒▒█░░█▄▄█▄▄█░░█
                ▒▒▒▒█░░░█▄▄▄▄▄▄▄▄▄▄█░█▄▄▄▄▄▄▄▄▄█
                ▒▒▒▒█▄▄█░░█▄▄█░░░░░░█▄▄█░░█▄▄█
';

echo  $text_art . PHP_EOL;


$red = "\033[0;31m";
$green = "\033[0;32m";
$reset = "\033[0m"; // Reset to default color
$inDepthScan = in_array('--in-depth', $argv);
$url = null;
$htmlComments = [];
$jsComments = [];
$links = [];

// Round about way of getting the url. Probably a better way to do this.
if (!empty($argv[1])) {
    $url = $argv[1];
} else {
    exit ("$red missing url $reset" . PHP_EOL);
}

if ($primaryUrlContent = file_get_contents($url)) {

    $extracted = extractComments($primaryUrlContent);
    $htmlComments = $extracted['html'] ?? null;
    $jsComments = $extracted['js'] ?? null;
    $lines = explode("\n", $primaryUrlContent);

    if ($inDepthScan) {
        foreach ($lines as $line) {
            if (preg_match_all('/<a\s+[^>]*href\s*=\s*["\']?([^"\'>]*)/i', $line, $matches)) {
                foreach ($matches[1] as $href) {
                    if (!str_contains($href, '://')) {
                        $href = $url . '/' . $href;
                    }
                    $links[] = $href;
                }
            }
        }

        foreach ($links as $link) {
            if ($secondaryUrlContent = file_get_contents($link)) {
                $extracted = extractComments($secondaryUrlContent, $link);
                $extracted = array_merge($htmlComments ?? [], $extracted['html'] ?? []);
                $jsComments = array_merge($jsComments ?? [], $extracted['js'] ?? []);
            } else {
                echo "$red something went wrong with retrieving the url content from $link $reset" . PHP_EOL;
            }
        }
    }

}  else {
    exit ("$red something went wrong with retrieving the url content $reset" . PHP_EOL);
}

if (!empty($htmlComments)) {
    echo "$red Comments discovered (html) $reset" . PHP_EOL;
    foreach ($htmlComments as $lineNumber => $comment) {
        echo "[$lineNumber] " . $comment  . PHP_EOL;
    }
}

if (!empty($htmlComments)) {
    echo "$red Comments discovered (JS) $reset"  . PHP_EOL;
    foreach ($jsComments as $lineNumber => $comment) {
        echo "[$lineNumber] " . $comment  . PHP_EOL;
    }
}
$prohibitedFindings = scanForProhibited($htmlComments, $jsComments);

if (!empty($prohibitedFindings)) {
    echo "$red ********* PROHIBITED COMMENTS DISCOVERED *************** $reset" . PHP_EOL;
    foreach ($prohibitedFindings as $lineNumber => $value) {
        echo $red .'[' . $lineNumber . ']'  . $value . PHP_EOL;
    }
}

function scanForProhibited(array $commentsHtml, array $commentsJs): array
{
    $return = [];

    $prohibited = json_decode(file_get_contents('prohib.json'), true);

    foreach ($prohibited as $value) {
        foreach ($commentsHtml as $line => $comment) {
            if (str_contains(strtolower($comment), strtolower($value))) {
                $return[$line] = "PROHIBITED VALUE ($value) in comment $comment";
            }
        }

        foreach ($commentsJs as $line => $comment) {
            if (str_contains(strtolower($comment), strtolower($value))) {
                $return[$line] = "PROHIBITED VALUE ($value) in comment $comment";
            }
        }
    }

    return $return;
}

function extractComments(string $content, string $additionalLocation = ''): array
{
    $return = [];
    $lines = explode("\n", $content);

    // Check for HTML comments and store line numbers
    foreach ($lines as $lineNumber => $line) {
        if (preg_match('/<!--(.*?)-->/s', $line, $matches)) {
            $return['html'][$lineNumber + 1] =
                (!empty($additionalLocation) ? '[' . $additionalLocation . ']' : '') . $matches[0];
        }
    }


    preg_match_all('/<script\b[^>]*>(.*?)<\/script>/is', $content, $matches);
    $scripts = $matches[1];
    foreach ($scripts as $lineNumber => $line) {
        if (preg_match('/\/\/(.*?)$|\/\*(.*?)\*\//s', $line, $matches)) {
            $return['js'][$lineNumber + 1] =
                (!empty($additionalLocation) ? '[' . $additionalLocation . ']' : '') . $matches[0];
        }
    }

    return $return;
}