<?php

declare(strict_types=1);

namespace {{ package_name }}\Controller;

use {{ package_name }}\Service\TextStats;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\Routing\Attribute\Route;

/**
 * The front page: a GET route that answers with a small JSON body built from
 * an injected service, so the business logic is testable without HTTP.
 */
final class HomeController extends AbstractController
{
    public function __construct(private readonly TextStats $textStats)
    {
    }

    #[Route('/', name: 'home', methods: ['GET'])]
    public function home(): JsonResponse
    {
        $message = 'Hello from Symfony!';
        $stats = $this->textStats->count($message);

        return new JsonResponse([
            'message' => $message,
            'stats' => [
                'lines' => $stats->lines,
                'words' => $stats->words,
                'bytes' => $stats->bytes,
            ],
        ]);
    }
}
