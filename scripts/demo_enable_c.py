"""Idempotently enable Shard C desired replica count after live C startup.

Fail closed unless C1 and C2 are actually healthy. Metadata ownership stays B.
This must run on a fresh video-only Compose project, never the real deployment.
"""
from __future__ import annotations

import os
import time

import httpx
import psycopg
from psycopg.rows import dict_row


def main() -> None:
    with psycopg.connect(os.environ['METADATA_DATABASE_URL'], row_factory=dict_row) as db:
        map_rows = db.execute('SELECT range_start,range_end,shard_id,epoch FROM shard_map '
                              'WHERE active=true ORDER BY range_start').fetchall()
        expected = [(1,1000,'A',1), (1001,2000,'B',1)]
        got = [(r['range_start'],r['range_end'],r['shard_id'],r['epoch']) for r in map_rows]
        if got != expected:
            raise RuntimeError(f'C activation must occur BEFORE cutover; current map: {got}')
    with psycopg.connect(os.environ['SHARD_C_DATABASE_URL'], row_factory=dict_row) as db:
        n = db.execute('SELECT COUNT(*) AS n FROM accounts').fetchone()['n']
        if n != 0:
            raise RuntimeError(f'Expected an initially empty Shard C, found {n} accounts')
    with httpx.Client(timeout=5, trust_env=False) as client:
        for slot in (1, 2):
            host = f'shard-c-{slot}'
            last = None
            for attempt in range(30):
                try:
                    result = client.get(f'http://{host}:8000/health')
                    result.raise_for_status()
                    payload = result.json()
                    if payload.get('shard') != 'C' or payload.get('replica') != f'C{slot}':
                        raise RuntimeError(f'Unexpected C replica identity: {payload}')
                    break
                except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                    last = exc
                    time.sleep(2)
            else:
                raise RuntimeError(f'Shard C replica {host} failed to become healthy: {last}')
    with psycopg.connect(os.environ['METADATA_DATABASE_URL']) as db:
        db.execute('INSERT INTO desired_replica_count(shard_id,desired_count) '
                   "VALUES ('C',2) ON CONFLICT (shard_id) DO UPDATE "
                   'SET desired_count=EXCLUDED.desired_count')
    print('SHARD C ENABLED: 2 healthy replica slots, database empty, owner map still A/B epoch 1', flush=True)


if __name__ == '__main__':
    main()
