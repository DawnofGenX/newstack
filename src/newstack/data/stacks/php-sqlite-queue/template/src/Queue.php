<?php

declare(strict_types=1);

namespace {{ package_name }};

class Queue
{
    private \PDO $pdo;
    /** @var callable */
    private $clock;

    public function __construct(\PDO $pdo, ?callable $clock = null)
    {
        $this->pdo = $pdo;
        $this->clock = $clock ?? static function (): int {
            return time();
        };
        $this->migrate();
    }

    private function now(): int
    {
        return ($this->clock)();
    }

    private function migrate(): void
    {
        $this->pdo->exec(
            'CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payload TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT \'pending\',
                leased_until INTEGER,
                attempts INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL
            )'
        );
    }

    public function push(string $payload): int
    {
        $stmt = $this->pdo->prepare(
            'INSERT INTO jobs (payload, status, created_at) VALUES (:payload, :status, :created_at)'
        );
        $stmt->execute([
            ':payload' => $payload,
            ':status' => 'pending',
            ':created_at' => $this->now(),
        ]);

        return (int) $this->pdo->lastInsertId();
    }

    /**
     * @return array{id:int,payload:string}|null
     */
    public function pop(int $leaseSeconds): ?array
    {
        $now = $this->now();
        $this->pdo->beginTransaction();
        try {
            $stmt = $this->pdo->prepare(
                'SELECT id, payload FROM jobs
                 WHERE status = \'pending\'
                    OR (status = \'leased\' AND leased_until <= :now)
                 ORDER BY id ASC LIMIT 1'
            );
            $stmt->execute([':now' => $now]);
            $row = $stmt->fetch(\PDO::FETCH_ASSOC);
            if ($row === false) {
                $this->pdo->commit();
                return null;
            }
            $id = (int) $row['id'];
            $update = $this->pdo->prepare(
                'UPDATE jobs SET status = \'leased\', leased_until = :until, attempts = attempts + 1 WHERE id = :id'
            );
            $update->execute([
                ':until' => $now + $leaseSeconds,
                ':id' => $id,
            ]);
            $this->pdo->commit();
            return ['id' => $id, 'payload' => (string) $row['payload']];
        } catch (\Throwable $e) {
            $this->pdo->rollBack();
            throw $e;
        }
    }

    public function ack(int $id): bool
    {
        $stmt = $this->pdo->prepare(
            'UPDATE jobs SET status = \'done\', leased_until = NULL WHERE id = :id AND status = \'leased\''
        );
        $stmt->execute([':id' => $id]);
        return $stmt->rowCount() > 0;
    }

    public function retry(int $id): bool
    {
        $stmt = $this->pdo->prepare(
            'UPDATE jobs SET status = \'pending\', leased_until = NULL WHERE id = :id'
        );
        $stmt->execute([':id' => $id]);
        return $stmt->rowCount() > 0;
    }

    public function status(int $id): ?string
    {
        $stmt = $this->pdo->prepare('SELECT status FROM jobs WHERE id = :id');
        $stmt->execute([':id' => $id]);
        $row = $stmt->fetch(\PDO::FETCH_ASSOC);
        return $row === false ? null : (string) $row['status'];
    }
}
