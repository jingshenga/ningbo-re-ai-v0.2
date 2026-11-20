-- CreatorHub bridge test fixture: the deliberately-unsalvageable row
-- (http source_url the main endpoint must reject) used by
-- tests/test_creatorhub_sidecar_bridge.py, plus a write probe statement
-- that read-only connections must refuse.
INSERT INTO posts (id, platform, source_url, content) VALUES (5, 'douyin', 'http://not-https.example/v', '宁波好房');
