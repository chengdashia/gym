# 健身与饮食小程序 - 前端（uni-app）

> 基于 `docs/健身饮食记录小程序_完整汇总文档.md` 的 PRD + 开发文档 + API + 数据库设计实现，对接同级 `backend/` 的 FastAPI + MySQL 服务。

## 技术栈

- **uni-app 3.x + Vue 3 + TypeScript + Pinia**
- **ECharts** 数据可视化（小程序端使用 `echarts-for-weixin`，H5 端使用原生 echarts）
- **SCSS** 主题样式（清新健康风：薄荷绿 + 米白 + 柔和渐变）
- **Vite** 构建

## 目录结构

```text
frontend/
├── src/
│   ├── api/                # 后端接口封装（auth/user/home/food/diet/training/...）
│   ├── components/         # 公共组件（Card/ProgressRing/MacroBar/RestTimer/EChartsView/...）
│   ├── pages/              # 业务页面（login/home/diet/training/stats/mine）
│   ├── static/tabbar/      # TabBar PNG 图标
│   ├── store/              # Pinia stores（auth/user/diet/training/app）
│   ├── styles/             # 全局 SCSS 变量与 reset
│   ├── utils/              # request/cache/date/nutrition/timer/echarts/constants
│   ├── App.vue
│   ├── main.ts
│   ├── manifest.json
│   └── pages.json
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## 后端地址

默认对接本地开发后端：

```
http://127.0.0.1:8000/api/v1
```

可在 `src/utils/request.ts` 中修改 `API_BASE`。

## 安装与运行

```bash
# 1. 安装依赖
cd frontend
npm install

# 2. 启动微信小程序端（开发模式）
npm run dev:mp-weixin
# 编译产物在 dist/dev/mp-weixin，用微信开发者工具打开该目录即可预览

# 3. 启动 H5 端（浏览器预览）
npm run dev:h5

# 4. 生产构建
npm run build:mp-weixin
npm run build:h5
```

## 关键能力

### 登录与引导
- 首次启动自动 `uni.login` 调 `POST /auth/wechat-login` 拿 token（开发阶段后端为 mock，code 即 openid）。
- token 持久化到 storage，后续请求自动注入 `Authorization: Bearer <token>`。
- 401 自动清理 token 并跳转 onboarding。
- onboarding 三步：协议确认 → 基础资料 → 系统推荐营养目标。

### 五大 Tab
1. **首页** (`pages/home/index`)：环形卡路里进度 + 三大营养条 + 今日训练卡 + 体重进度卡 + 4 个快捷入口。
2. **饮食** (`pages/diet/index`)：横向日期切换 + 餐次折叠卡片 + FAB 添加（搜索/自定义/拍照）。
3. **训练** (`pages/training/index`)：今日训练 hero 卡（休息/计划外/进行中/未开始）+ 计划列表 + 快捷入口。
4. **数据** (`pages/stats/index`)：7/30/90 天切换，三张 ECharts 折线（饮食热量+三大营养、训练容量+次数、体重趋势+目标参考线）。
5. **我的** (`pages/mine/index`)：头像/会员/健身目标 + 4 个 mini 入口 + 资料/目标/提醒/账号菜单。

### 训练执行
- 训练执行页 (`pages/training/execute`)：每组填写实际次数/重量，勾选完成自动启动组间休息倒计时。
- 倒计时支持：暂停/继续/跳过/+15s/-15s/关闭，结束时震动提醒。
- 退出训练弹窗三选项：保存进度（paused）/放弃（cancelled）/标记完成（completed）。
- 训练中断后首页会显示「继续训练」入口。

### 拍照识别
- `pages/diet/photo-recognize`：调用相机或相册 → 上传到 `/api/v1/uploads/image` → 调用 `/api/v1/ai/food-recognition` 返回候选食物 → 用户确认 → 保存为饮食记录。
- 候选选择后填写克数 / 餐次 / 是否保存图片。

### 数据可视化
- `components/EChartsView.vue` 同时支持 H5（echarts.init）与小程序（echarts-for-weixin）。
- 饮食图：左轴热量（带目标参考线）+ 右轴三大营养。
- 训练图：柱状容量 + 折线次数。
- 体重图：折线 + 目标参考线，自动连接空值。

## 设计系统

- **主色**：薄荷绿 `#5BC89A`，深薄荷 `#3FA67C`，浅薄荷 `#C5ECDB`，极浅薄荷 `#EAF8F1`
- **背景**：`#F7FAF8` 米白
- **辅色**：暖橙 `#FFD79A`（热量）
- **圆角**：8 / 12 / 16 / 20 / 24
- **阴影**：`0 6rpx 24rpx rgba(95, 175, 145, 0.08)`
- **渐变**：主渐变 `linear-gradient(135deg, #5BC89A 0%, #7BD8B0 100%)`，hero `linear-gradient(160deg, #5BC89A 0%, #A6E3C5 100%)`

所有 SCSS 变量在 `src/styles/variables.scss` 集中维护，组件 scoped 样式可直接使用 `$primary`、`$text-1` 等变量。

## API 路径

所有请求通过 `src/utils/request.ts` 封装，前缀 `/api/v1`，自动处理 `code/message/data` 与 401：

| 模块 | 路径 |
|---|---|
| auth | `/auth/wechat-login` |
| users | `/users/me`, `/agreement-confirm`, `/nutrition-goal`, `/reminders`, `/delete-data`, `/cancel-account` |
| home | `/home/summary?date=YYYY-MM-DD` |
| foods | `/foods/search`, `/foods/{id}`, `/foods/custom` |
| diet | `/diet/records` (CRUD) |
| uploads | `/uploads/image` |
| ai | `/ai/food-recognition` |
| exercises | `/exercises/search`, `/exercises/custom` |
| training | `/training/templates`, `/plans`, `/today`, `/sessions` |
| weight | `/weight/records` (CRUD) |
| stats | `/stats/{diet,training,weight}?range=7|30|90` |

## 验收要点

1. `npm run dev:mp-weixin` 在微信开发者工具打开 `dist/dev/mp-weixin` 预览。
2. 打开小程序即触发 mock 登录，token 写入 storage。
3. 5 个 Tab 切换无白屏；首页 / 饮食 / 训练 / 数据 / 我的 全部能渲染真实后端数据。
4. 添加饮食（搜索/自定义/拍照）、训练计划创建与执行（含倒计时）、体重记录、7/30/90 天图表全部跑通。
5. 注销账号 / 删除个人数据 二次确认后生效。
6. 401 token 失效自动跳回 onboarding 重新登录。

## 后续可扩展

- 真实微信 jscode2session 替换 mock 登录
- 接入 iconfont CDN（替换 TabBar PNG）
- 真实 AI 识别 provider
- 数据导出（CSV / Excel）
- 高级统计与会员服务