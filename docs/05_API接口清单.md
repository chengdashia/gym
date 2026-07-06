# API 接口清单

> Base URL：`/api/v1`  
> 认证方式：`Authorization: Bearer <access_token>`  
> 响应格式：统一 JSON

---

## 1. 通用响应格式

### 1.1 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

### 1.2 失败响应

```json
{
  "code": 40001,
  "message": "参数错误",
  "data": null
}
```

### 1.3 通用错误码

| code | 含义 |
|---|---|
| 0 | 成功 |
| 40001 | 参数错误 |
| 40101 | 未登录或 token 失效 |
| 40301 | 无权限 |
| 40401 | 资源不存在 |
| 40901 | 数据冲突 |
| 50001 | 服务异常 |
| 60001 | 图片上传失败 |
| 60002 | 食物识别失败 |

---

## 2. 认证接口

### 2.1 微信静默登录

`POST /auth/wechat-login`

请求：

```json
{
  "code": "wx_login_code"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "token",
    "token_type": "Bearer",
    "user": {
      "id": 1,
      "nickname": "用户",
      "avatar_url": "",
      "is_new_user": true,
      "agreement_confirmed": false
    }
  }
}
```

---

## 3. 用户接口

### 3.1 获取当前用户

`GET /users/me`

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "nickname": "用户",
    "avatar_url": "",
    "phone": null,
    "is_member": false,
    "member_expired_at": null,
    "profile": {
      "gender": "male",
      "age": 28,
      "height_cm": 175,
      "current_weight_kg": 70,
      "target_weight_kg": 65,
      "fitness_goal": "fat_loss",
      "training_frequency": "3-4"
    }
  }
}
```

### 3.2 更新用户资料

`PUT /users/me`

请求：

```json
{
  "nickname": "用户昵称",
  "avatar_url": "https://example.com/avatar.png",
  "gender": "male",
  "age": 28,
  "height_cm": 175,
  "current_weight_kg": 70,
  "target_weight_kg": 65,
  "fitness_goal": "fat_loss",
  "training_frequency": "3-4"
}
```

### 3.3 确认协议

`POST /users/agreement-confirm`

请求：

```json
{
  "agreement_version": "v1.0",
  "privacy_version": "v1.0"
}
```

### 3.4 获取营养目标

`GET /users/nutrition-goal`

### 3.5 更新营养目标

`PUT /users/nutrition-goal`

请求：

```json
{
  "calories_kcal": 1800,
  "carbs_g": 180,
  "protein_g": 120,
  "fat_g": 50
}
```

### 3.6 推荐营养目标

`POST /users/nutrition-goal/recommend`

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "calories_kcal": 1800,
    "carbs_g": 180,
    "protein_g": 120,
    "fat_g": 50,
    "formula_note": "基于基础信息和目标的估算值，可手动调整"
  }
}
```

### 3.7 获取提醒设置

`GET /users/reminders`

### 3.8 更新提醒设置

`PUT /users/reminders`

请求：

```json
{
  "items": [
    {"reminder_type": "diet", "enabled": true, "reminder_time": "08:30", "weekdays": "1,2,3,4,5,6,7"},
    {"reminder_type": "training", "enabled": true, "reminder_time": "19:00", "weekdays": "1,3,5"},
    {"reminder_type": "weight", "enabled": false, "reminder_time": "07:30", "weekdays": "1,2,3,4,5,6,7"}
  ]
}
```

### 3.9 删除个人数据

`POST /users/delete-data`

### 3.10 注销账号

`POST /users/cancel-account`

---

## 4. 首页接口

### 4.1 首页聚合

`GET /home/summary?date=2026-07-05`

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "date": "2026-07-05",
    "diet": {
      "calories_kcal": 1200,
      "calories_goal": 1800,
      "carbs_g": 130,
      "carbs_goal": 180,
      "protein_g": 85,
      "protein_goal": 120,
      "fat_g": 35,
      "fat_goal": 50,
      "record_count": 5
    },
    "training": {
      "status": "not_started",
      "plan_id": 1,
      "plan_day_id": 2,
      "session_id": null,
      "title": "胸部训练",
      "exercise_count": 4,
      "is_rest_day": false
    },
    "weight": {
      "current_weight_kg": 70,
      "target_weight_kg": 65,
      "diff_kg": 5,
      "last_recorded_at": "2026-07-05 08:00:00"
    }
  }
}
```

---

## 5. 食物接口

### 5.1 搜索食物

`GET /foods/search?keyword=鸡胸肉&page=1&page_size=20`

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "source": "system",
        "name": "鸡胸肉",
        "category": "肉蛋奶",
        "calories_per_100g": 165,
        "carbs_per_100g": 0,
        "protein_per_100g": 31,
        "fat_per_100g": 3.6,
        "default_unit": "g",
        "serving_weight_g": 100
      }
    ],
    "total": 1
  }
}
```

### 5.2 获取食物详情

`GET /foods/{id}?source=system|custom`

### 5.3 创建自定义食物

`POST /foods/custom`

请求：

```json
{
  "name": "自制鸡胸肉饭",
  "category": "主食",
  "calories_per_100g": 180,
  "carbs_per_100g": 20,
  "protein_per_100g": 15,
  "fat_per_100g": 4,
  "default_unit": "g",
  "serving_weight_g": 300
}
```

---

## 6. 饮食记录接口

### 6.1 查询饮食记录

`GET /diet/records?date=2026-07-05`

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "date": "2026-07-05",
    "summary": {
      "calories_kcal": 1200,
      "carbs_g": 130,
      "protein_g": 85,
      "fat_g": 35
    },
    "meals": {
      "breakfast": [],
      "lunch": [],
      "dinner": [],
      "snack": []
    }
  }
}
```

### 6.2 创建饮食记录

`POST /diet/records`

请求：

```json
{
  "record_date": "2026-07-05",
  "record_time": "12:30",
  "meal_type": "lunch",
  "food_source": "system",
  "food_id": 1,
  "custom_food_id": null,
  "unit_type": "g",
  "amount_g": 150,
  "serving_count": null,
  "image_url": null,
  "save_image": false,
  "note": "午餐"
}
```

### 6.3 更新饮食记录

`PUT /diet/records/{id}`

### 6.4 删除饮食记录

`DELETE /diet/records/{id}`

---

## 7. 上传与 AI 识别接口

### 7.1 上传图片

`POST /uploads/image`

Content-Type：`multipart/form-data`

字段：

- file
- usage_type：`food_recognition` / `diet_record`
- temporary：true/false

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "file_id": 1,
    "file_url": "https://example.com/uploads/1.jpg",
    "is_temporary": true
  }
}
```

### 7.2 食物识别

`POST /ai/food-recognition`

请求：

```json
{
  "file_id": 1,
  "image_url": "https://example.com/uploads/1.jpg"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "recognition_id": 1,
    "provider": "mock",
    "candidates": [
      {"food_id": 1, "source": "system", "name": "米饭", "confidence": 0.92},
      {"food_id": 2, "source": "system", "name": "鸡蛋", "confidence": 0.81},
      {"food_id": 3, "source": "system", "name": "鸡胸肉", "confidence": 0.76}
    ]
  }
}
```

---

## 8. 动作接口

### 8.1 搜索动作

`GET /exercises/search?keyword=卧推&body_part=胸&page=1&page_size=20`

### 8.2 创建自定义动作

`POST /exercises/custom`

请求：

```json
{
  "name": "弹力带夹胸",
  "body_part": "胸",
  "description": "自定义动作"
}
```

---

## 9. 训练模板接口

### 9.1 获取训练模板

`GET /training/templates`

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "三分化增肌模板",
        "split_type": "three_split",
        "goal": "muscle_gain",
        "days": []
      }
    ]
  }
}
```

---

## 10. 训练计划接口

### 10.1 获取训练计划列表

`GET /training/plans`

### 10.2 创建训练计划

`POST /training/plans`

请求：

```json
{
  "name": "我的四分化计划",
  "schedule_type": "weekly",
  "source_template_id": null,
  "days": [
    {
      "day_index": 1,
      "day_name": "胸部训练",
      "is_rest_day": false,
      "weekday": 1,
      "exercises": [
        {
          "exercise_source": "system",
          "exercise_id": 1,
          "custom_exercise_id": null,
          "target_sets": 4,
          "target_reps": 10,
          "target_weight_kg": 60,
          "rest_seconds": 180,
          "sort_order": 1
        }
      ]
    }
  ]
}
```

### 10.3 获取训练计划详情

`GET /training/plans/{id}`

### 10.4 更新训练计划

`PUT /training/plans/{id}`

### 10.5 删除训练计划

`DELETE /training/plans/{id}`

### 10.6 获取今日训练

`GET /training/today?date=2026-07-05`

---

## 11. 训练执行接口

### 11.1 创建训练 session

`POST /training/sessions`

请求：

```json
{
  "plan_id": 1,
  "plan_day_id": 2,
  "session_date": "2026-07-05"
}
```

### 11.2 获取训练 session 详情

`GET /training/sessions/{id}`

### 11.3 更新训练 session 进度

`PUT /training/sessions/{id}`

请求：

```json
{
  "status": "in_progress",
  "exercises": [
    {
      "session_exercise_id": 1,
      "sets": [
        {
          "set_id": 1,
          "actual_reps": 10,
          "actual_weight_kg": 60,
          "completed": true
        }
      ]
    }
  ]
}
```

### 11.4 完成训练

`POST /training/sessions/{id}/finish`

### 11.5 放弃训练

`POST /training/sessions/{id}/cancel`

### 11.6 查询训练历史

`GET /training/sessions?start_date=2026-07-01&end_date=2026-07-31`

---

## 12. 体重接口

### 12.1 查询体重记录

`GET /weight/records?range=30`

### 12.2 添加体重记录

`POST /weight/records`

请求：

```json
{
  "record_date": "2026-07-05",
  "record_time": "08:00",
  "weight_kg": 70.5,
  "note": "早晨空腹"
}
```

### 12.3 更新体重记录

`PUT /weight/records/{id}`

### 12.4 删除体重记录

`DELETE /weight/records/{id}`

---

## 13. 数据统计接口

### 13.1 饮食统计

`GET /stats/diet?range=7`

响应字段：

- date
- calories_kcal
- carbs_g
- protein_g
- fat_g
- calories_goal
- completion_rate

### 13.2 训练统计

`GET /stats/training?range=30`

响应字段：

- date
- session_count
- duration_seconds
- total_volume
- exercise_weight_trends

### 13.3 体重统计

`GET /stats/weight?range=90`

响应字段：

- date
- weight_kg
- target_weight_kg
- diff_kg
- change_from_start

---

## 14. 接口权限说明

| 接口类型 | 是否需要登录 |
|---|---|
| `/auth/wechat-login` | 否 |
| `/foods/search` | 是 |
| `/diet/*` | 是 |
| `/training/*` | 是 |
| `/weight/*` | 是 |
| `/stats/*` | 是 |
| `/uploads/*` | 是 |
| `/ai/*` | 是 |
| `/users/*` | 是 |

---

## 15. 前端联调注意事项

1. 所有请求都需要经过统一 request 封装。
2. token 失效时自动重新登录。
3. 日期统一使用 `YYYY-MM-DD`。
4. 时间统一使用 `HH:mm` 或完整 ISO 时间。
5. 重量和营养字段前端展示保留 1～2 位小数。
6. 删除操作需要二次确认。
7. 训练执行页离开时需要提示保存进度。
