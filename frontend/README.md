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

## 页面结构（初版）
1. **仪表盘**：显示最新市场环境、回测 KPI、当前持仓/盯盘数量。
2. **Watchlist**：表格+筛选，按 tier/env/signal_score 排序；支持勾选“加入观察池”。
3. **Watch Pool / 执行**：按 `status`（active/stale/trading）分组，展示 last_seen、env_score，并结合 pending orders 提示下一步动作。
4. **信号详情**：查看某只 ETF 的历史信号、回测成绩（以折线或柱状展示）。
5. **系统状态**：展示最近一次全量刷新、日更、活跃池更新、执行管线运行时间，方便排查。

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
   - Backtest：读 `watchlist_summary.csv` / `watchlist_summary_by_regime.csv`，用图表展示 KPI。
5. **回写操作**：例如“加入观察池”、“标记正在交易”，通过 PATCH `/api/watch_pool` 更新 CSV（后端写入）。
6. **部署**：仅供内网/本机使用，可通过 `npm run dev` 或 `next build && next start`。若要容器化，可在仓库根目录写 Dockerfile / docker-compose 统一启动。

> 注意：此前端仅供个人/内部使用，不对外暴露。运行时建议通过本地 Node 服务器或静态托管（如 `npm run dev`），并限制网络访问范围。 
