"""统计口径（docs/database.md 统计表）。"""

from tests.conftest import CITY_CODES, create_member, create_trip


def test_stats_empty_zeroes(client):
    r = client.get("/api/v1/stats")
    assert r.status_code == 200
    assert r.json() == {
        "years": 0, "provinces": 0, "cities": 0, "attractions": 0,
        "countries": 0, "trips": 0, "days": 0, "with_kids": 0,
    }


def test_stats_counts_trips_days_years(client):
    create_trip(client, title="2018", start_date="2018-04-01", end_date="2018-04-08")
    create_trip(client, title="2024", start_date="2024-05-01", end_date="2024-05-07")
    stats = client.get("/api/v1/stats").json()
    assert stats["trips"] == 2
    assert stats["days"] == 8 + 7
    assert stats["years"] == 2026 - 2018  # 当前自然年（测试环境 2026）− 首次旅行年份


def test_stats_drafts_excluded(client):
    create_trip(client, title="草稿", status="draft")
    assert client.get("/api/v1/stats").json()["trips"] == 0


def test_stats_province_city_dedup(client):
    """两次云南：省、市、景点都按去重口径计。"""
    create_trip(
        client,
        title="第一次云南",
        cities=[{"city_code": CITY_CODES["昆明市"]}, {"city_code": CITY_CODES["大理白族自治州"]}],
        attractions=[
            {"name": "洱海", "city_code": CITY_CODES["大理白族自治州"]},
            {"name": "滇池", "city_code": CITY_CODES["昆明市"]},
        ],
    )
    create_trip(
        client,
        title="第二次云南",
        cities=[{"city_code": CITY_CODES["大理白族自治州"]}],
        attractions=[{"name": "洱海", "city_code": CITY_CODES["大理白族自治州"]}],
    )

    stats = client.get("/api/v1/stats").json()
    assert stats["provinces"] == 1  # 云南省
    assert stats["cities"] == 2  # 昆明 + 大理
    assert stats["attractions"] == 2  # (大理,洱海)(昆明,滇池) 去重


def test_stats_municipality_counts_both(client):
    """直辖市同时计入省、市两项。"""
    create_trip(client, cities=[{"city_code": CITY_CODES["北京市市级"]}])
    stats = client.get("/api/v1/stats").json()
    assert stats["provinces"] == 1
    assert stats["cities"] == 1


def test_stats_attraction_same_name_different_city(client):
    create_trip(client, attractions=[
        {"name": "古城", "city_code": CITY_CODES["昆明市"]},
        {"name": "古城", "city_code": CITY_CODES["丽江市"]},
    ])
    assert client.get("/api/v1/stats").json()["attractions"] == 2


def test_stats_countries_domestic_plus_foreign(client):
    create_trip(client, title="国内", country=None)
    create_trip(client, title="日本", country="日本", cities=[])
    create_trip(client, title="日本关西再访", country="日本", cities=[])
    create_trip(client, title="泰国", country="泰国", cities=[])
    stats = client.get("/api/v1/stats").json()
    assert stats["countries"] == 3  # 中国 1 + 日本 + 泰国


def test_stats_countries_foreign_only(client):
    create_trip(client, title="只有日本", country="日本", cities=[])
    stats = client.get("/api/v1/stats").json()
    assert stats["countries"] == 1


def test_stats_with_kids(client):
    dad = create_member(client, "张三", nickname="爸爸")
    son = create_member(client, "张小四", nickname="哥哥", is_child=True)

    create_trip(client, title="带娃 1", member_ids=[dad["id"], son["id"]])
    create_trip(client, title="带娃 2", member_ids=[son["id"]])
    create_trip(client, title="不带娃", member_ids=[dad["id"]])
    create_trip(client, title="没人")

    stats = client.get("/api/v1/stats").json()
    assert stats["with_kids"] == 2


def test_stats_foreign_trip_not_in_domestic_province_city(client):
    create_trip(client, title="京都", country="日本", cities=[{"city_name": "京都"}])
    stats = client.get("/api/v1/stats").json()
    assert stats["provinces"] == 0
    assert stats["cities"] == 0
