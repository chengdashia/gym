# 健身与饮食记录小程序

一个用于记录和分析日常健身、饮食与体重数据的微信小程序项目。项目采用前后端分离架构：前端负责小程序/H5 页面，后端提供用户、饮食、训练、体重、统计和上传等 API。

## 项目特点

- 饮食记录：食物搜索、自定义食物、餐次管理、历史餐次复制
- 拍照识别：上传食物图片并返回模拟识别结果，确认后生成饮食记录
- 训练管理：训练模板、训练计划、训练执行、组间休息倒计时
- 体重管理：体重记录、目标体重、趋势图和历史编辑
- 数据统计：首页营养汇总、饮食/训练/体重 7/30/90 天统计、周总结
- 用户管理：微信登录 mock、营养目标、数据导出、清空数据和注销账号

> 当前微信登录和食物拍照识别仍是 mock 实现，适合本地开发和功能联调。

## 技术栈

### 前端 `frontend/`

- uni-app 3.x
- Vue 3 + TypeScript
- Pinia
- Vite
- ECharts / echarts-for-weixin
- SCSS
- Vitest + vue-tsc

### 后端 `backend/`

- Python 3.11
- FastAPI
- SQLAlchemy 2.0
- Alembic
- Pydantic v2 / pydantic-settings
- PyMySQL
- PyJWT
- MySQL

## 项目结构

```text
gym/
├── README.md                         # 项目总览、启动和开发说明
├── frontend/                         # uni-app 前端
│   ├── src/
│   │   ├── api/                      # 后端接口封装
│   │   ├── components/               # 公共 UI 组件
│   │   ├── pages/                    # 页面：登录、首页、饮食、训练、统计、我的
│   │   ├── store/                    # Pinia 状态：auth、user、diet、training、app
│   │   ├── styles/                   # 全局 SCSS、主题变量和组件样式
│   │   ├── utils/                    # 请求、鉴权、日期、营养、统计、训练等工具
│   │   ├── App.vue                   # 应用入口组件
│   │   ├── main.ts                   # Vue/Pinia 应用入口
│   │   ├── pages.json                # 页面路由和 TabBar 配置
│   │   └── manifest.json             # uni-app 应用配置
│   ├── scripts/                      # 构建后处理脚本
│   ├── package.json                  # 前端依赖和 npm scripts
│   ├── vite.config.ts                # Vite/uni-app 配置
│   └── vitest.config.mts             # 前端测试配置
├── backend/                          # FastAPI 后端
│   ├── app/
│   │   ├── main.py                   # FastAPI 应用入口、CORS、健康检查
│   │   ├── api/v1/                    # API 路由：auth、users、diet、training 等
│   │   ├── core/                      # 配置、数据库、JWT、异常和统一响应
│   │   ├── models/                    # SQLAlchemy ORM 模型
│   │   ├── schemas/                   # Pydantic 请求/响应模型
│   │   ├── services/                  # 推荐、营养、排期、统计等业务逻辑
│   │   ├── seed/                      # 食物、动作和训练模板种子数据
│   │   └── utils/                     # 后端通用工具
│   ├── alembic/                       # 数据库迁移脚本
│   │   └── versions/                  # 各版本迁移文件
│   ├── tests/                         # pytest 后端测试
│   ├── uploads/                       # 本地上传文件目录
│   ├── alembic.ini                    # Alembic 配置
│   ├── requirements.txt               # Python 依赖
│   └── README.md                      # 后端详细说明
└── docs/                              # 产品、开发、数据库和 API 文档
    ├── 00_文档总览.md
    ├── 01_产品需求文档_PRD.md
    ├── 02_开发文档.md
    ├── 03_Codex可执行任务清单.md
    ├── 04_数据库表结构设计.md
    └── 05_API接口清单.md
```

## 环境要求

- Node.js 18+ 和 npm
- Python 3.11+
- MySQL 8.x（或兼容版本）
- 微信开发者工具（预览微信小程序时需要）

如果本地使用 Conda，可创建名为 `gym` 的 Python 环境；下面命令沿用项目已有的 `conda run -n gym` 写法。

## 配置后端

在 `backend/` 目录创建 `.env` 文件。项目当前没有提交 `.env.example`，可按下面内容填写：

```env
DB_URL=mysql+pymysql://root:密码@127.0.0.1:3306/fitness_diet?charset=utf8mb4
JWT_SECRET=请替换为至少32位的随机字符串
DEBUG=true
MOCK_WECHAT=true
```

开发环境不配置时，默认数据库地址为：

```text
mysql+pymysql://root@127.0.0.1:3306/fitness_diet?charset=utf8mb4
```

请先在 MySQL 中创建 `fitness_diet` 数据库，或修改 `DB_URL` 指向已有数据库。

## 启动项目

### 1. 安装后端依赖并初始化数据库

```bash
cd backend
conda run -n gym pip install -r requirements.txt
conda run -n gym alembic -c alembic.ini upgrade head
conda run -n gym python -m app.seed.seed_data
```

如果不使用 Conda，可将 `conda run -n gym` 替换为当前 Python 环境对应的 `python`、`pip` 命令。

### 2. 启动后端服务

```bash
cd backend
conda run -n gym uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --app-dir .
```

后端地址：`http://127.0.0.1:8000`

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

接口文档：

- Swagger UI：`http://127.0.0.1:8000/docs`
- ReDoc：`http://127.0.0.1:8000/redoc`

### 3. 安装并启动前端

```bash
cd frontend
npm install
npm run dev:mp-weixin
```

微信小程序开发产物位于：

```text
frontend/dist/dev/mp-weixin
```

使用微信开发者工具打开该目录即可预览。默认后端 API 地址为：

```text
http://127.0.0.1:8000/api/v1
```

如需修改，请编辑 `frontend/src/utils/request.ts`。

浏览器预览 H5：

```bash
cd frontend
npm run dev:h5
```

## 常用命令

```bash
# 前端
cd frontend
npm run dev:mp-weixin       # 微信小程序开发模式
npm run build:mp-weixin     # 微信小程序生产构建
npm run dev:h5              # H5 开发模式
npm run build:h5            # H5 生产构建
npm run typecheck           # TypeScript 类型检查
npm run test                # 前端单元测试

# 后端
cd backend
pytest -q                  # 后端测试
alembic -c alembic.ini upgrade head  # 执行数据库迁移
python -m app.seed.seed_data          # 初始化/补充种子数据
```

## API 模块

后端 API 统一前缀为 `/api/v1`，主要模块如下：

| 模块 | 说明 |
| --- | --- |
| `auth` | 登录和 token |
| `users` | 用户资料、营养目标、数据导出、删除和注销 |
| `home` | 首页聚合数据 |
| `foods` | 食物搜索和自定义食物 |
| `diet` | 饮食记录、最近食物和餐次复制 |
| `uploads` | 图片上传和访问 |
| `ai` | 食物图片识别 mock 接口 |
| `exercises` | 训练动作 |
| `training` | 训练模板、计划和训练记录 |
| `weight` | 体重记录 |
| `stats` | 饮食、训练、体重统计和周总结 |

完整接口列表见 [`docs/05_API接口清单.md`](docs/05_API接口清单.md) 和 [`backend/README.md`](backend/README.md)。

## 测试

```bash
cd frontend && npm run typecheck && npm run test
cd ../backend && pytest -q
```

前端测试主要覆盖请求封装、鉴权、日期、营养计算、饮食上下文、训练计划、统计和体重记录等工具；后端测试覆盖认证安全、业务规则、数据导出、营养计算、统计和上传等模块。

## 开发文档

建议阅读顺序：

1. [`docs/00_文档总览.md`](docs/00_文档总览.md)
2. [`docs/01_产品需求文档_PRD.md`](docs/01_产品需求文档_PRD.md)
3. [`docs/02_开发文档.md`](docs/02_开发文档.md)
4. [`docs/04_数据库表结构设计.md`](docs/04_数据库表结构设计.md)
5. [`docs/05_API接口清单.md`](docs/05_API接口清单.md)

## 当前限制

- 微信登录使用 mock 模式，生产环境需要接入真实 `jscode2session`。
- 食物图片识别使用 mock provider，生产环境需要替换为真实 AI 服务。
- 上传文件默认保存在 `backend/uploads/`，生产环境建议使用对象存储。
- 生产环境必须关闭 debug，并配置安全的数据库连接和 JWT 密钥。
