"""slug 生成工具。"""

from app.utils import city_display, city_short, province_short, slugify_title


def test_city_short():
    assert city_short("昆明市") == "昆明"
    assert city_short("大理白族自治州") == "大理"
    assert city_short("阿坝藏族羌族自治州") == "阿坝"
    assert city_short("北京市") == "北京"
    assert city_short("湘西土家族苗族自治州") == "湘西"
    assert city_short("西双版纳傣族自治州") == "西双版纳"
    assert city_short("锡林郭勒盟") == "锡林郭勒"
    assert city_short("大兴安岭地区") == "大兴安岭"


def test_slugify_chinese_to_pinyin():
    assert slugify_title("云南环线") == "yun-nan-huan-xian"
    assert slugify_title("云南环线：从滇池到玉龙") == "yun-nan-huan-xian-cong-dian-chi-dao-yu-long"


def test_slugify_mixed_and_punctuation():
    assert slugify_title("2024 云南 Trip!") == "2024-yun-nan-trip"
    assert slugify_title("A  B——C") == "a-b-c"


def test_slugify_symbols_fallback():
    slug = slugify_title("！！！")
    assert slug.startswith("trip-") and len(slug) == 11


def test_slugify_length_cap():
    assert len(slugify_title("很长的标题" * 30)) <= 64


def test_province_short():
    assert province_short("云南省") == "云南"
    assert province_short("北京市") == "北京"
    assert province_short("内蒙古自治区") == "内蒙古"
    assert province_short("香港特别行政区") == "香港"


def test_city_display():
    assert city_display("云南省", "昆明市") == "云南 · 昆明"
    assert city_display("北京市", "北京市") == "北京"  # 直辖市不重复
    assert city_display("浙江省", "杭州市") == "浙江 · 杭州"
