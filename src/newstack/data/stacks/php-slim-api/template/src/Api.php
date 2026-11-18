<?php

declare(strict_types=1);

namespace {{ package_name }};

use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Slim\Factory\AppFactory;

final class Api
{
    public static function createApp(): \Slim\App
    {
        $app = AppFactory::create();

        $app->get('/health', function (Request $request, Response $response): Response {
            $response->getBody()->write(json_encode(['status' => 'ok']));
            return $response->withHeader('Content-Type', 'application/json');
        });

        $app->get('/items', function (Request $request, Response $response): Response {
            $response->getBody()->write(json_encode(Store::all()));
            return $response->withHeader('Content-Type', 'application/json');
        });

        $app->post('/items', function (Request $request, Response $response): Response {
            $data = json_decode((string) $request->getBody(), true);
            if (!is_array($data) || !isset($data['name']) || !is_string($data['name']) || trim($data['name']) === '') {
                $response->getBody()->write(json_encode(['error' => 'invalid']));
                return $response->withStatus(422)->withHeader('Content-Type', 'application/json');
            }
            Store::add($data['name']);
            $response->getBody()->write(json_encode(['name' => $data['name']]));
            return $response->withStatus(201)->withHeader('Content-Type', 'application/json');
        });

        return $app;
    }
}
