<?php
declare(strict_types=1);

namespace {{ package_name }}\Tests;

use {{ package_name }}\Markdown;
use PHPUnit\Framework\TestCase;

final class MarkdownTest extends TestCase
{
    public function testHeading(): void
    {
        $html = Markdown::toHtml("# Hello\n");
        $this->assertStringContainsString('<h1>Hello</h1>', $html);
    }

    public function testBoldAndItalic(): void
    {
        $html = Markdown::toHtml("This is **bold** and *italic*.\n");
        $this->assertStringContainsString('<strong>bold</strong>', $html);
        $this->assertStringContainsString('<em>italic</em>', $html);
    }

    public function testCodeAndLink(): void
    {
        $html = Markdown::toHtml("Use `code` and [link](https://example.com).\n");
        $this->assertStringContainsString('<code>code</code>', $html);
        $this->assertStringContainsString('<a href="https://example.com">link</a>', $html);
    }

    public function testList(): void
    {
        $html = Markdown::toHtml("- one\n- two\n");
        $this->assertStringContainsString('<ul>', $html);
        $this->assertStringContainsString('<li>one</li>', $html);
        $this->assertStringContainsString('<li>two</li>', $html);
    }

    public function testCodeBlock(): void
    {
        $html = Markdown::toHtml("```\n<x>\n```\n");
        $this->assertStringContainsString('<pre><code>&lt;x&gt;', $html);
    }

    public function testParagraph(): void
    {
        $html = Markdown::toHtml("Hello world\n");
        $this->assertStringContainsString('<p>Hello world</p>', $html);
    }
}
