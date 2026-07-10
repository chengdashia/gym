# 健身与饮食记录小程序 - 后端（FastAPI + MySQL）

> 对接 `docs/健身饮食记录小程序_完整汇总文档.md` 中所述的 API、数据库与业务规则。

## 技术栈

- Python 3.11 + FastAPI 0.139
- SQLAlchemy 2.0 + PyMySQL + Alembic
- Pydantic v2 / pydantic-settings
- PyJWT (HS256, 30 天有效)
- 本地存储上传的图片；头像经 `/static` 公开，饮食与识别图片通过鉴权接口读取

## 目录结构

```
backend/
├── app/
│   ├── main.py                # FastAPI 入口 + CORS + 异常处理
│   ├── core/                  # 配置 / DB / 响应 / 异常 / JWT
│   ├── api/v1/                # 业务路由（auth, users, foods, diet, ...）
│   ├── models/                # SQLAlchemy 2.0 ORM 模型
│   ├── schemas/               # Pydantic v2 输入输出 schema
│   ├── services/              # 营养计算 / 排期 / 推荐 / 统计
│   ├── utils/                 # 日期工具
│   └── seed/seed_data.py      # 食物/动作/训练模板种子数据（幂等）
├── alembic/                   # 数据库迁移
├── uploads/                   # 用户上传图片
├── alembic.ini
└── requirements.txt
```

## 环境配置

复制 `.env.example` 为 `.env` 并填写数据库和 JWT 密钥：

```
DB_URL=mysql+pymysql://USER:PASSWORD@HOST:3306/DATABASE?charset=utf8mb4
JWT_SECRET=至少32位随机字符串
```

## 初始化与启动

```bash
# 1. 安装依赖（已在 conda gym 中预装大部分）
conda run -n gym pip install -r backend/requirements.txt

# 2. 建表（幂等）
cd backend
conda run -n gym alembic -c alembic.ini upgrade head

# 3. 灌入基础食物/动作/训练模板（幂等可重复执行）
conda run -n gym python -m app.seed.seed_data

# 4. 启动服务
conda run -n gym uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --app-dir .
```

## 健康检查

```bash
curl http://127.0.0.1:8000/health
# {"code":0,"message":"success","data":{"status":"ok","app":"Fitness Diet API"}}
```

## 主要接口

| 模块 | 关键路径 |
|---|---|
| 健康检查 | `GET /health` |
| 微信登录（mock） | `POST /api/v1/auth/wechat-login` |
| 用户 | `/api/v1/users/me`, `/agreement-confirm`, `/nutrition-goal`, `/export.csv`, `/delete-data`, `/cancel-account` |
| 首页聚合 | `GET /api/v1/home/summary` |
| 食物 | `GET /api/v1/foods/search`, `GET /api/v1/foods/{id}`, `POST /api/v1/foods/custom` |
| 饮食 | `/api/v1/diet/records` (CRUD), `/recent-foods`, `/copy-meal` |
| 上传 | `POST /api/v1/uploads/image`, `GET /api/v1/uploads/{id}/content` |
| AI 识别（mock） | `POST /api/v1/ai/food-recognition` |
| 动作 | `/api/v1/exercises/search`, `/custom` |
| 训练 | `/api/v1/training/templates`, `/plans`, `/today`, `/sessions` |
| 体重 | `/api/v1/weight/records` |
| 统计 | `/api/v1/stats/{diet,training,weight}?range=7|30|90`, `/weekly-summary` |

完整接口清单见 `docs/健身饮食记录小程序_完整汇总文档.md`。

## 响应格式

```json
{ "code": 0, "message": "success", "data": { ... } }
```

错误码表：

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

## 微信登录

当前处于 **mock 模式**：直接将 `code` 字段当作 `openid` 用于 upsert 用户。可在 `app/core/config.py` 中关闭 `mock_wechat` 并实现真实 `jscode2session` 调用。

## 测试

运行自动化测试：

```bash
cd backend
pytest -q
```

## 后续计划

- 真实微信 jscode2session 接入
- 对象存储（OSS / COS）替换本地静态文件
- 实时 AI 识别 provider
