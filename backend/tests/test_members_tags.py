"""家庭成员与标签 CRUD。"""

from tests.conftest import create_member, create_tag


def test_member_crud_full_cycle(client):
    created = create_member(client, "李四", nickname="妈妈")
    assert created["id"] > 0
    assert created == {"id": created["id"], "name": "李四", "nickname": "妈妈", "is_child": False}

    listed = client.get("/api/v1/admin/members").json()
    assert listed == [created]

    updated = client.put(f"/api/v1/admin/members/{created['id']}", json={"nickname": "二姨"})
    assert updated.status_code == 200
    assert updated.json()["nickname"] == "二姨"
    assert updated.json()["name"] == "李四"  # 未传字段保持不变

    r = client.delete(f"/api/v1/admin/members/{created['id']}")
    assert r.status_code == 204
    assert client.get("/api/v1/admin/members").json() == []


def test_member_update_404(client):
    assert client.put("/api/v1/admin/members/999", json={"name": "x"}).status_code == 404


def test_member_delete_404(client):
    assert client.delete("/api/v1/admin/members/999").status_code == 404


def test_member_name_required(client):
    assert client.post("/api/v1/admin/members", json={"nickname": "无名字"}).status_code == 422


def test_member_delete_removes_trip_association(client, db):
    from tests.conftest import create_trip

    member = create_member(client, "王五")
    trip = create_trip(client, member_ids=[member["id"]])
    assert trip["members"][0]["name"] == "王五"

    client.delete(f"/api/v1/admin/members/{member['id']}")

    detail = client.get(f"/api/v1/admin/trips/{trip['id']}").json()
    assert detail["members"] == []
    # trip_member 关联行随 ON DELETE CASCADE 清除（SQLite 不强制 FK，验证应用层 delete-orphan 语义）
    from sqlalchemy import text
    n = db.execute(text("SELECT COUNT(*) FROM trip_member")).scalar()
    assert n == 0


def test_tag_crud(client):
    tag = create_tag(client, "亲子")
    assert client.get("/api/v1/admin/tags").json() == [tag]

    r = client.put(f"/api/v1/admin/tags/{tag['id']}", json={"name": "遛娃"})
    assert r.status_code == 200
    assert r.json()["name"] == "遛娃"

    assert client.delete(f"/api/v1/admin/tags/{tag['id']}").status_code == 204
    assert client.get("/api/v1/admin/tags").json() == []


def test_tag_duplicate_409(client):
    create_tag(client, "自驾")
    r = client.post("/api/v1/admin/tags", json={"name": "自驾"})
    assert r.status_code == 409


def test_tag_rename_to_existing_409(client):
    a = create_tag(client, "海岛")
    create_tag(client, "高原")
    r = client.put(f"/api/v1/admin/tags/{a['id']}", json={"name": "高原"})
    assert r.status_code == 409


def test_tag_404(client):
    assert client.put("/api/v1/admin/tags/9", json={"name": "x"}).status_code == 404
    assert client.delete("/api/v1/admin/tags/9").status_code == 404
