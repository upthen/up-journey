"""地名展示与 slug 工具。"""

import hashlib
import re
import unicodedata

from pypinyin import Style, lazy_pinyin

PROVINCE_SUFFIXES = ("壮族自治区", "维吾尔自治区", "回族自治区", "自治区", "特别行政区", "省", "市")


def province_short(name: str) -> str:
    """云南省→云南，北京市→北京，内蒙古自治区→内蒙古。"""
    for suf in PROVINCE_SUFFIXES:
        if name.endswith(suf) and len(name) > len(suf):
            return name[: -len(suf)]
    return name


CITY_SUFFIXES = ("自治州", "地区", "盟", "林区", "市")

# 自治州名中的民族限定词（大理白族→大理、阿坝藏族羌→阿坝）：取首个出现位置截断
ETHNIC_TERMS = (
    "汉族", "蒙古族", "回族", "藏族", "维吾尔族", "苗族", "彝族", "壮族", "布依族", "朝鲜族",
    "满族", "侗族", "瑶族", "白族", "土家族", "哈尼族", "哈萨克族", "傣族", "黎族", "傈僳族",
    "佤族", "畲族", "拉祜族", "水族", "东乡族", "纳西族", "景颇族", "柯尔克孜族", "土族",
    "达斡尔族", "仫佬族", "羌族", "布朗族", "撒拉族", "毛南族", "仡佬族", "锡伯族", "阿昌族",
    "普米族", "塔吉克族", "怒族", "乌孜别克族", "俄罗斯族", "鄂温克族", "德昂族", "保安族",
    "裕固族", "京族", "塔塔尔族", "独龙族", "鄂伦春族", "赫哲族", "门巴族", "珞巴族", "基诺族",
)


def _strip_ethnic(name: str) -> str:
    cut = len(name)
    for term in ETHNIC_TERMS:
        i = name.find(term)
        if 0 < i < cut:
            cut = i
    return name[:cut]


def city_short(name: str) -> str:
    """昆明市→昆明；大理白族自治州→大理（约定俗成短名，统计按 code 去重不受影响）。"""
    for suf in CITY_SUFFIXES:
        if name.endswith(suf) and len(name) > len(suf):
            return _strip_ethnic(name[: -len(suf)])
    return name


def city_display(province_name: str, city_name: str) -> str:
    """地图/卡片上的城市显示名：云南 · 昆明；直辖市只显示 北京。"""
    prov = province_short(province_name)
    city = city_short(city_name)
    if city.startswith(prov):  # 北京市/北京市 → 北京
        return city
    return f"{prov} · {city}"


_slug_cleanup = re.compile(r"[^a-z0-9]+")


def slugify_title(title: str) -> str:
    """由标题生成 URL slug：中文逐字转拼音、非字母数字折叠为 -。

    云南环线 → yun-nan-huan-xian；纯符号标题退化为内容寻址短 slug。
    """
    normalized = unicodedata.normalize("NFKC", title)
    # 按字转拼音（errors=default 保留数字/拉丁字符），非字母数字随后折叠为 -
    segments = lazy_pinyin(normalized, style=Style.NORMAL, errors="default")
    text = "-".join(str(seg).lower() for seg in segments if str(seg).strip())
    slug = _slug_cleanup.sub("-", text).strip("-")
    slug = slug[:64].strip("-")
    if not slug:
        digest = hashlib.sha1(title.encode("utf-8")).hexdigest()[:6]
        slug = f"trip-{digest}"
    return slug
