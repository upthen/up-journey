"""展示端旅行列表与详情。"""

from tests.conftest import CITY_CODES, create_trip


def test_list_only_published_ordered_desc(client):
    create_trip(client, title="较新的旅行", start_date="2024-05-01", end_date="2024-05-03")
    create_trip(client, title="更早的旅行", start_date="2018-04-01", end_date="2018-04-02")
    create_trip(client, title="半成品草稿", start_date="2026-01-01", end_date="2026-01-02", status="draft")

    trips = client.get("/api/v1/trips").json()
    assert [t["title"] for t in trips] == ["较新的旅行", "更早的旅行"]  # 草稿不可见 + 时间倒序


def test_list_year_filter(client):
    create_trip(client, title="2024 之旅", start_date="2024-05-01", end_date="2024-05-02")
    create_trip(client, title="2023 之旅", start_date="2023-05-01", end_date="2023-05-02")

    trips = client.get("/api/v1/trips", params={"year": 2023}).json()
    assert [t["title"] for t in trips] == ["2023 之旅"]


def test_list_tag_filter(client):
    from tests.conftest import create_tag

    tag = create_tag(client, "海岛")
    create_trip(client, title="有标签", tag_ids=[tag["id"]])
    create_trip(client, title="无标签")

    trips = client.get("/api/v1/trips", params={"tag": "海岛"}).json()
    assert [t["title"] for t in trips] == ["有标签"]


def test_card_fields(client):
    from tests.conftest import create_member, create_tag

    dad = create_member(client, "张三", nickname="爸爸")
    tag = create_tag(client, "亲子")
    create_trip(
        client,
        title="云南环线",
        cover_photo="2024云南/大理洱海/sunset.jpg",
        summary="七天一千二百公里。",
        member_ids=[dad["id"]],
        tag_ids=[tag["id"]],
    )
    card = client.get("/api/v1/trips").json()[0]
    assert card["cover_photo"] == "2024云南/大理洱海/sunset.jpg"
    assert card["summary"] == "七天一千二百公里。"
    assert card["days_count"] == 7
    assert card["year"] == 2024
    assert card["route"] == ["昆明", "大理", "丽江"]
    assert card["members"][0]["nickname"] == "爸爸"
    assert card["tags"][0]["name"] == "亲子"
    assert card["trip_days"][0]["date"] == "2024-05-01"
    assert "content" not in card  # 列表不拖正文


def test_detail_404_unknown_slug(client):
    assert client.get("/api/v1/trips/nope").status_code == 404


def test_detail_404_for_draft(client):
    trip = create_trip(client, title="未发布", status="draft")
    assert client.get(f"/api/v1/trips/{trip['slug']}").status_code == 404


def test_detail_contents(client, photos_root):
    from tests.conftest import make_jpeg

    make_jpeg(photos_root / "2024云南" / "大理洱海" / "a.jpg")
    make_jpeg(photos_root / "2024云南" / "大理洱海" / "b.jpg")

    trip = create_trip(client, content="<h2>大理</h2><p>风花雪月。</p>")
    detail = client.get(f"/api/v1/trips/{trip['slug']}").json()

    assert detail["content"] == "<h2>大理</h2><p>风花雪月。</p>"
    assert detail["photo_count"] == 2
    group = next(g for g in detail["gallery"] if g["attraction"] == "洱海")
    assert group["count"] == 2
    assert group["photos"] == ["2024云南/大理洱海/a.jpg", "2024云南/大理洱海/b.jpg"]

    erhai = next(a for a in detail["attractions"] if a["name"] == "洱海")
    assert erhai["resolved_lng"] == 100.18  # 景点精调坐标优先
    dianchi = next(a for a in detail["attractions"] if a["name"] == "滇池 · 海埂大坝")
    # 未精调的景点跟随城市中心（昆明市 530100）
    from app.seed import city_rows
    kunming = next(c for c in city_rows() if c["code"] == CITY_CODES["昆明市"])
    assert round(dianchi["resolved_lng"], 4) == round(kunming["lng"], 4)
    assert dianchi["city_display"] == "云南 · 昆明"


def test_detail_prev_next(client):
    older = create_trip(client, title="2018 京都", start_date="2018-04-01", end_date="2018-04-08")
    mid = create_trip(client, title="2023 青岛", start_date="2023-08-12", end_date="2023-08-15")
    newer = create_trip(client, title="2024 云南", start_date="2024-05-01", end_date="2024-05-07")

    mid_detail = client.get(f"/api/v1/trips/{mid['slug']}").json()
    assert mid_detail["prev"] == {"slug": older["slug"], "title": "2018 京都"}  # 时间上更早 = 上一篇
    assert mid_detail["next"] == {"slug": newer["slug"], "title": "2024 云南"}

    newest = client.get(f"/api/v1/trips/{newer['slug']}").json()
    assert newest["next"] is None
