"""Read-only proof that a video project begins with only Shards A and B."""
from __future__ import annotations

import os

import httpx
import psycopg
from psycopg.rows import dict_row


def main() -> None:
    with psycopg.connect(os.environ['METADATA_DATABASE_URL'], row_factory=dict_row) as db:
        intervals = db.execute('SELECT range_start,range_end,shard_id,epoch FROM shard_map '
                               'WHERE active=true ORDER BY range_start').fetchall()
        got = [(r['range_start'], r['range_end'], r['shard_id'], r['epoch']) for r in intervals]
        expected = [(1,1000,'A',1),(1001,2000,'B',1)]
        assert got == expected, (got,expected)
        desired = db.execute('SELECT shard_id,desired_count FROM desired_replica_count '
                             'ORDER BY shard_id').fetchall()
        assert [(r['shard_id'],r['desired_count']) for r in desired] == [('A',2),('B',2)],desired
        rows = db.execute('SELECT shard_id,replica_id FROM replica_registry ORDER BY shard_id,replica_id').fetchall()
        assert all(r['shard_id'] in ('A','B') for r in rows), rows
    with psycopg.connect(os.environ['SHARD_A_DATABASE_URL']) as db:
        n = db.execute("SELECT COUNT(*) FROM accounts WHERE account_id !~ '^A(0[0-9]{3}|1000)$'").fetchone()[0]
        assert n == 0, 'Shard A contains account outside A0001-A1000'
        assert db.execute('SELECT COUNT(*) FROM accounts').fetchone()[0] == 1000
        assert db.execute("SELECT COUNT(*) FROM accounts WHERE account_id='A0500'").fetchone()[0] == 1
    with psycopg.connect(os.environ['SHARD_B_DATABASE_URL']) as db:
        n = db.execute("SELECT COUNT(*) FROM accounts WHERE account_id !~ '^A(1[0-9]{3}|2000)$'").fetchone()[0]
        assert n == 0, 'Shard B contains account outside A1001-A2000'
        assert db.execute('SELECT COUNT(*) FROM accounts').fetchone()[0] == 1000
        assert db.execute("SELECT COUNT(*) FROM accounts WHERE account_id='A2000'").fetchone()[0] == 1
    with httpx.Client(timeout=10,trust_env=False) as client:
        for account, shard in [('A0500','A'),('A1500','B'),('A2000','B')]:
            response=client.get(f'http://gateway:8000/accounts/{account}/balance')
            response.raise_for_status()
            body=response.json()
            assert body['shard']==shard,(account,body)
        for shard in ('A','B'):
            response=client.get(f'http://gateway:8000/debug/replicas/{shard}')
            response.raise_for_status()
            assert response.json()['healthy_count']==2,(shard,response.json())
    print('VIDEO INITIAL A/B: ALL CHECKS PASSED',flush=True)
    print('A: A0001-A1000, B: A1001-A2000, epoch=1, 1000 accounts per shard, 2 healthy replicas per shard, no C slot',flush=True)


if __name__ == '__main__':
    main()
