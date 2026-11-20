-- CreatorHub bridge test fixture: deterministic four-row posts table
-- (three Ningbo rows + one Shanghai row the main endpoint must reject).
-- Data only; loaded by tests/test_creatorhub_bridge.py via executescript.
CREATE TABLE posts (id INTEGER PRIMARY KEY, platform TEXT, post_id TEXT, source_url TEXT, title TEXT, content TEXT, author_name TEXT, publish_time TEXT, media_urls TEXT, tags TEXT, raw_html_snippet TEXT, created_at TEXT DEFAULT (datetime('now')));

INSERT INTO posts (id, platform, post_id, source_url, title, content, author_name, publish_time, media_urls, tags, raw_html_snippet) VALUES (1, '小红书', 'xhs-001', 'https://www.xiaohongshu.com/explore/001', '东部新城笋盘', '宁波东部新城 89平 189万', '宁波看房日记', '2026-11-19', '["https://img.example/1.jpg"]', '宁波', NULL);
INSERT INTO posts (id, platform, post_id, source_url, title, content, author_name, publish_time, media_urls, tags, raw_html_snippet) VALUES (2, 'douyin', 'dy-002', 'https://www.douyin.com/video/002', '镇海学区', '镇海学区房 120平 260万 急售', '宁波置业', '2026-11-19', 'https://img.example/2.jpg,https://img.example/3.jpg', '宁波', NULL);
INSERT INTO posts (id, platform, post_id, source_url, title, content, author_name, publish_time, media_urls, tags, raw_html_snippet) VALUES (3, '视频号', 'sph-003', 'https://channels.weixin.qq.com/mm/003', '奉化新盘', '奉化新盘开盘 143平 415万', '奉化楼市', '2026-11-19', '[]', '奉化', NULL);
INSERT INTO posts (id, platform, post_id, source_url, title, content, author_name, publish_time, media_urls, tags, raw_html_snippet) VALUES (4, '小红书', 'xhs-004', 'https://www.xiaohongshu.com/explore/004', '上海楼市', '上海浦东内环开盘售罄', '上海达人', '2026-11-19', '[]', '上海', NULL);
