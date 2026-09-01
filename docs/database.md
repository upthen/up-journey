# up-journey 数据库设计（MySQL 8 · utf8mb4 · InnoDB）

> 实体关系与口径见 spec；本文是实施级 DDL 蓝本，开发时以 Alembic 迁移为准。

## ER 总览

```
family_member 1─n trip_member n─1 trip 1─n trip_tag n─1 tag
                                  trip 1─n trip_city n─1 city(字典)
                                  trip 1─n attraction ──(city_code)──▶ city
                                  trip 1─n trip_day
```

## DDL

```sql
-- 城市字典（种子迁移导入；名称与前端 GeoJSON 严格对齐）
CREATE TABLE city (
  code           VARCHAR(12)  PRIMARY KEY,   -- 行政区划码，如 530100
  name           VARCHAR(32)  NOT NULL,      -- 如 昆明市
  province_code  VARCHAR(12)  NOT NULL,
  province_name  VARCHAR(32)  NOT NULL,      -- 与地图 GeoJSON 省份名一致
  level          TINYINT      NOT NULL,      -- 1 省级(含直辖市/港澳台) 2 地级市
  lng            DECIMAL(9,6) NOT NULL,
  lat            DECIMAL(8,6) NOT NULL,
  KEY idx_province (province_code)
);

CREATE TABLE family_member (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  name       VARCHAR(32)  NOT NULL,
  nickname   VARCHAR(32)  NULL,             -- 称呼：爸爸/妈妈/哥哥…
  created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tag (
  id   INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(16) NOT NULL UNIQUE
);

CREATE TABLE trip (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  slug        VARCHAR(64)  NOT NULL UNIQUE,           -- 由标题生成，可改
  title       VARCHAR(128) NOT NULL,
  start_date  DATE         NOT NULL,
  end_date    DATE         NOT NULL,
  summary     VARCHAR(500) NULL,                      -- 卡片摘要
  content     LONGTEXT     NULL,                      -- 富文本 HTML
  cover_photo VARCHAR(255) NULL,                      -- 相册相对路径，从本旅行图片中挑选
  country     VARCHAR(32)  NULL,                      -- 境外旅行时填，如 日本；境内为 NULL
  status      ENUM('draft','published') NOT NULL DEFAULT 'draft',
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_status_date (status, start_date)
);

CREATE TABLE trip_member (
  trip_id   INT NOT NULL,
  member_id INT NOT NULL,
  PRIMARY KEY (trip_id, member_id),
  FOREIGN KEY (trip_id)  REFERENCES trip(id)  ON DELETE CASCADE,
  FOREIGN KEY (member_id) REFERENCES family_member(id) ON DELETE CASCADE
);

CREATE TABLE trip_tag (
  trip_id INT NOT NULL,
  tag_id  INT NOT NULL,
  PRIMARY KEY (trip_id, tag_id),
  FOREIGN KEY (trip_id) REFERENCES trip(id) ON DELETE CASCADE,
  FOREIGN KEY (tag_id)  REFERENCES tag(id)  ON DELETE CASCADE
);

-- 途经城市（有序）。境内：city_code 非空；境外：city_code 空，用自由文本 + 可选坐标
CREATE TABLE trip_city (
  id        INT AUTO_INCREMENT PRIMARY KEY,
  trip_id   INT NOT NULL,
  city_code VARCHAR(12) NULL,
  city_name VARCHAR(32) NULL,               -- 境外城市名，如 京都
  lng       DECIMAL(9,6) NULL,
  lat       DECIMAL(8,6) NULL,
  sort_order SMALLINT NOT NULL DEFAULT 0,   -- 路线顺序
  FOREIGN KEY (trip_id)  REFERENCES trip(id) ON DELETE CASCADE,
  FOREIGN KEY (city_code) REFERENCES city(code),
  KEY idx_trip (trip_id, sort_order)
);

CREATE TABLE trip_day (
  id        INT AUTO_INCREMENT PRIMARY KEY,
  trip_id   INT NOT NULL,
  day_index SMALLINT NOT NULL,              -- D1、D2…
  date      DATE     NOT NULL,
  title     VARCHAR(128) NULL,              -- 昆明 → 大理
  note      VARCHAR(500) NULL,
  FOREIGN KEY (trip_id) REFERENCES trip(id) ON DELETE CASCADE,
  KEY idx_trip (trip_id, day_index)
);

CREATE TABLE attraction (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  trip_id        INT NOT NULL,
  name           VARCHAR(64) NOT NULL,      -- 洱海、西湖
  city_code      VARCHAR(12) NULL,          -- 境内景点关联字典城市
  album_rel_path VARCHAR(255) NULL,         -- 共享相册子目录（相对 /photos 根）
  lng            DECIMAL(9,6) NULL,         -- 可选精调坐标；空 = 跟随城市中心
  lat            DECIMAL(8,6) NULL,
  note           VARCHAR(255) NULL,
  FOREIGN KEY (trip_id)   REFERENCES trip(id) ON DELETE CASCADE,
  FOREIGN KEY (city_code) REFERENCES city(code),
  KEY idx_trip (trip_id)
);
```

## 统计口径（`GET /api/v1/stats`，SQL 聚合一次返回）

| 指标 | 口径 |
|---|---|
| 旅行年数 | 当前自然年 − MIN(start_date) 的年份 |
| 省数 | trip_city 去重 province_code（直辖市同时计省、市） |
| 市数 | 境内去重 city_code（含直辖市） |
| 景点数 | attraction 按 (city_code, name) 去重 |
| 国家数 | 境内算 1（中国）+ 去重 country |
| 旅行次数 / 累计天数 | COUNT(trip)；SUM(end_date − start_date + 1) |
| 带娃次数 | 含孩子成员的 trip 数 |

## 种子数据

- `city` 表：34 省级（含港澳台）+ 全部地级市 + 中心坐标，来源 = 行政区划码 × 阿里 DataV GeoJSON 名称对齐，构建脚本生成 JSON，Alembic 种子迁移导入。
- 省份名称以 **GeoJSON 的 name 字段为唯一真源**（着色时按名称匹配），字典生成脚本负责对齐并断言无遗漏。
