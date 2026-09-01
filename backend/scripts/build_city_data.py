"""构建城市字典 city_data.json（docs/database.md 种子数据节）。

数据源 = 阿里 DataV 行政区划树 https://geo.datav.aliyun.com/areas_v3/bound/all.json
（行政区划码 × 中心经纬度 × 名称）。产出：
  - 34 个省级单位（含港澳台），province_name 与前端 china GeoJSON 的 name 严格一致；
  - 全部地级市；直辖市/港澳台在 DataV 树上无市级子节点，按国家统计局市级码合成一条
    （110100 北京市 / 120100 / 310100 / 500100 / 810100 香港 / 820100 澳门 / 710100 台湾），
    使"直辖市同时计入省、市两项"的统计口径有数据可依。

用法：uv run python scripts/build_city_data.py [已下载的 all.json 路径]
不带参数则现场下载。
"""

import json
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parents[1] / "app" / "city_data.json"
DATAV_URL = "https://geo.datav.aliyun.com/areas_v3/bound/all.json"
GEOJSON = REPO / "docs" / "prototype" / "assets" / "china.json"

# 直辖市/港澳台 → 合成市级条目 (code, name)
SYNTHETIC_CITIES = {
    110000: ("110100", "北京市"),
    120000: ("120100", "天津市"),
    310000: ("310100", "上海市"),
    500000: ("500100", "重庆市"),
    810000: ("810100", "香港"),
    820000: ("820100", "澳门"),
    710000: ("710100", "台湾"),
}

PROVINCE_SUFFIXES = ("壮族自治区", "维吾尔自治区", "回族自治区", "自治区", "特别行政区", "省", "市")


def province_short(name: str) -> str:
    """云南省→云南，北京市→北京，内蒙古自治区→内蒙古（仅用于展示，不影响存储）。"""
    for suf in PROVINCE_SUFFIXES:
        if name.endswith(suf) and len(name) > len(suf):
            return name[: -len(suf)]
    return name


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if src and src.exists():
        areas = json.loads(src.read_text(encoding="utf-8"))
    else:
        print(f"downloading {DATAV_URL} ...")
        with urllib.request.urlopen(DATAV_URL, timeout=60) as resp:
            areas = json.loads(resp.read().decode("utf-8"))

    provinces = [a for a in areas if a.get("level") == "province"]
    cities = [a for a in areas if a.get("level") == "city"]

    geo_names = {
        f["properties"].get("name")
        for f in json.loads(GEOJSON.read_text(encoding="utf-8"))["features"]
        if f["properties"].get("name")
    }
    for p in provinces:
        assert p["name"] in geo_names, f"省份名与 GeoJSON 不一致: {p['name']}"
    assert len(provinces) == 34, f"省级单位应为 34 个，实际 {len(provinces)}"

    prov_by_code = {a["adcode"]: a for a in provinces}
    rows: list[dict] = []
    for p in provinces:
        rows.append(
            {
                "code": str(p["adcode"]),
                "name": p["name"],
                "province_code": str(p["adcode"]),
                "province_name": p["name"],
                "level": 1,
                "lng": p["lng"],
                "lat": p["lat"],
            }
        )

    for c in cities:
        parent = prov_by_code.get(c.get("parent"))
        if parent is None:  # 省直辖县级市挂在省下时 parent 一定可查；防御意外层级
            continue
        rows.append(
            {
                "code": str(c["adcode"]),
                "name": c["name"],
                "province_code": str(parent["adcode"]),
                "province_name": parent["name"],
                "level": 2,
                "lng": c["lng"],
                "lat": c["lat"],
            }
        )

    for prov_code, (code, name) in SYNTHETIC_CITIES.items():
        p = prov_by_code[prov_code]
        rows.append(
            {
                "code": code,
                "name": name,
                "province_code": str(prov_code),
                "province_name": p["name"],
                "level": 2,
                "lng": p["lng"],
                "lat": p["lat"],
            }
        )

    OUT.write_text(
        json.dumps(rows, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    n_prov = sum(1 for r in rows if r["level"] == 1)
    n_city = sum(1 for r in rows if r["level"] == 2)
    print(f"wrote {OUT}: {n_prov} 省级 + {n_city} 市 = {len(rows)} rows")


if __name__ == "__main__":
    main()
