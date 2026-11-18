<?php
declare(strict_types=1);

namespace {{ package_name }}\Tests;

use {{ package_name }}\Sanitizer;
use PHPUnit\Framework\TestCase;

final class SanitizerTest extends TestCase
{
    private Sanitizer $sanitizer;

    protected function setUp(): void
    {
        $this->sanitizer = new Sanitizer();
    }

    public function testKeepsAllowedMarkup(): void
    {
        $this->assertSame('<p>Hello <strong>world</strong></p>', $this->sanitizer->sanitize('<p>Hello <strong>world</strong></p>'));
    }

    public function testRemovesScriptWithItsContent(): void
    {
        $out = $this->sanitizer->sanitize('<p>safe</p><script>alert("x")</script>');
        $this->assertSame('<p>safe</p>', $out);
        $this->assertStringNotContainsString('alert', $out);
    }

    public function testRemovesInlineEventHandlers(): void
    {
        $out = $this->sanitizer->sanitize('<p onclick="steal()">text</p>');
        $this->assertSame('<p>text</p>', $out);
    }

    public function testStripsJavascriptHrefButKeepsTheLink(): void
    {
        $out = $this->sanitizer->sanitize('<a href="javascript:alert(1)">click</a>');
        $this->assertSame('<a>click</a>', $out);
    }

    public function testKeepsSafeHref(): void
    {
        $out = $this->sanitizer->sanitize('<a href="https://example.com" title="home">site</a>');
        $this->assertSame('<a href="https://example.com" title="home">site</a>', $out);
    }

    public function testTargetBlankGetsNoopener(): void
    {
        $out = $this->sanitizer->sanitize('<a href="https://example.com" target="_blank">x</a>');
        $this->assertStringContainsString('rel="noopener noreferrer"', $out);
    }

    public function testUnknownTagIsUnwrapped(): void
    {
        $this->assertSame('plain', $this->sanitizer->sanitize('<marquee>plain</marquee>'));
    }

    public function testCommentsAreDropped(): void
    {
        $this->assertSame('<p>hi</p>', $this->sanitizer->sanitize('<p>hi</p><!-- tracker -->'));
    }

    public function testEmptyInputStaysEmpty(): void
    {
        $this->assertSame('', $this->sanitizer->sanitize('   '));
    }

    public function testStyleTagIsDropped(): void
    {
        $out = $this->sanitizer->sanitize('<style>body{display:none}</style><p>ok</p>');
        $this->assertSame('<p>ok</p>', $out);
    }
}
