from copy import deepcopy


_TEMPLATES = (
    {
        "code": "balanced_cut", "name": "均衡减脂", "version": 1,
        "description": "温和热量缺口与均衡宏量营养分配",
        "rules": {"strict": False, "requires_fiber": False},
        "applicability": {"default": True},
    },
    {
        "code": "time_restricted_16_8", "name": "16:8 限时进食", "version": 1,
        "description": "在连续 8 小时窗口内安排计划餐",
        "rules": {"strict": False, "requires_fiber": False, "eating_window_hours": 8},
        "applicability": {"requires_eating_window": True},
    },
    {
        "code": "carb_taper_532", "name": "532 碳水渐降", "version": 1,
        "description": "锁定蛋白质和脂肪，仅按评估结果渐进调整碳水",
        "rules": {"strict": False, "requires_fiber": False, "ratios": ["5/3/2", "4/4/2"]},
        "applicability": {"requires_weight_monitoring": True},
    },
    {
        "code": "ketogenic", "name": "生酮饮食", "version": 1,
        "description": "严格净碳水方案，建议在专业人员指导下进行",
        "rules": {"strict": True, "requires_fiber": True},
        "applicability": {"professional_guidance_recommended": True},
    },
)


def get_active_templates() -> list[dict]:
    return deepcopy(list(_TEMPLATES))
