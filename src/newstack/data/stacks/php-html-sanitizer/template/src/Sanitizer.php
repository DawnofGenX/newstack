<?php
declare(strict_types=1);

namespace {{ package_name }};

use DOMDocument;
use DOMElement;
use DOMNode;

// php-html-sanitizer
final class Sanitizer
{
    /** @var array<string, list<string>> tag => allowed attributes */
    public const ALLOWED = [
        'a' => ['href', 'title', 'target'],
        'b' => [],
        'blockquote' => [],
        'br' => [],
        'code' => [],
        'em' => [],
        'h1' => [],
        'h2' => [],
        'h3' => [],
        'h4' => [],
        'hr' => [],
        'i' => [],
        'li' => [],
        'ol' => [],
        'p' => [],
        'pre' => [],
        'span' => [],
        'strong' => [],
        'u' => [],
        'ul' => [],
    ];

    /** Tags removed together with everything inside them. */
    public const DROP_WITH_CONTENT = ['script', 'style', 'iframe', 'object', 'embed', 'noscript', 'template'];

    /** Schemes that must never appear in an href. */
    private const BAD_SCHEME = '/^\s*(javascript|vbscript|data)\s*:/i';

    public function sanitize(string $html): string
    {
        if (trim($html) === '') {
            return '';
        }
        $document = new DOMDocument('1.0', 'UTF-8');
        $previous = libxml_use_internal_errors(true);
        $document->loadHTML(
            '<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>' . $html . '</body></html>',
            LIBXML_NONET
        );
        libxml_clear_errors();
        libxml_use_internal_errors($previous);

        $body = $document->getElementsByTagName('body')->item(0);
        if ($body === null) {
            return '';
        }

        $this->clean($body);

        $out = '';
        foreach ($body->childNodes as $child) {
            $out .= $document->saveHTML($child);
        }
        return trim($out);
    }

    private function clean(DOMNode $node): void
    {
        // Snapshot first: we mutate the live child list while iterating.
        $children = [];
        foreach ($node->childNodes as $child) {
            $children[] = $child;
        }

        foreach ($children as $child) {
            if ($child instanceof DOMElement) {
                $tag = strtolower($child->tagName);
                if (in_array($tag, self::DROP_WITH_CONTENT, true)) {
                    $node->removeChild($child);
                    continue;
                }
                if (!array_key_exists($tag, self::ALLOWED)) {
                    // Unknown tag: keep the text, drop the tag.
                    $this->clean($child);
                    while ($child->firstChild !== null) {
                        $node->insertBefore($child->firstChild, $child);
                    }
                    $node->removeChild($child);
                    continue;
                }
                $this->cleanAttributes($child, $tag);
            } elseif ($child->nodeType === XML_COMMENT_NODE) {
                $node->removeChild($child);
                continue;
            }
            $this->clean($child);
        }
    }

    private function cleanAttributes(DOMElement $element, string $tag): void
    {
        $allowed = self::ALLOWED[$tag];
        $drop = [];
        foreach (iterator_to_array($element->attributes ?? []) as $attribute) {
            $name = strtolower($attribute->nodeName);
            if (!in_array($name, $allowed, true)) {
                $drop[] = $name;
            }
        }
        foreach ($drop as $name) {
            $element->removeAttribute($name);
        }

        if ($tag === 'a') {
            $href = $element->getAttribute('href');
            if ($href !== '' && preg_match(self::BAD_SCHEME, $href) === 1) {
                $element->removeAttribute('href');
            }
            if (strtolower($element->getAttribute('target')) === '_blank') {
                $element->setAttribute('rel', 'noopener noreferrer');
            }
        }
    }
}
