"""Demo-only range seed: all 2,000 accounts are present from the first scene.

Preserves specially seeded balances from Stage 01. Safe to re-run; inserts
missing accounts only and never overwrites an existing balance or version.
Use ONLY on a separate video project with the initial A/B owner map.
"""
from __future__ import annotations

import os

import psycopg
from psycopg.rows import dict_row


def seed_full_ranges() -> None:
    with psycopg.connect(os.environ['METADATA_DATABASE_URL'], row_factory=dict_row) as db:
        mapping=db.execute('SELECT range_start,range_end,shard_id,epoch FROM shard_map '
                           'WHERE active=true ORDER BY range_start').fetchall()
        found=[(r['range_start'],r['range_end'],r['shard_id'],r['epoch']) for r in mapping]
        if found != [(1,1000,'A',1),(1001,2000,'B',1)]:
            print('VIDEO A/B SEED: SKIPPED, map has already changed', flush=True)
            return
        desired=db.execute('SELECT shard_id FROM desired_replica_count ORDER BY shard_id').fetchall()
        if [r['shard_id'] for r in desired] != ['A','B']:
            raise RuntimeError('Refusing A/B seed when Shard C is already configured')
    for shard,lo,hi in [('A',1,1000),('B',1001,2000)]:
        env=f'SHARD_{shard}_DATABASE_URL'
        with psycopg.connect(os.environ[env]) as db:
            db.execute('INSERT INTO accounts(account_id,balance) '
                       "SELECT 'A' || lpad(n::text,4,'0'),100.00 "
                       'FROM generate_series(%s::integer,%s::integer) n ON CONFLICT (account_id) DO NOTHING',
                       (lo,hi))
            count=db.execute('SELECT COUNT(*)::integer FROM accounts').fetchone()[0]
            if count != 1000:
                raise RuntimeError(f'Shard {shard} expected 1000 seed accounts, found {count}')
        print(f'VIDEO SHARD {shard}: {count} accounts present ({lo}-{hi})',flush=True)
    print('VIDEO A/B SEED: 2000 accounts split exactly 1000/1000',flush=True)


if __name__ == '__main__':
    seed_full_ranges()
