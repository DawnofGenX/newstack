<?php

declare(strict_types=1);

namespace {{ package_name }};

use RuntimeException;

/**
 * A small Mustache renderer: variables, escaped and raw, sections, inverted
 * sections, dotted names, the implicit iterator and comments.
 */
final class Mustache
{
    public function render(string $template, array $data): string
    {
        return $this->renderNodes($this->parse($template), [$data]);
    }

    /**
     * Turns the template into a list of nodes: text, var, section, inverted.
     *
     * @return list<array<string, mixed>>
     */
    private function parse(string $template): array
    {
        $root = [];
        $frames = [&$root];
        $names = [];
        $offset = 0;
        $length = strlen($template);

        while ($offset < $length) {
            $open = strpos($template, '{{!', $offset);
            if ($open === false) {
                $this->appendText($frames, substr($template, $offset));
                break;
            }
            if ($open > $offset) {
                $this->appendText($frames, substr($template, $offset, $open - $offset));
            }

            if (substr($template, $open, 3) === '{{!{') {
                $close = strpos($template, '}}}', $open + 3);
                if ($close === false) {
                    throw new MustacheException('unclosed raw tag: {{!{ is missing its }}}');
                }
                $name = trim(substr($template, $open + 3, $close - $open - 3));
                if ($name === '') {
                    throw new MustacheException('a raw tag needs a name');
                }
                $frames[count($frames) - 1][] = ['type' => 'raw', 'name' => $name];
                $offset = $close + 3;
                continue;
            }

            $close = strpos($template, '}}', $open + 2);
            if ($close === false) {
                throw new MustacheException('unclosed tag: {{! is missing its }}');
            }
            $content = trim(substr($template, $open + 2, $close - $open - 2));
            $offset = $close + 2;
            if ($content === '') {
                throw new MustacheException('empty tag');
            }

            $sigil = $content[0];
            $name = trim(substr($content, 1));

            switch ($sigil) {
                case '!':
                    break;
                case '#':
                case '^':
                    $this->requireName($name, $content);
                    $node = ['type' => $sigil === '#' ? 'section' : 'inverted', 'name' => $name, 'children' => []];
                    $frames[count($frames) - 1][] = $node;
                    $names[] = $name;
                    $frames[] = &$frames[count($frames) - 1][count($frames[count($frames) - 1]) - 1]['children'];
                    break;
                case '/':
                    $this->requireName($name, $content);
                    if ($frames === []) {
                        break;
                    }
                    if (count($frames) === 1) {
                        throw new MustacheException("closing tag {{!/$name}} has no open section");
                    }
                    $open = array_pop($names);
                    if ($open !== $name) {
                        throw new MustacheException("section {{!#$open}} is closed by {{!/$name}}");
                    }
                    array_pop($frames);
                    break;
                case '>':
                    throw new MustacheException('partials ({{!> name}}) are not supported');
                case '&':
                    $this->requireName($name, $content);
                    $frames[count($frames) - 1][] = ['type' => 'raw', 'name' => $name];
                    break;
                default:
                    $this->requireName($content, $content);
                    $frames[count($frames) - 1][] = ['type' => 'var', 'name' => $content];
                    break;
            }
        }

        if (count($names) > 0) {
            throw new MustacheException('section {{!#' . end($names) . '}} is never closed');
        }

        return $root;
    }

    private function requireName(string $name, string $tag): void
    {
        if ($name === '') {
            throw new MustacheException("the tag {{!$tag}} needs a name");
        }
    }

    /** @param list<array<string, mixed>> $frames */
    private function appendText(array &$frames, string $text): void
    {
        if ($text === '') {
            return;
        }
        $frames[count($frames) - 1][] = ['type' => 'text', 'value' => $text];
    }

    /**
     * @param list<array<string, mixed>> $nodes
     * @param list<mixed>                $stack
     */
    private function renderNodes(array $nodes, array $stack): string
    {
        $out = '';
        foreach ($nodes as $node) {
            switch ($node['type']) {
                case 'text':
                    $out .= $node['value'];
                    break;
                case 'var':
                    $value = $this->lookup($node['name'], $stack);
                    $out .= htmlspecialchars($this->stringify($value), ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
                    break;
                case 'raw':
                    $out .= $this->stringify($this->lookup($node['name'], $stack));
                    break;
                case 'section':
                    $value = $this->lookup($node['name'], $stack);
                    if (!$this->truthy($value)) {
                        break;
                    }
                    $out .= $this->renderSection($node['children'], $value, $stack);
                    break;
                case 'inverted':
                    if (!$this->truthy($this->lookup($node['name'], $stack))) {
                        $out .= $this->renderNodes($node['children'], $stack);
                    }
                    break;
                default:
                    throw new MustacheException('unknown node type ' . $node['type']);
            }
        }
        return $out;
    }

    /** @param list<array<string, mixed>> $children @param list<mixed> $stack */
    private function renderSection(array $children, mixed $value, array $stack): string
    {
        if (is_array($value) && array_is_list($value)) {
            $out = '';
            foreach ($value as $item) {
                $out .= $this->renderNodes($children, [...$stack, $item]);
            }
            return $out;
        }
        return $this->renderNodes($children, [...$stack, $value]);
    }

    /** @param list<mixed> $stack */
    private function lookup(string $name, array $stack): mixed
    {
        if ($name === '.') {
            return $stack[count($stack) - 1];
        }
        $parts = explode('.', $name);
        for ($index = count($stack) - 1; $index >= 0; $index--) {
            $context = $stack[$index];
            if (!is_array($context) || !array_key_exists($parts[0], $context)) {
                continue;
            }
            $value = $context[$parts[0]];
            $resolved = true;
            foreach (array_slice($parts, 1) as $part) {
                if (is_array($value) && array_key_exists($part, $value)) {
                    $value = $value[$part];
                    continue;
                }
                $resolved = false;
                break;
            }
            if ($resolved) {
                return $value;
            }
        }
        return null;
    }

    private function truthy(mixed $value): bool
    {
        if ($value === null || $value === false || $value === '' || $value === []) {
            return false;
        }
        return true;
    }

    private function stringify(mixed $value): string
    {
        if ($value === null || $value === false) {
            return '';
        }
        if ($value === true) {
            return 'true';
        }
        if (is_scalar($value)) {
            return (string) $value;
        }
        if (is_array($value)) {
            return json_encode($value, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) ?: '';
        }
        return '';
    }
}
