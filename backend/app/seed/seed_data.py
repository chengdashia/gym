"""Seed initial data: foods, exercises, training templates.

Idempotent: rerunning does not duplicate rows.
"""
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import (
    Exercise,
    Food,
    TrainingTemplate,
    TrainingTemplateDay,
    TrainingTemplateExercise,
)


FOODS = [
    # 主食
    ("米饭", "主食", 116, 25.6, 2.6, 0.3),
    ("面条", "主食", 138, 25.0, 5.0, 1.0),
    ("馒头", "主食", 223, 47.0, 7.0, 1.1),
    ("燕麦", "主食", 389, 66.3, 13.0, 6.5),
    ("全麦面包", "主食", 247, 41.0, 9.0, 3.4),
    ("玉米", "主食", 112, 22.8, 4.0, 1.2),
    ("红薯", "主食", 86, 20.1, 1.6, 0.2),
    ("土豆", "主食", 81, 17.0, 2.0, 0.2),
    # 肉蛋奶
    ("鸡胸肉", "肉蛋奶", 165, 0.0, 31.0, 3.6, "g", 100),
    ("牛肉", "肉蛋奶", 250, 0.0, 26.0, 17.0),
    ("猪肉(瘦)", "肉蛋奶", 143, 1.0, 20.0, 6.2),
    ("鸡蛋", "肉蛋奶", 144, 1.1, 13.3, 8.8, "g", 50),
    ("牛奶", "肉蛋奶", 54, 3.4, 3.0, 3.6, "ml", 100),
    ("酸奶", "肉蛋奶", 72, 9.3, 2.5, 2.6, "g", 100),
    ("三文鱼", "肉蛋奶", 208, 0.0, 20.0, 13.0),
    ("虾", "肉蛋奶", 93, 0.0, 18.6, 1.2),
    # 豆制品
    ("豆腐", "肉蛋奶", 116, 6.2, 12.0, 7.0),
    # 蔬菜
    ("西兰花", "蔬菜", 34, 6.6, 2.8, 0.4),
    ("菠菜", "蔬菜", 24, 3.6, 2.6, 0.4),
    ("生菜", "蔬菜", 15, 2.9, 1.3, 0.3),
    ("西红柿", "蔬菜", 18, 3.9, 0.9, 0.2),
    ("黄瓜", "蔬菜", 16, 2.9, 0.8, 0.2),
    ("胡萝卜", "蔬菜", 41, 9.6, 0.9, 0.2),
    ("白菜", "蔬菜", 13, 1.2, 1.5, 0.2),
    ("蘑菇", "蔬菜", 22, 3.3, 3.1, 0.3),
    # 水果
    ("苹果", "水果", 52, 13.8, 0.3, 0.2),
    ("香蕉", "水果", 89, 22.8, 1.1, 0.3),
    ("橙子", "水果", 47, 11.8, 0.7, 0.2),
    ("蓝莓", "水果", 57, 14.5, 0.7, 0.3),
    ("猕猴桃", "水果", 61, 14.7, 1.0, 0.5),
    ("草莓", "水果", 32, 7.7, 0.7, 0.3),
    # 坚果
    ("杏仁", "坚果", 579, 21.6, 21.2, 49.9),
    ("核桃", "坚果", 654, 13.7, 15.2, 65.2),
    # 零食 / 快餐
    ("巧克力", "零食", 546, 56.0, 7.6, 31.0),
    ("可乐", "饮品", 42, 10.6, 0.1, 0.0),
    ("咖啡(美式)", "饮品", 5, 0.7, 0.3, 0.0),
    ("绿茶", "饮品", 1, 0.2, 0.2, 0.0),
    # 油
    ("橄榄油", "其他", 884, 0.0, 0.0, 100.0),
    # 蛋白质补剂
    ("乳清蛋白粉", "其他", 380, 8.0, 80.0, 5.0),
]

# Values are grams per 100 g for common, minimally processed foods. Foods without
# a sufficiently reliable value intentionally remain NULL.
FIBER_PER_100G = {
    "燕麦": 10.1,
    "全麦面包": 6.0,
    "玉米": 2.4,
    "红薯": 3.0,
    "土豆": 2.2,
    "西兰花": 2.6,
    "菠菜": 2.2,
    "生菜": 1.3,
    "西红柿": 1.2,
    "黄瓜": 0.5,
    "胡萝卜": 2.8,
    "蘑菇": 1.0,
    "苹果": 2.4,
    "香蕉": 2.6,
    "橙子": 2.4,
    "蓝莓": 2.4,
    "猕猴桃": 3.0,
    "草莓": 2.0,
    "杏仁": 12.5,
    "核桃": 6.7,
}

EXERCISES = [
    ("杠铃卧推", "胸", "平躺仰卧，双手略宽于肩握杠铃，下放至胸口推起"),
    ("哑铃卧推", "胸", "平躺仰卧持哑铃推举"),
    ("上斜哑铃推举", "胸", "上斜椅30度，哑铃推举"),
    ("龙门架夹胸", "胸", "站姿龙门架夹胸"),
    ("双杠臂屈伸", "胸", "双杠撑体下降后撑起"),
    ("俯卧撑", "胸", "标准俯卧撑"),
    ("杠铃划船", "背", "俯身杠铃划船"),
    ("坐姿划船", "背", "坐姿器械划船"),
    ("引体向上", "背", "正握单杠引体向上"),
    ("高位下拉", "背", "龙门架高位下拉"),
    ("罗马椅挺身", "背", "罗马椅挺身下放挺起"),
    ("杠铃推举", "肩", "站姿杠铃颈前推举"),
    ("哑铃侧平举", "肩", "站姿哑铃侧平举"),
    ("阿诺德推举", "肩", "旋转动作的阿诺德推举"),
    ("绳索面拉", "肩", "绳索面拉锻炼后束"),
    ("杠铃深蹲", "腿", "后蹲到大腿平行"),
    ("腿举", "腿", "器械腿推"),
    ("腿弯举", "腿", "俯卧/坐姿腿弯举"),
    ("腿屈伸", "腿", "坐姿腿屈伸"),
    ("罗马尼亚硬拉", "腿", "直腿为主的硬拉变体"),
    ("杠铃硬拉", "腿", "传统屈腿硬拉"),
    ("箭步蹲", "腿", "行走箭步蹲"),
    ("二头弯举", "手臂", "哑铃/杠铃二头弯举"),
    ("三头下压", "手臂", "龙门架三头下压"),
    ("仰卧臂屈伸", "手臂", "仰卧杠铃三头臂屈伸"),
    ("弯举集中弯举", "手臂", "坐姿集中弯举"),
    ("仰卧起坐", "核心", "标准仰卧起坐"),
    ("平板支撑", "核心", "俯桥平板支撑"),
    ("卷腹", "核心", "仰卧卷腹"),
    ("俄罗斯转体", "核心", "坐姿转体"),
    ("跑步", "有氧", "慢跑/快跑"),
    ("跳绳", "有氧", "跳绳有氧"),
    ("动感单车", "有氧", "室内单车"),
    ("椭圆机", "有氧", "椭圆机训练"),
]


def _ensure_foods(db: Session) -> None:
    existing_foods = {f.name: f for f in db.execute(select(Food)).scalars().all()}
    for item in FOODS:
        name = item[0]
        if name in existing_foods:
            food = existing_foods[name]
            if food.fiber_per_100g is None and name in FIBER_PER_100G:
                food.fiber_per_100g = Decimal(str(FIBER_PER_100G[name]))
            continue
        category = item[1]
        cal = item[2]
        carb = item[3]
        prot = item[4]
        fat = item[5]
        default_unit = item[6] if len(item) > 6 else "g"
        serving = item[7] if len(item) > 7 else None
        db.add(Food(
            name=name, category=category,
            calories_per_100g=Decimal(str(cal)), carbs_per_100g=Decimal(str(carb)),
            protein_per_100g=Decimal(str(prot)), fat_per_100g=Decimal(str(fat)),
            fiber_per_100g=(
                Decimal(str(FIBER_PER_100G[name])) if name in FIBER_PER_100G else None
            ),
            default_unit=default_unit,
            serving_weight_g=Decimal(str(serving)) if serving else None,
            is_system=1, status="active",
        ))
    db.commit()


def _ensure_exercises(db: Session) -> dict[str, int]:
    rows = db.query(Exercise).filter(Exercise.is_system == 1).all()
    existing = {e.name: e.id for e in rows}
    for item in EXERCISES:
        if item[0] in existing:
            continue
        e = Exercise(name=item[0], body_part=item[1], description=item[2], is_system=1, status="active")
        db.add(e)
        db.flush()
        existing[e.name] = e.id
    db.commit()
    return existing


def _ensure_template(
    db: Session, name: str, description: str, split_type: str,
    difficulty: str, goal: str, days_def: list[tuple[str, bool, int | None, list[tuple[str, int, int, Decimal | None, int]]]]
) -> None:
    t = db.query(TrainingTemplate).filter(TrainingTemplate.name == name).first()
    if t:
        return
    t = TrainingTemplate(
        name=name, description=description,
        split_type=split_type, difficulty=difficulty, goal=goal, status="active",
    )
    db.add(t)
    db.flush()
    # lookup current exercises
    ex_rows = {e.name: e.id for e in db.query(Exercise).filter(Exercise.is_system == 1).all()}
    for idx, day_def in enumerate(days_def, start=1):
        day_name, is_rest, weekday, ex_list = day_def
        d = TrainingTemplateDay(
            template_id=t.id, day_index=idx, day_name=day_name,
            is_rest_day=1 if is_rest else 0, weekday=weekday,
        )
        db.add(d)
        db.flush()
        if is_rest:
            continue
        for sort, (ex_name, sets, reps, weight, rest) in enumerate(ex_list, start=1):
            ex_id = ex_rows.get(ex_name)
            if not ex_id:
                continue
            te = TrainingTemplateExercise(
                template_day_id=d.id, exercise_id=ex_id, sort_order=sort,
                target_sets=sets, target_reps=reps,
                target_weight_kg=Decimal(str(weight)) if weight else None,
                rest_seconds=rest,
            )
            db.add(te)
    db.commit()


def _seed_templates(db: Session) -> None:
    # 三分化（推/拉/腿）
    _ensure_template(
        db, "三分化增肌模板", "经典推/拉/腿三分化，适合中级训练者",
        "three_split", "intermediate", "muscle_gain",
        [
            ("推（胸/肩/三头）", False, 1, [
                ("杠铃卧推", 4, 8, 60.0, 180),
                ("上斜哑铃推举", 4, 10, 22.5, 150),
                ("哑铃侧平举", 3, 12, 8.0, 90),
                ("三头下压", 4, 12, 30.0, 90),
                ("俯卧撑", 3, 15, None, 90),
            ]),
            ("拉（背/二头）", False, 3, [
                ("杠铃划船", 4, 8, 50.0, 180),
                ("高位下拉", 4, 10, 45.0, 120),
                ("引体向上", 3, 8, None, 180),
                ("二头弯举", 4, 10, 12.0, 90),
                ("绳索面拉", 3, 12, 20.0, 90),
            ]),
            ("腿（股四/腘绳/臀）", False, 5, [
                ("杠铃深蹲", 4, 8, 80.0, 240),
                ("罗马尼亚硬拉", 4, 10, 70.0, 180),
                ("腿举", 4, 12, 120.0, 180),
                ("腿弯举", 3, 12, 30.0, 90),
                ("卷腹", 3, 15, None, 60),
            ]),
        ],
    )

    # 四分化（胸/背/肩/腿+手臂）
    _ensure_template(
        db, "四分化增肌模板", "适合中级以上的精细化训练",
        "four_split", "intermediate", "muscle_gain",
        [
            ("胸部", False, 1, [
                ("杠铃卧推", 5, 6, 60.0, 180),
                ("上斜哑铃推举", 4, 8, 22.5, 150),
                ("龙门架夹胸", 4, 12, 25.0, 90),
                ("俯卧撑", 3, 15, None, 90),
            ]),
            ("背部", False, 3, [
                ("引体向上", 4, 8, None, 180),
                ("杠铃划船", 4, 8, 50.0, 180),
                ("高位下拉", 4, 10, 45.0, 120),
                ("罗马椅挺身", 3, 12, None, 90),
            ]),
            ("肩部", False, 5, [
                ("杠铃推举", 4, 6, 35.0, 180),
                ("哑铃侧平举", 4, 12, 8.0, 90),
                ("阿诺德推举", 3, 10, 10.0, 120),
                ("绳索面拉", 4, 12, 20.0, 90),
                ("三头下压", 3, 12, 30.0, 90),
            ]),
            ("腿部 + 手臂", False, 7, [
                ("杠铃深蹲", 5, 6, 80.0, 240),
                ("罗马尼亚硬拉", 4, 8, 70.0, 180),
                ("腿弯举", 4, 12, 30.0, 90),
                ("二头弯举", 4, 10, 12.0, 90),
                ("弯举集中弯举", 3, 12, 8.0, 90),
            ]),
        ],
    )

    # 五分化
    _ensure_template(
        db, "五分化增肌模板", "每天一个部位，恢复充分",
        "five_split", "intermediate", "muscle_gain",
        [
            ("胸部", False, 1, [("杠铃卧推", 4, 8, 60.0, 180),
                                ("上斜哑铃推举", 4, 10, 22.5, 150),
                                ("龙门架夹胸", 3, 12, 25.0, 90),
                                ("俯卧撑", 3, 12, None, 90)]),
            ("背部", False, 2, [("引体向上", 4, 8, None, 180),
                                ("杠铃划船", 4, 8, 50.0, 180),
                                ("高位下拉", 3, 12, 45.0, 120)]),
            ("肩部 + 三头", False, 3, [("杠铃推举", 4, 8, 35.0, 180),
                                        ("哑铃侧平举", 4, 12, 8.0, 90),
                                        ("绳索面拉", 3, 12, 20.0, 90),
                                        ("三头下压", 4, 10, 30.0, 90)]),
            ("腿部", False, 4, [("杠铃深蹲", 4, 8, 80.0, 240),
                                ("罗马尼亚硬拉", 4, 8, 70.0, 180),
                                ("腿举", 4, 12, 120.0, 180),
                                ("腿弯举", 3, 12, 30.0, 90)]),
            ("手臂", False, 5, [("二头弯举", 4, 10, 12.0, 90),
                                ("三头下压", 4, 10, 30.0, 90),
                                ("弯举集中弯举", 3, 10, 8.0, 90),
                                ("仰卧臂屈伸", 3, 10, 25.0, 90)]),
        ],
    )

    # 减脂基础模板（有氧循环）
    _ensure_template(
        db, "减脂基础模板", "抗阻 + 有氧循环,适合减脂期",
        "fat_loss_split", "beginner", "fat_loss",
        [
            ("全身循环 A", False, 1, [("杠铃深蹲", 3, 12, 50.0, 120),
                                       ("杠铃卧推", 3, 12, 40.0, 120),
                                       ("杠铃划船", 3, 12, 40.0, 120),
                                       ("跑步", 1, 20, None, 0),
                                       ("平板支撑", 3, 45, None, 60)]),
            ("全身循环 B", False, 3, [("罗马尼亚硬拉", 3, 12, 50.0, 120),
                                       ("哑铃卧推", 3, 12, 18.0, 120),
                                       ("高位下拉", 3, 12, 40.0, 120),
                                       ("跳绳", 1, 15, None, 0),
                                       ("卷腹", 3, 15, None, 60)]),
            ("有氧日", False, 5, [("动感单车", 1, 30, None, 0),
                                  ("卷腹", 3, 15, None, 60)]),
            ("休息", True, 2, []),
            ("休息", True, 4, []),
            ("休息", True, 6, []),
            ("休息", True, 7, []),
        ],
    )

    # 新手全身训练
    _ensure_template(
        db, "新手全身训练模板", "每周3次全身训练，适合训练新手",
        "full_body", "beginner", "general",
        [
            ("全身训练 A", False, 1, [("杠铃深蹲", 3, 8, 40.0, 150),
                                       ("杠铃卧推", 3, 8, 30.0, 150),
                                       ("杠铃划船", 3, 8, 30.0, 150)]),
            ("休息", True, 2, []),
            ("全身训练 B", False, 3, [("罗马尼亚硬拉", 3, 8, 40.0, 150),
                                       ("哑铃卧推", 3, 10, 14.0, 120),
                                       ("高位下拉", 3, 10, 35.0, 120)]),
            ("休息", True, 4, []),
            ("全身训练 A", False, 5, [("杠铃深蹲", 3, 8, 40.0, 150),
                                       ("哑铃侧平举", 3, 12, 6.0, 90),
                                       ("二头弯举", 3, 10, 10.0, 90)]),
            ("休息", True, 6, []),
            ("休息/有氧", True, 7, []),
        ],
    )


def run_seed() -> dict:
    db = SessionLocal()
    try:
        _ensure_foods(db)
        _ensure_exercises(db)
        _seed_templates(db)
        n_foods = db.query(Food).filter(Food.is_system == 1).count()
        n_ex = db.query(Exercise).filter(Exercise.is_system == 1).count()
        n_t = db.query(TrainingTemplate).count()
        return {"foods": n_foods, "exercises": n_ex, "templates": n_t}
    finally:
        db.close()


if __name__ == "__main__":
    import json
    print(json.dumps(run_seed(), ensure_ascii=False))
