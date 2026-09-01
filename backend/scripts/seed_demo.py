"""本地演示数据：家庭成员、标签、三次旅行 + 相册样例图（复制自原型 assets）。

用途：本地开发 / 浏览器验收，不进生产容器。幂等：已有旅行时跳过。
用法：uv run python scripts/seed_demo.py
"""

import shutil
import sys
from datetime import date
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.config import get_settings, photos_root  # noqa: E402
from app.db import SessionLocal, engine  # noqa: E402
from app.models import Attraction, Base, City, FamilyMember, Tag, Trip, TripCity, TripDay  # noqa: E402
from app.seed import seed_cities  # noqa: E402

IMG = BACKEND.parent / "docs" / "prototype" / "assets" / "img"

ALBUMS = {
    "2024云南/昆明滇池": ["gulls-boy.jpg"],
    "2024云南/大理洱海": ["erhai-sunset.jpg", "erhai-pano.jpg", "erhai-village.jpg"],
    "2024云南/玉龙雪山": ["yulong-peak.jpg", "yulong-trail.jpg", "lanmeigu.jpg", "ganhaizi.jpg", "snow-family.jpg"],
    "2023四川/四姑娘山": ["stars.jpg"],
    "2023青岛/礁石滩": ["qingdao-beach.jpg", "qingdao-tide.jpg"],
    "2018日本/京都": ["kyoto.jpg", "kyoto-v.jpg"],
}


def copy_albums() -> None:
    root = photos_root(get_settings())
    for rel, files in ALBUMS.items():
        dst = root / rel
        dst.mkdir(parents=True, exist_ok=True)
        for f in files:
            src = IMG / f
            if src.exists():
                shutil.copy2(src, dst / f)


def main() -> None:
    Base.metadata.create_all(engine)
    db = SessionLocal()
    if db.query(Trip).count():
        print("已有旅行数据，跳过演示数据导入")
        return
    seed_cities(db)
    copy_albums()

    kunming, dali, lijiang, chengdu, abazhou, qingdao = (
        db.get(City, code) for code in ("530100", "532900", "530700", "510100", "513200", "370200")
    )
    dad = FamilyMember(name="张三", nickname="爸爸")
    mom = FamilyMember(name="李四", nickname="妈妈")
    boy = FamilyMember(name="张小四", nickname="哥哥", is_child=True)
    tags = {t.name: t for t in (Tag(name=n) for n in ("亲子", "自驾", "高原", "海滨", "境外", "春樱"))}
    db.add_all([dad, mom, boy, *tags.values()])

    yunnan = Trip(
        slug="yun-nan-huan-xian-cong-dian-chi-dao-yu-long-2024",
        title="云南环线：从滇池到玉龙",
        start_date=date(2024, 5, 1),
        end_date=date(2024, 5, 7),
        summary="七天一千二百公里，滇池的海鸥、洱海的日落、玉龙的初雪。哥哥在缆车上睡着了，醒来第一句话是“云在我脚下”。",
        content=(
            "<p>出发前一晚，哥哥把行李箱开了又关、关了又开，最后塞进去一只望远镜和三包海鸥食。</p>"
            "<h2>大理：风花雪月的注脚</h2>"
            "<p>我们沿着环海西路慢慢开，左边是苍山十九峰的黛色剪影，右边是洱海一整面被夕阳烫金的水。</p>"
            "<blockquote>风花雪月原来不是成语，是大理的四种天气：下关风、上关花、苍山雪、洱海月。</blockquote>"
            "<h2>玉龙：第一次见雪的人</h2>"
            "<p>索道爬升到四千五百米时，哥哥在缆车里睡着了。醒来推窗见雪，他说的第一句话是：“云在我脚下。”</p>"
        ),
        cover_photo="2024云南/大理洱海/erhai-sunset.jpg",
        status="published",
    )
    yunnan.cities = [
        TripCity(city_code=kunming.code, sort_order=0),
        TripCity(city_code=dali.code, sort_order=1),
        TripCity(city_code=lijiang.code, sort_order=2),
    ]
    yunnan.days = [
        TripDay(day_index=i + 1, date=date(2024, 5, i + 1), title=t, note=n)
        for i, (t, n) in enumerate([
            ("海埂大坝喂红嘴鸥", "晚宿翠湖旁"), ("西山 → 动车赴大理", None), ("洱海 S 湾骑行", None),
            ("崇圣寺三塔 · 古城", None), ("丽江 · 万古楼", None), ("玉龙雪山 · 蓝月谷", None), ("返程 · 三义机场", None),
        ])
    ]
    yunnan.attractions = [
        Attraction(name="滇池 · 海埂大坝", city_code=kunming.code, album_rel_path="2024云南/昆明滇池",
                   note="成千上万只红嘴鸥盘旋成一团灰白的云。哥哥举着饲料，海鸥落在手腕上啄食。"),
        Attraction(name="大理古城", city_code=dali.code, album_rel_path=None,
                   note="风花雪月不是成语，是大理的四种天气。"),
        Attraction(name="洱海", city_code=dali.code, album_rel_path="2024云南/大理洱海", lng=100.18, lat=25.75,
                   note="S 湾的日落持续了整整四十分钟，云从橘红烧到绛紫，最后沉入墨蓝。没有人说话。"),
        Attraction(name="玉龙雪山", city_code=lijiang.code, album_rel_path="2024云南/玉龙雪山",
                   note="哥哥在缆车里睡着了，醒来推窗见雪：“云在我脚下。”他人生第一场真正的雪。"),
    ]
    yunnan.members = [dad, mom, boy]
    yunnan.tags = [tags["亲子"], tags["自驾"]]

    sichuan = Trip(
        slug="si-gu-niang-shan-xia-de-xing-kong-2023",
        title="四姑娘山下的星空",
        start_date=date(2023, 10, 2),
        end_date=date(2023, 10, 6),
        summary="翻过巴朗山垭口的那一刻，云海在脚下铺开。夜里的高原冷得刺骨，星星却多到让人生出敬畏。",
        cover_photo="2023四川/四姑娘山/stars.jpg",
        status="published",
    )
    sichuan.cities = [TripCity(city_code=chengdu.code, sort_order=0), TripCity(city_code=abazhou.code, sort_order=1)]
    sichuan.days = [
        TripDay(day_index=1, date=date(2023, 10, 2), title="成都集合 · 夜奔巴朗山"),
        TripDay(day_index=2, date=date(2023, 10, 3), title="猫鼻梁看四峰日出"),
        TripDay(day_index=3, date=date(2023, 10, 4), title="双桥沟一日"),
        TripDay(day_index=4, date=date(2023, 10, 5), title="长坪沟徒步"),
        TripDay(day_index=5, date=date(2023, 10, 6), title="返程 · 天府机场"),
    ]
    sichuan.attractions = [
        Attraction(name="四姑娘山 · 双桥沟", city_code=abazhou.code, album_rel_path="2023四川/四姑娘山", lng=102.90, lat=31.10,
                   note="翻过巴朗山垭口的那一刻，云海在脚下铺开。夜里的星星多到让人生出敬畏。"),
        Attraction(name="宽窄巷子", city_code=chengdu.code,
                   note="火锅、盖碗茶和采耳，成都负责把旅行的开头调得松弛。"),
    ]
    sichuan.members = [dad, mom]
    sichuan.tags = [tags["自驾"], tags["高原"]]

    qingdao_trip = Trip(
        slug="gan-hai-de-xiao-hai-2023",
        title="赶海的小孩",
        start_date=date(2023, 8, 12),
        end_date=date(2023, 8, 15),
        summary="退潮后的礁石滩是一座没有围墙的自然博物馆。哥哥蹲了两小时不肯走，带回一只寄居蟹和满裤腿的沙。",
        cover_photo="2023青岛/礁石滩/qingdao-beach.jpg",
        status="published",
    )
    qingdao_trip.cities = [TripCity(city_code=qingdao.code, sort_order=0)]
    qingdao_trip.days = [
        TripDay(day_index=1, date=date(2023, 8, 12), title="抵青岛 · 台东夜市"),
        TripDay(day_index=2, date=date(2023, 8, 13), title="礁石滩赶海一整天"),
        TripDay(day_index=3, date=date(2023, 8, 14), title="八大关 · 啤酒屋"),
        TripDay(day_index=4, date=date(2023, 8, 15), title="返程"),
    ]
    qingdao_trip.attractions = [
        Attraction(name="青岛 · 礁石滩", city_code=qingdao.code, album_rel_path="2023青岛/礁石滩", lng=120.35, lat=36.05,
                   note="退潮后的礁石滩是一座没有围墙的自然博物馆。哥哥蹲了两小时，带回一只寄居蟹。"),
    ]
    qingdao_trip.members = [dad, mom, boy]
    qingdao_trip.tags = [tags["亲子"], tags["海滨"]]

    kyoto = Trip(
        slug="luo-ying-shi-jie-you-feng-jun-2018",
        title="落樱时节，又逢君",
        start_date=date(2018, 4, 1),
        end_date=date(2018, 4, 8),
        summary="哲学之道的樱吹雪落了满肩。第一次带哥哥出国，他学会了说 arigatou。",
        cover_photo="2018日本/京都/kyoto.jpg",
        country="日本",
        status="published",
    )
    kyoto.cities = [TripCity(city_name="大阪", sort_order=0), TripCity(city_name="京都", lng=135.80, lat=35.03, sort_order=1), TripCity(city_name="奈良", sort_order=2)]
    kyoto.days = [
        TripDay(day_index=i + 1, date=date(2018, 4, i + 1), title=t)
        for i, t in enumerate([
            "抵大阪 · 道顿堀", "大阪 — 京都", "哲学之道 · 樱吹雪", "岚山小火车",
            "伏见稻荷 · 千本鸟居", "奈良 · 鹿", "回大阪 · 环球影城", "返程",
        ])
    ]
    kyoto.attractions = [
        Attraction(name="京都 · 哲学之道", city_code=None, album_rel_path="2018日本/京都",
                   note="樱吹雪落了满肩。第一次带哥哥出国，他学会了说 arigatou。"),
    ]
    kyoto.members = [dad, mom, boy]
    kyoto.tags = [tags["境外"], tags["春樱"]]

    db.add_all([yunnan, sichuan, qingdao_trip, kyoto])
    db.commit()
    print(f"演示数据就绪：4 次旅行 · 相册样例已复制到 {photos_root(get_settings())}")


if __name__ == "__main__":
    main()
