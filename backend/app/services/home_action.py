def choose_primary_action(
    *, needs_profile: bool, has_goal: bool, meal_recorded: bool,
    training_status: str, weight_recorded_today: bool,
) -> dict:
    if needs_profile:
        return {"type": "complete_profile", "title": "补充身体资料", "description": "补充后可生成更准确的营养建议", "url": "/pages/mine/profile"}
    if not has_goal:
        return {"type": "set_nutrition_goal", "title": "设置每日营养目标", "description": "先确定今天的热量和营养目标", "url": "/pages/mine/goals"}
    if not meal_recorded:
        return {"type": "record_meal", "title": "记录这一餐", "description": "及时记录，今天的剩余摄入更清楚", "url": "/pages/diet/add"}
    if training_status == "in_progress":
        return {"type": "resume_training", "title": "继续今日训练", "description": "训练还没有结束", "url": "/pages/training/index"}
    if training_status == "not_started":
        return {"type": "start_training", "title": "开始今日训练", "description": "按计划完成今天的动作", "url": "/pages/training/index"}
    if not weight_recorded_today:
        return {"type": "record_weight", "title": "记录今日体重", "description": "持续记录才能看清真实趋势", "url": "/pages/mine/account?action=weight"}
    return {"type": "day_complete", "title": "今天的主要任务已完成", "description": "保持节奏，明天继续", "url": "/pages/stats/index"}
