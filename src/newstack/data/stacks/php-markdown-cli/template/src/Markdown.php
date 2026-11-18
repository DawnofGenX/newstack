<?php
declare(strict_types=1);

// php-markdown-cli

namespace {{ package_name }};

final class Markdown
{
    public static function toHtml(string $md): string
    {
        $lines = preg_split('/\r\n|\r|\n/', $md);
        if ($lines === false) {
            $lines = [];
        }
        $html = '';
        $inCode = false;
        $codeBuf = '';
        $inList = false;
        $para = [];
        foreach ($lines as $line) {
            if (str_starts_with(trim($line), '```')) {
                if ($inCode) {
                    $html .= "<pre><code>" . htmlspecialchars($codeBuf, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8') . "</code></pre>\n";
                    $codeBuf = '';
                    $inCode = false;
                } else {
                    $html .= self::flushParagraph($para);
                    $para = [];
                    if ($inList) {
                        $html .= "</ul>\n";
                        $inList = false;
                    }
                    $inCode = true;
                }
                continue;
            }
            if ($inCode) {
                $codeBuf .= $line . "\n";
                continue;
            }
            $trimmed = trim($line);
            if ($trimmed === '') {
                $html .= self::flushParagraph($para);
                $para = [];
                if ($inList) {
                    $html .= "</ul>\n";
                    $inList = false;
                }
                continue;
            }
            if (preg_match('/^(#{1,6})\s+(.*)$/', $trimmed, $m) === 1) {
                $html .= self::flushParagraph($para);
                $para = [];
                if ($inList) {
                    $html .= "</ul>\n";
                    $inList = false;
                }
                $level = strlen($m[1]);
                $html .= "<h{$level}>" . self::inline($m[2]) . "</h{$level}>\n";
                continue;
            }
            if (preg_match('/^[-*]\s+(.*)$/', $trimmed, $m) === 1) {
                $html .= self::flushParagraph($para);
                $para = [];
                if (!$inList) {
                    $html .= "<ul>\n";
                    $inList = true;
                }
                $html .= "<li>" . self::inline($m[1]) . "</li>\n";
                continue;
            }
            $para[] = $trimmed;
        }
        $html .= self::flushParagraph($para);
        if ($inList) {
            $html .= "</ul>\n";
        }
        if ($inCode) {
            $html .= "<pre><code>" . htmlspecialchars($codeBuf, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8') . "</code></pre>\n";
        }
        return $html;
    }

    private static function flushParagraph(array $para): string
    {
        if ($para === []) {
            return '';
        }
        return "<p>" . self::inline(implode(' ', $para)) . "</p>\n";
    }

    private static function inline(string $text): string
    {
        $text = htmlspecialchars($text, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
        $text = preg_replace('/`([^`]+)`/', '<code>$1</code>', $text) ?? $text;
        $text = preg_replace('/\*\*(.+?)\*\*/s', '<strong>$1</strong>', $text) ?? $text;
        $text = preg_replace('/\*(.+?)\*/s', '<em>$1</em>', $text) ?? $text;
        $text = preg_replace('/\[([^\]]+)\]\(([^)]+)\)/', '<a href="$2">$1</a>', $text) ?? $text;
        return $text;
    }
}
