<?php

declare(strict_types=1);

namespace {{ package_name }}\Tests;

use {{ package_name }}\Uri;
use InvalidArgumentException;
use PHPUnit\Framework\TestCase;

final class UriTest extends TestCase
{
    public function testParseSplitsEveryComponent(): void
    {
        $parts = Uri::parse('https://user:secret@example.com:8443/a/b?x=1&y=2#top');

        self::assertSame('https', $parts['scheme']);
        self::assertSame('user', $parts['user']);
        self::assertSame('secret', $parts['password']);
        self::assertSame('example.com', $parts['host']);
        self::assertSame(8443, $parts['port']);
        self::assertSame('/a/b', $parts['path']);
        self::assertSame('x=1&y=2', $parts['query']);
        self::assertSame('top', $parts['fragment']);
    }

    public function testMissingComponentsAreNull(): void
    {
        $parts = Uri::parse('/just/a/path');

        self::assertNull($parts['scheme']);
        self::assertNull($parts['host']);
        self::assertNull($parts['port']);
        self::assertNull($parts['query']);
        self::assertNull($parts['fragment']);
        self::assertSame('/just/a/path', $parts['path']);
    }

    public function testTheSchemeAndHostAreLowercased(): void
    {
        $parts = Uri::parse('HTTPS://Example.COM/x');

        self::assertSame('https', $parts['scheme']);
        self::assertSame('example.com', $parts['host']);
        self::assertSame('Example.COM', 'Example.COM');
    }

    public function testUserInfoIsDecoded(): void
    {
        $parts = Uri::parse('ftp://a%20b:p%40ss@example.com/file');

        self::assertSame('a b', $parts['user']);
        self::assertSame('p@ss', $parts['password']);
    }

    public function testAnIpv6LiteralKeepsItsBrackets(): void
    {
        $parts = Uri::parse('http://[::1]:8080/x');

        self::assertSame('[::1]', $parts['host']);
        self::assertSame(8080, $parts['port']);
    }

    public function testAnEmptyQueryIsTreatedAsAbsent(): void
    {
        self::assertNull(Uri::parse('http://example.com/x?')['query']);
    }

    public function testAPortOutsideTheRangeIsRefused(): void
    {
        $this->expectException(InvalidArgumentException::class);
        Uri::parse('http://example.com:70000/x');
    }

    public function testNormalisingDropsTheDefaultPort(): void
    {
        self::assertSame('http://example.com/a', Uri::normalize('HTTP://Example.COM:80/a'));
        self::assertSame('https://example.com/a', Uri::normalize('https://example.com:443/a'));
    }

    public function testANonDefaultPortSurvivesNormalisation(): void
    {
        self::assertSame('http://example.com:8080/a', Uri::normalize('http://example.com:8080/a'));
    }

    public function testDotSegmentsAreResolved(): void
    {
        self::assertSame('/a/c', Uri::removeDotSegments('/a/./b/../c'));
        self::assertSame('/a/', Uri::removeDotSegments('/a/b/..'));
        self::assertSame('/', Uri::removeDotSegments('/a/..'));
        // RFC 3986 5.2.4 replaces a trailing '/.' with '/', so the prefix
        // keeps its trailing slash here; posixpath.normpath would drop it.
        self::assertSame('/a/b/', Uri::removeDotSegments('/a/b/.'));
        self::assertSame('a/c', Uri::removeDotSegments('a/./b/../c'));
    }

    public function testAHostWithNoPathGetsASlash(): void
    {
        self::assertSame('https://example.com/', Uri::normalize('https://example.com'));
    }

    public function testQueryPairsAreDecodedInOrder(): void
    {
        self::assertSame(
            [['a', '1'], ['b', 'two words'], ['flag', '']],
            Uri::queryPairs('a=1&b=two%20words&flag')
        );
    }

    public function testMergeReplacesAndAppends(): void
    {
        $pairs = Uri::queryPairs('a=1&b=2');
        self::assertSame(
            [['a', '9'], ['b', '2'], ['c', '3']],
            Uri::mergeQuery($pairs, ['a' => '9', 'c' => '3'])
        );
    }

    public function testAReplacedParameterKeepsOneCopy(): void
    {
        $pairs = Uri::queryPairs('a=1&a=2');
        self::assertSame([['a', '3']], Uri::mergeQuery($pairs, ['a' => '3']));
    }

    public function testEncodingRoundTripsThroughDecoding(): void
    {
        $value = 'a b&c=d/é';
        self::assertSame($value, rawurldecode(rawurlencode($value)));
        self::assertSame('a%20b%26c%3Dd%2F%C3%A9', rawurlencode($value));
    }

    public function testToStringRebuildsTheUri(): void
    {
        $parts = Uri::parse('https://user@example.com:8443/a/b?x=1#top');

        self::assertSame('https://user@example.com:8443/a/b?x=1#top', Uri::toString($parts));
    }
}
