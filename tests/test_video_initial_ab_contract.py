"""Pure file-structure proof: C must be a runtime opt-in in the video copy."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_initial_compose_has_opt_in_expansion_and_isolated_name():
    src=(ROOT/'compose.yaml').read_text()
    assert 'name: banking-video-ab' in src
    for service in ('shard-c-db','shard-c-1','shard-c-2','migration-manager'):
        after=src.split(f"  {service}:\n",1)[1].split('\n  ',1)[0]
        assert 'profiles: [expansion]' in after
    migrator=src.split('  schema-migrator:\n',1)[1].split('\n  shard-a-1:',1)[0]
    assert 'shard-c-db: {condition: service_healthy}' not in migrator
    assert 'scripts.demo_bootstrap_ab' in migrator

def test_stage11_c_is_not_prematurely_registered():
    src=(ROOT/'sql/migrations/metadata/008_stage11_target.sql').read_text()
    assert "VALUES ('C',2)" not in src
    assert 'demo_enable_c.py' in src

def test_demo_full_range_seed_and_expansion_scripts_exist():
    assert "generate_series(%s::integer,%s::integer)" in (ROOT/'scripts/demo_seed_full_ranges.py').read_text()
    assert "('A',1,1000),('B',1001,2000)" in (ROOT/'scripts/demo_seed_full_ranges.py').read_text()
    assert 'INSERT INTO desired_replica_count' in (ROOT/'scripts/demo_enable_c.py').read_text()
