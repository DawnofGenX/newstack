<?php

declare(strict_types=1);

namespace {{ package_name }}\Tests;

use {{ package_name }}\Mustache;
use {{ package_name }}\MustacheException;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

final class MustacheTest extends TestCase
{
    private Mustache $mustache;

    protected function setUp(): void
    {
        $this->mustache = new Mustache();
    }

    /** @return iterable<string, array{string, array<string, mixed>, string}> */
    public static function renders(): iterable
    {
        yield 'plain text' => ['hello', [], 'hello'];
        yield 'variable' => ['hi {{!name}}', ['name' => 'ada'], 'hi ada'];
        yield 'missing variable' => ['[{{!name}}]', [], '[]'];
        yield 'escaping' => ['{{!html}}', ['html' => '<b>&"'], '&lt;b&gt;&amp;&quot;'];
        yield 'triple braces stay raw' => ['{{!{html}}}', ['html' => '<b>'], '<b>'];
        yield 'ampersand stays raw' => ['{{!&html}}', ['html' => '<b>'], '<b>'];
        yield 'dotted name' => ['{{!user.name}}', ['user' => ['name' => 'ada']], 'ada'];
        yield 'numbers and booleans' => ['{{!n}}/{{!yes}}', ['n' => 3, 'yes' => true], '3/true'];
        yield 'comment' => ['a{{! ignore me }}b', [], 'ab'];
        yield 'list section' => [
            '{{!#items}}<{{!.}}>{{!/items}}',
            ['items' => ['a', 'b']],
            '<a><b>',
        ];
        yield 'list of maps' => [
            '{{!#rows}}{{!name}}:{{!score}} {{!/rows}}',
            ['rows' => [['name' => 'a', 'score' => 1], ['name' => 'b', 'score' => 2]]],
            'a:1 b:2 ',
        ];
        yield 'map section' => [
            '{{!#user}}{{!name}}{{!/user}}',
            ['user' => ['name' => 'ada']],
            'ada',
        ];
        yield 'empty list hides the section' => [
            '{{!#items}}x{{!/items}}done',
            ['items' => []],
            'done',
        ];
        yield 'inverted section' => [
            '{{!^items}}none{{!/items}}',
            ['items' => []],
            'none',
        ];
        yield 'inverted section over a value' => [
            '{{!^name}}anonymous{{!/name}}',
            ['name' => 'ada'],
            '',
        ];
        yield 'nested sections' => [
            '{{!#outer}}{{!#inner}}{{!value}}{{!/inner}}{{!/outer}}',
            ['outer' => ['inner' => ['value' => 'deep']]],
            'deep',
        ];
        yield 'parent context is visible in a section' => [
            '{{!#items}}{{!prefix}}{{!.}} {{!/items}}',
            ['prefix' => '#', 'items' => ['a', 'b']],
            '#a #b ',
        ];
    }

    /** @param array<string, mixed> $data */
    #[DataProvider('renders')]
    public function testRenders(string $template, array $data, string $expected): void
    {
        self::assertSame($expected, $this->mustache->render($template, $data));
    }

    public function testUnclosedSectionIsReported(): void
    {
        $this->expectException(MustacheException::class);
        $this->expectExceptionMessage('is never closed');
        $this->mustache->render('{{!#items}}x', []);
    }

    public function testMismatchedCloseIsReported(): void
    {
        $this->expectException(MustacheException::class);
        $this->expectExceptionMessage('is closed by');
        $this->mustache->render('{{!#a}}x{{!/b}}', []);
    }

    public function testClosingWithoutOpeningIsReported(): void
    {
        $this->expectException(MustacheException::class);
        $this->mustache->render('{{!/a}}', []);
    }

    public function testUnclosedTagIsReported(): void
    {
        $this->expectException(MustacheException::class);
        $this->mustache->render('{{!name', []);
    }

    public function testPartialsAreRefused(): void
    {
        $this->expectException(MustacheException::class);
        $this->expectExceptionMessage('partials');
        $this->mustache->render('{{!> header}}', []);
    }

    public function testMultilineTemplatesKeepTheirNewlines(): void
    {
        $template = "{{!#people}}- {{!name}}\n{{!/people}}";
        $rendered = $this->mustache->render($template, ['people' => [['name' => 'ada'], ['name' => 'bo']]]);
        self::assertSame("- ada\n- bo\n", $rendered);
    }
}
