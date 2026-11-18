<?php

declare(strict_types=1);

namespace {{ package_name }}\Tests;

use {{ package_name }}\Queue;
use PHPUnit\Framework\TestCase;

class QueueTest extends TestCase
{
    private function makeQueue(?callable $clock = null): Queue
    {
        $pdo = new \PDO('sqlite::memory:');
        $pdo->setAttribute(\PDO::ATTR_ERRMODE, \PDO::ERRMODE_EXCEPTION);
        return new Queue($pdo, $clock);
    }

    public function testPushAndPop(): void
    {
        $q = $this->makeQueue();
        $id = $q->push('hello');
        $job = $q->pop(30);
        $this->assertNotNull($job);
        $this->assertSame($id, $job['id']);
        $this->assertSame('hello', $job['payload']);
    }

    public function testAck(): void
    {
        $q = $this->makeQueue();
        $id = $q->push('hello');
        $q->pop(30);
        $this->assertTrue($q->ack($id));
        $this->assertSame('done', $q->status($id));
        $this->assertNull($q->pop(30));
    }

    public function testRetry(): void
    {
        $q = $this->makeQueue();
        $id = $q->push('hello');
        $q->pop(30);
        $this->assertTrue($q->retry($id));
        $job = $q->pop(30);
        $this->assertNotNull($job);
        $this->assertSame($id, $job['id']);
    }

    public function testLeaseExpiryReclaims(): void
    {
        $now = 1000;
        $clock = function () use (&$now): int {
            return $now;
        };
        $q = $this->makeQueue($clock);
        $id = $q->push('hello');
        $first = $q->pop(5);
        $this->assertNotNull($first);
        $now = 1010; // expired
        $second = $q->pop(5);
        $this->assertNotNull($second);
        $this->assertSame($id, $second['id']);
    }

    public function testClaimSurvivesNewProcess(): void
    {
        $path = sys_get_temp_dir() . '/queue-' . uniqid() . '.db';
        if (file_exists($path)) {
            unlink($path);
        }
        $pdo1 = new \PDO('sqlite:' . $path);
        $pdo1->setAttribute(\PDO::ATTR_ERRMODE, \PDO::ERRMODE_EXCEPTION);
        $q1 = new Queue($pdo1);
        $id = $q1->push('durable');
        $q1->pop(60);

        $pdo2 = new \PDO('sqlite:' . $path);
        $pdo2->setAttribute(\PDO::ATTR_ERRMODE, \PDO::ERRMODE_EXCEPTION);
        $q2 = new Queue($pdo2);
        $this->assertSame('leased', $q2->status($id));

        @unlink($path);
    }
}
