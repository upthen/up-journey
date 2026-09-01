"""health / meta / 城市字典。"""


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_meta_empty(client):
    r = client.get("/api/v1/meta")
    assert r.status_code == 200
    assert r.json() == {"members": [], "tags": []}


def test_meta_lists_members_and_tags(client):
    from tests.conftest import create_member, create_tag

    create_member(client, "张三", nickname="爸爸")
    create_member(client, "张小四", nickname="哥哥", is_child=True)
    create_tag(client, "亲子")

    r = client.get("/api/v1/meta")
    data = r.json()
    assert [m["nickname"] for m in data["members"]] == ["爸爸", "哥哥"]
    assert data["members"][1]["is_child"] is True
    assert [t["name"] for t in data["tags"]] == ["亲子"]


def test_cities_returns_full_dict(client):
    r = client.get("/api/v1/admin/cities", params={"level": 1})
    assert r.status_code == 200
    provinces = r.json()
    assert len(provinces) == 34  # 34 个省级行政区（含港澳台）
    names = {p["name"] for p in provinces}
    assert "云南省" in names and "香港特别行政区" in names and "台湾省" in names


def test_cities_kunming(client):
    r = client.get("/api/v1/admin/cities", params={"province": "530000"})
    assert r.status_code == 200
    cities = r.json()
    kunming = next(c for c in cities if c["name"] == "昆明市")
    assert kunming["code"] == "530100"
    assert kunming["province_name"] == "云南省"
    assert round(kunming["lng"], 1) == 102.7
    assert round(kunming["lat"], 1) == 25.0


def test_cities_municipality_has_city_row(client):
    """直辖市同时有省级与市级条目（统计口径：同时计入省、市两项）。"""
    r = client.get("/api/v1/admin/cities", params={"province": "110000"})
    beijing_rows = r.json()
    assert any(c["code"] == "110100" and c["level"] == 2 for c in beijing_rows)


def test_cities_hk_macau_taiwan(client):
    for prov, city_name in (("810000", "香港"), ("820000", "澳门"), ("710000", "台湾")):
        r = client.get("/api/v1/admin/cities", params={"province": prov})
        assert any(c["name"] == city_name for c in r.json()), city_name
