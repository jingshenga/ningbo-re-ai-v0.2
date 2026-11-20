-- Minimal schema emitted by CreatorHub's ContentRecord and MonitorTarget models.
CREATE TABLE monitortarget (
    id INTEGER PRIMARY KEY,
    nickname TEXT,
    tags TEXT
);
CREATE TABLE contentrecord (
    id INTEGER PRIMARY KEY,
    platform TEXT,
    target_id INTEGER,
    aweme_id TEXT,
    "desc" TEXT,
    create_time INTEGER
);

INSERT INTO monitortarget (id, nickname, tags)
VALUES (1, '宁波看房记录', '["宁波","海曙"]');
INSERT INTO contentrecord (id, platform, target_id, aweme_id, "desc", create_time)
VALUES (1, 'douyin', 1, '7234567890123456789', '宁波海曙房源线索 120㎡ 260万', 1795159200);
