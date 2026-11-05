<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Support\TextStat;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

/**
 * The whole HTTP surface: describe the service, and count text.
 */
final class StatController
{
    public function service(): JsonResponse
    {
        return response()->json([
            'service' => config('app.name'),
            'endpoints' => [
                'GET /count?text=...' => 'count the text in the query string',
                'POST /count' => 'count the text in the JSON body field "text"',
            ],
        ]);
    }

    public function count(Request $request): JsonResponse
    {
        $text = $request->input('text');

        if (! is_string($text)) {
            return response()->json([
                'error' => 'the "text" field is required and must be a string',
            ], 422);
        }

        return response()->json(['text' => $text] + TextStat::of($text));
    }
}
