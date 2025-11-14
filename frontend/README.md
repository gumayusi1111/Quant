# 前端方案（仅供内部自用）

> 目标：提供一个轻量的 Web 控制台，用于本地查看指标、盯盘池和执行结果，不对外发布，仅在开发机/内网运行。

## 技术选型

| 层级 | 方案 | 说明 |
| ---- | ---- | ---- |
| 前端框架 | **Next.js + React 18 (TypeScript)** | 支持 SSG/SSR，方便未来扩展路由与鉴权；本地开发 `npm run dev` 即可。Vite 也可行，但 Next 自带更完整的结构。 |
| UI 组件 | **Ant Design 5** | 内置表格、统计卡片、标签等，配色易统一。 |
| 数据层 | **React Query + Axios** | 包装对后端 API 的请求，支持缓存和错误状态显示。 |
| 图表 | **ECharts + echarts-for-react** | 绘制市场环境、回测曲线、胜率柱状等。 |
| 后端 API（本地） | **FastAPI / Flask** | 负责把 CSV/Parquet 转为 JSON 并提供写入 watch_pool 的接口；也可直接读取本地文件，只要统一 schema。 |

## 数据来源 & API 规划
| 模块 | 数据文件 / 接口 | 说明 |
| --- | --- | --- |
| 全量池/活跃池 | `data/master/etf_master.csv`、`data/universe/active_universe.csv` | 用于展示基础信息与筛选条件。 |
| 市场环境 | `data/backtests/market_regime.csv` | 折线图展示 bull/sideways/bear 时间段。 |
| Watchlist 快照 | `data/watchlists/watchlist_today.csv` | 当日候选列表，显示 score、tier、env 等。 |
| Watch Pool | `data/watchlists/watch_pool.csv` | 持续跟踪列表，可手动标记“正在交易/重点观察”。 |
| 回测结果 | `data/backtests/watchlist_summary*.csv` | 胜率、平均收益、回撤等。 |
| 执行计划 | `data/execution/pending_orders.csv` | 展示最新 pending orders，供手动/自动下单参考。 |

如需 API，可在后端新增一个轻量的 FastAPI 服务，把上述 CSV 转成 JSON，前端只需 fetch `/api/watchlist/today` 等接口。

### 推荐 API 设计

| Endpoint | Method | 描述 | 返回字段示例 |
| --- | --- | --- | --- |
| `/api/status` | GET | 系统状态：最近一次数据刷新/活跃池/执行计划时间 | `{ "last_full_pool": "2025-11-01", "last_daily_update": "...", "last_watchlist": "...", "last_execution": "..." }` |
| `/api/regime/segments` | GET | 市场环境时间线 | `[{ "date": "2025-01-01", "regime": "bull" }, ...]` |
| `/api/watchlist/today` | GET | 当日候选列表 | `[{ "ts_code": "510300.SH", "tier": "A", "score": 6, "env": "bull", ... }]` |
| `/api/watch_pool` | GET | 当前盯盘池 | 同上并包含 `first_seen/last_seen/status/days_inactive`。 |
| `/api/watch_pool` | PATCH | 更新状态（如标记“正在交易”），body: `{ "ts_code": "...", "status": "trading" }`. |
| `/api/backtests/watchlist` | GET | 回测汇总 | 包括 `win_rate/avg_return/max_drawdown`，支持 query 参数 `?tier=A&regime=bull`. |
| `/api/execution/pending` | GET | 待执行订单 | 读取 `pending_orders.csv`，返回 `action/price/confidence/trigger_time`. |
| `/api/minute/:code` | GET | （可选）返回指定标的最近 N 条分钟数据，供前端绘制。 |

API 层可直接读取 CSV（用 pandas 转 JSON），也可将 CSV 转 Parquet 后提升性能。

### 池子定义与操作

| 池子 | 数据源 | 典型字段 | 前端操作 |
| ---- | ---- | ---- | ---- |
| **Watchlist Snapshot** | `watchlist_today.csv` | `ts_code, tier, env, score, close, pct_chg` | 加入观察池、设为忽略、打开详情。 |
| **观察池（Watch Pool）** | `watch_pool.csv` | `first_seen, last_seen, status (active/stale/trading), days_inactive, env_score` | 更新状态、添加备注、手动删除、推送到正在交易池。 |
| **正在交易池** | 可扩展 `watch_pool` 增加 `position_weight/buy_price` 字段或独立 JSON | `buy_price, position, stop_loss, target` | 编辑仓位信息、结束交易（移回观察池或归档）。 |
| **执行池（Pending Orders）** | `pending_orders.csv` | `action, price, confidence, trigger_time` | 手动确认/取消、刷新 minute 数据、导出。 |
| **历史交易/回测** | `watchlist_trades.csv`、`watchlist_summary*.csv` | `entry_date, exit_date, return, regime` | 查看绩效、筛选样本。 |

> 观察池应允许用户自定义“标签/备注”，以免每天盯盘时被新的筛选覆盖；前端可提供一个本地存储或写回 CSV 的接口。

## 页面结构（v1.1 规划）
1. **仪表盘 `/overview`**  
   - 核心指标：全量池总数、活跃池总数、观察池 active/stale/trading 数量、pending orders 数量。  
   - 最近运行状态：记录全量刷新、日更、活跃池更新、执行管线的时间戳。  
   - 市场环境快照：当前 regime、最近 N 天 regime 走势。  
2. **候选池 `/watchlist`**  
   - 表格+筛选，全部字段来自 `watchlist_today.csv`；可批量加入观察池、设为忽略。  
   - 后续加入排序、导出、列配置。  
3. **观察池 `/pool`**  
   - 与 `watch_pool.csv` 同步；按 status 分组展示，支持标记 active/stale/trading、添加备注、移除。  
   - 提供“迁移到正在交易池”的快捷操作。  
4. **执行池 `/execution`**  
   - 读取 `pending_orders.csv`，展示待执行订单；可刷新、确认、撤销。  
5. **全量池 `/full-pool`**  
   - 查看 `etf_master.csv`：列表+搜索+统计，包含总数、停牌/退市数量，以及交易所信息。  
   - 元数据：显示最近一次全量刷新时间、近30日新增数量、异常记录数。  
   - 后续扩展增删改（需新增 API）。  
6. **回测 `/backtest`（新）**  
   - 展示 `watchlist_summary*.csv` 的胜率/收益/回撤，支持按 tier/regime 的图表。  
7. **信号详情**  
   - 作为弹窗或独立页面，展示单只 ETF 的历史信号/回测表现（待需求明确后实现）。

## 开发步骤
1. **初始化项目**  
   ```bash
   cd frontend
   npx create-next-app@latest --ts quant-dashboard
   cd quant-dashboard
   npm install antd @tanstack/react-query echarts echarts-for-react axios
   ```
2. **封装 API 客户端**：`/lib/api.ts` 中用 Axios 指向本地 FastAPI（或读取 `public/mock` JSON），统一错误处理。
3. **实现 Layout**：侧边导航（仪表盘 / Watchlist / Watch Pool / 执行 / 回测 / 设置），头部显示当前 regime。
4. **对接各页面**：
   - 仪表盘：调用 `/api/status` + `/api/regime/segments`，用 ECharts 展示环境时间轴。
   - Watchlist：表格 + 筛选 + 快速操作（加入观察池/打开详情）。
   - Watch Pool：表格 + 状态标签；提供 PATCH 接口修改状态。
   - Execution：列表展示 pending orders，支持刷新、导出。
   - Full Pool：读取 `etf_master.csv`，展示基础信息 + 统计数据。
   - Backtest：读取 `watchlist_summary*.csv`，用图表展示 KPI。
5. **回写操作**：例如“加入观察池”、“标记正在交易”，通过 PATCH `/api/watch_pool` 更新 CSV（后端写入）。
6. **部署**：仅供内网/本机使用，可通过 `npm run dev` 或 `next build && next start`。若要容器化，可在仓库根目录写 Dockerfile / docker-compose 统一启动。

> 注意：此前端仅供个人/内部使用，不对外暴露。运行时建议通过本地 Node 服务器或静态托管（如 `npm run dev`），并限制网络访问范围。 

## 任务 API（FastAPI）

为避免频繁手动运行 CLI，可通过 `backend/tasks_api.py` 启动 FastAPI 服务，暴露以下接口：

| Method | Path | 说明 |
| --- | --- | --- |
| `POST /tasks/full_pool` | 运行全量池刷新（受 `refresh_interval_days` 限制） |
| `POST /tasks/backfill_daily` | 拉取全部历史日线并计算指标（慢，首拉/异常时用） |
| `POST /tasks/daily` | 增量日线拉取 + 指标计算（仅补缺失交易日） |
| `POST /tasks/daily_routine` | 日常一键：增量日线 → 活跃池 & 市场环境 → 候选池 |
| `POST /tasks/watchlist` | 生成候选池并同步观察池 |
| `POST /tasks/auto` | 一键执行整条流水线（调用 `run_auto_pipeline`） |
| `GET /tasks/status` | 返回各任务的最近执行时间、状态、耗时等 |

启动方式：

```bash
pip install -r requirements.txt  # fastapi/uvicorn 已加入
uvicorn backend.tasks_api:app --host 0.0.0.0 --port 8000
```

前端通过 `NEXT_PUBLIC_TASK_API_BASE`（默认 `http://127.0.0.1:8000`）访问该服务，仪表盘会显示任务状态并提供「立即执行」按钮。

## TODO / 需求追踪

| 模块 | 状态 | 说明 |
| --- | --- | --- |
| 前端骨架 & 布局 | ✅ | Next.js + TS + AntD + React Query；App Router 中 `(dashboard)/layout.tsx` 统一侧栏/头部。 |
| Watchlist API | ✅ | `/api/watchlist` 已读取真实 CSV。 |
| 仪表盘指标 | ⏳ | 需新增 `/api/metrics`，整合全量/活跃/观察池/执行统计与运行时间。 |
| Watch Pool 页面 | ⏳ | 需要接入 `watch_pool.csv` 显示并提供状态编辑/PATCH。 |
| 执行池页面 | ⏳ | 需要接入 `pending_orders.csv` 并实现操作按钮。 |
| 全量池页面 | ⏳ | `/full-pool` 已有列表/统计/元数据显示；后续补批量操作、增删改 API。 |
| 回测页面 | ⏳ | 新增 `/backtest` 路由，图表化显示 `watchlist_summary*.csv`。 |
| API 层（FastAPI/Flask） | ⏳ | 把 CSV 读写封装成 REST API，前端只通过 Axios 调用。 |
| 样式/主题 | ⏳ | 当前为浅色主题；后续可加入暗色模式、响应式优化等。 |
