<?php

declare(strict_types=1);

namespace {{ package_name }}\Tests;

use {{ package_name }}\Api;
use {{ package_name }}\Store;
use PHPUnit\Framework\TestCase;
use Slim\Psr7\Factory\ServerRequestFactory;
use Slim\Psr7\Factory\StreamFactory;

final class ApiTest extends TestCase
{
    protected function setUp(): void
    {
        putenv('PHP_SLIM_ITEMS_FILE=' . sys_get_temp_dir() . '/php-slim-api-test-' . getmypid() . '.json');
        Store::reset();
    }

    protected function tearDown(): void
    {
        Store::reset();
        putenv('PHP_SLIM_ITEMS_FILE');
    }

    public function testHealthReturnsOk(): void
    {
        $app = Api::createApp();
        $request = (new ServerRequestFactory())->createServerRequest('GET', '/health');
        $response = $app->handle($request);
        $this->assertSame(200, $response->getStatusCode());
        $body = (string) $response->getBody();
        $this->assertStringContainsString('ok', $body);
    }

    public function testItemsCanBeCreatedAndListed(): void
    {
        $app = Api::createApp();
        $request = (new ServerRequestFactory())->createServerRequest('POST', '/items');
        $stream = (new StreamFactory())->createStream(json_encode(['name' => 'widget']));
        $request = $request->withBody($stream)->withHeader('Content-Type', 'application/json');
        $response = $app->handle($request);
        $this->assertSame(201, $response->getStatusCode());

        $request = (new ServerRequestFactory())->createServerRequest('GET', '/items');
        $response = $app->handle($request);
        $body = (string) $response->getBody();
        $this->assertStringContainsString('widget', $body);
    }

    public function testItemsSurviveARequestBoundary(): void
    {
        // Regression: PHP resets statics at request shutdown, so the store has
        // to reach the filesystem or a second request would see an empty list.
        Store::add('widget');

        $this->assertFileExists(Store::path());
        $this->assertStringContainsString('widget', (string) file_get_contents(Store::path()));
        $this->assertSame(['widget'], Store::all());
    }

    public function testInvalidItemReturns422(): void
    {
        $app = Api::createApp();
        $request = (new ServerRequestFactory())->createServerRequest('POST', '/items');
        $stream = (new StreamFactory())->createStream(json_encode(['name' => '']));
        $request = $request->withBody($stream);
        $response = $app->handle($request);
        $this->assertSame(422, $response->getStatusCode());
    }
}
