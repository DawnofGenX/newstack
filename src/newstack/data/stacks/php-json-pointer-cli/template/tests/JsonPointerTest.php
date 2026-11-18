<?php

declare(strict_types=1);

namespace {{ package_name }}\Tests;

use PHPUnit\Framework\TestCase;
use {{ package_name }}\JsonPointer;
use {{ package_name }}\JsonPointerException;

final class JsonPointerTest extends TestCase
{
    private function document(): array
    {
        return [
            'name' => 'demo',
            'tags' => ['a', 'b'],
            'nested' => ['list' => [['id' => 1], ['id' => 2]]],
            'a/b' => ['m~n' => 7],
        ];
    }

    public function testEmptyPointerIsTheWholeDocument(): void
    {
        $document = $this->document();
        self::assertSame($document, JsonPointer::get($document, ''));
    }

    public function testReadsNestedValues(): void
    {
        $document = $this->document();
        self::assertSame('demo', JsonPointer::get($document, '/name'));
        self::assertSame('b', JsonPointer::get($document, '/tags/1'));
        self::assertSame(2, JsonPointer::get($document, '/nested/list/1/id'));
    }

    public function testDecodesEscapedTokens(): void
    {
        $document = $this->document();
        self::assertSame(7, JsonPointer::get($document, '/a~1b/m~0n'));
        self::assertSame(['a/b', 'm~n'], JsonPointer::tokens('/a~1b/m~0n'));
        self::assertSame('a~b/c', JsonPointer::unescape('a~0b~1c'));
        self::assertSame('a~0b~1c', JsonPointer::escape('a~b/c'));
    }

    public function testSetReplacesAndInserts(): void
    {
        $document = $this->document();
        JsonPointer::set($document, '/name', 'renamed');
        self::assertSame('renamed', $document['name']);

        JsonPointer::set($document, '/nested/extra', true);
        self::assertTrue($document['nested']['extra']);

        JsonPointer::set($document, '/tags/-', 'c');
        self::assertSame(['a', 'b', 'c'], $document['tags']);

        JsonPointer::set($document, '/fresh/deep', 1);
        self::assertSame(1, $document['fresh']['deep']);
    }

    public function testSetOnTheRootReplacesEverything(): void
    {
        $document = $this->document();
        JsonPointer::set($document, '', ['only' => 1]);
        self::assertSame(['only' => 1], $document);
    }

    public function testRemoveDeletesAndReturnsTheValue(): void
    {
        $document = $this->document();
        self::assertSame('b', JsonPointer::remove($document, '/tags/1'));
        self::assertSame(['a'], $document['tags']);
        self::assertSame('demo', JsonPointer::remove($document, '/name'));
        self::assertArrayNotHasKey('name', $document);
    }

    public function testMissingPathsAreReported(): void
    {
        $document = $this->document();
        $error = null;
        try {
            JsonPointer::get($document, '/nope');
        } catch (JsonPointerException $caught) {
            $error = $caught->getMessage();
        }
        self::assertSame("no such member 'nope' at (document root)", $error);

        $this->expectException(JsonPointerException::class);
        JsonPointer::get($document, '/tags/9');
    }

    public function testRejectsMalformedPointers(): void
    {
        $this->expectException(JsonPointerException::class);
        $this->expectExceptionMessage("must be empty or start with '/'");
        JsonPointer::tokens('name');
    }

    public function testCannotStepIntoAScalar(): void
    {
        $this->expectException(JsonPointerException::class);
        $this->expectExceptionMessage('cannot step into');
        JsonPointer::get($this->document(), '/name/deeper');
    }

    public function testHasReportsPresence(): void
    {
        $document = $this->document();
        self::assertTrue(JsonPointer::exists($document, '/tags/0'));
        self::assertFalse(JsonPointer::exists($document, '/tags/0/x'));
        self::assertFalse(JsonPointer::exists($document, '/missing'));
    }
}
