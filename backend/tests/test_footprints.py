"""足迹地图数据（footprints）：省份热力、景点点、路线、编年聚合。"""

from tests.conftest import CITY_CODES, create_trip, make_jpeg


def test_footprints_empty(client):
    data = client.get("/api/v1/footprints").json()
    assert data == {
        "years": [],
        "provinces": {},
        "provinces_by_year": {},
        "spots": [],
        "routes": [],
        "timeline": [],
        "abroad_trips": [],
    }


def test_footprints_provinces_count_distinct_trips(client):
    create_trip(client, title="云南一次")
    create_trip(client, title="云南二次", start_date="2023-05-01", end_date="2023-05-02")
    create_trip(client, title="青岛", cities=[{"city_code": CITY_CODES["青岛市"]}])

    data = client.get("/api/v1/footprints").json()
    assert data["provinces"] == {"云南省": 2, "山东省": 1}  # 省名与 GeoJSON 严格一致


def test_footprints_spots_resolved_coords(client):
    """景点坐标：精调优先，否则跟随城市中心；境外/草稿不上图。"""
    create_trip(client, attractions=[
        {"name": "洱海", "city_code": CITY_CODES["大理白族自治州"], "lng": 100.18, "lat": 25.75},
        {"name": "滇池", "city_code": CITY_CODES["昆明市"]},
    ])
    create_trip(client, title="京都", country="日本", cities=[{"city_name": "京都"}],
                attractions=[{"name": "哲学之道"}])
    create_trip(client, title="草稿", status="draft",
                attractions=[{"name": "草稿景点", "city_code": CITY_CODES["昆明市"]}])

    data = client.get("/api/v1/footprints").json()
    spots = {s["name"]: s for s in data["spots"]}
    assert set(spots) == {"洱海", "滇池"}  # 境外与草稿被排除

    assert spots["洱海"]["lng"] == 100.18
    from app.seed import city_rows
    kunming = next(c for c in city_rows() if c["code"] == CITY_CODES["昆明市"])
    assert spots["滇池"]["lng"] == kunming["lng"]
    assert spots["滇池"]["city"] == "云南 · 昆明"
    assert spots["滇池"]["year"] == 2024
    assert spots["滇池"]["trip_title"] == "云南环线：从滇池到玉龙"


def test_footprints_spot_photos_and_note(client, photos_root):
    make_jpeg(photos_root / "2024云南" / "大理洱海" / "a.jpg")
    make_jpeg(photos_root / "2024云南" / "大理洱海" / "b.jpg")
    make_jpeg(photos_root / "2024云南" / "大理洱海" / "c.jpg")
    make_jpeg(photos_root / "2024云南" / "大理洱海" / "d.jpg")

    create_trip(client)
    data = client.get("/api/v1/footprints").json()
    erhai = next(s for s in data["spots"] if s["name"] == "洱海")
    assert erhai["photo_count"] == 4
    assert erhai["photos"] == [
        "2024云南/大理洱海/a.jpg", "2024云南/大理洱海/b.jpg", "2024云南/大理洱海/c.jpg",
    ]  # 面板缩略图只取前 3
    assert erhai["note"] == "S 湾的日落持续了四十分钟。"


def test_footprints_routes_follow_sort_order(client):
    create_trip(client)  # 昆明 → 大理 → 丽江
    data = client.get("/api/v1/footprints").json()
    assert len(data["routes"]) == 1
    route = data["routes"][0]
    assert route["year"] == 2024
    assert route["trip_slug"]
    assert len(route["coords"]) == 3
    # 与城市字典中心一致
    from app.seed import city_rows
    dali = next(c for c in city_rows() if c["code"] == CITY_CODES["大理白族自治州"])
    assert route["coords"][1] == [dali["lng"], dali["lat"]]


def test_footprints_route_needs_two_domestic_cities(client):
    create_trip(client, cities=[{"city_code": CITY_CODES["昆明市"]}])  # 单城无连线
    assert client.get("/api/v1/footprints").json()["routes"] == []


def test_footprints_foreign_cities_not_routed_on_china_map(client):
    create_trip(client, cities=[{"city_code": CITY_CODES["昆明市"]}, {"city_name": "曼谷"}])
    data = client.get("/api/v1/footprints").json()
    assert data["routes"] == []  # 境外城市不进中国地图路线


def test_footprints_years_and_timeline(client):
    create_trip(client, title="2024 一次", start_date="2024-05-01", end_date="2024-05-07")
    create_trip(client, title="2024 二次", start_date="2024-10-01", end_date="2024-10-03")
    create_trip(client, title="2023", start_date="2023-08-12", end_date="2023-08-15")

    data = client.get("/api/v1/footprints").json()
    assert data["years"] == [2024, 2023]
    tl2024 = next(t for t in data["timeline"] if t["year"] == 2024)
    assert tl2024["trip_count"] == 2
    assert tl2024["total_days"] == 7 + 3


def test_footprints_provinces_by_year_and_abroad(client):
    """年份筛选联动需要分年省份数据；境外行程要单独给出入口（#16）。"""
    create_trip(client, title="云南2024", start_date="2024-05-01", end_date="2024-05-02",
                cities=[{"city_code": CITY_CODES["昆明市"]}])
    create_trip(client, title="京都", country="日本", start_date="2018-04-01", end_date="2018-04-02",
                cities=[{"city_name": "京都"}])

    data = client.get("/api/v1/footprints").json()
    # JSON 序列化会把 int 键转字符串；前端用数字索引时 JS 自动转字符串键，行为一致
    assert data["provinces_by_year"] == {"2024": {"云南省": 1}}
    assert data["abroad_trips"] == [
        {"year": 2018, "title": "京都", "slug": data["abroad_trips"][0]["slug"], "country": "日本"}
    ]
