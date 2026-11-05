<?php

declare(strict_types=1);

namespace Tests\Feature;

use Tests\TestCase;

final class StatApiTest extends TestCase
{
    public function test_the_service_describes_itself(): void
    {
        $this->getJson('/')
            ->assertOk()
            ->assertJsonPath('service', config('app.name'));
    }

    public function test_a_json_body_is_counted_with_wc_semantics(): void
    {
        $this->postJson('/count', ['text' => "one two\nthree\n"])
            ->assertOk()
            ->assertExactJson([
                'text' => "one two\nthree\n",
                'lines' => 2,
                'words' => 3,
                'bytes' => 14,
            ]);
    }

    public function test_a_query_parameter_is_counted_too(): void
    {
        $this->getJson('/count?text='.urlencode('héllo world'))
            ->assertOk()
            ->assertJson(['lines' => 0, 'words' => 2, 'bytes' => 12]);
    }

    public function test_input_is_counted_exactly_as_sent(): void
    {
        // TrimStrings and ConvertEmptyStringsToNull are removed in
        // bootstrap/app.php, so padding and empty strings survive the request.
        $this->postJson('/count', ['text' => "  padded  \n"])
            ->assertOk()
            ->assertJson(['lines' => 1, 'words' => 1, 'bytes' => 11]);

        $this->postJson('/count', ['text' => ''])
            ->assertOk()
            ->assertJson(['lines' => 0, 'words' => 0, 'bytes' => 0]);
    }

    public function test_a_missing_field_is_rejected_with_422(): void
    {
        $this->postJson('/count', ['txt' => 'typo'])
            ->assertStatus(422)
            ->assertJsonPath('error', 'the "text" field is required and must be a string');
    }

    public function test_an_unknown_route_is_a_json_404(): void
    {
        $this->getJson('/nope')
            ->assertNotFound()
            ->assertJsonStructure(['message']);
    }
}
