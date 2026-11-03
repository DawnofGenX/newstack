<?php

declare(strict_types=1);

namespace {{ package_name }}\Tests;

use Symfony\Bundle\FrameworkBundle\Test\WebTestCase;

final class HomeControllerTest extends WebTestCase
{
    public function testHomeReturnsJsonWithStats(): void
    {
        $client = static::createClient();

        $client->request('GET', '/');

        self::assertResponseIsSuccessful();
        self::assertResponseStatusCodeSame(200);

        $content = (string) $client->getResponse()->getContent();
        self::assertJson($content);

        $data = json_decode($content, true);

        self::assertIsArray($data);
        self::assertArrayHasKey('message', $data);
        self::assertArrayHasKey('stats', $data);
        self::assertSame('Hello from Symfony!', $data['message']);
        self::assertSame(['lines' => 0, 'words' => 3, 'bytes' => 19], $data['stats']);
    }
}
