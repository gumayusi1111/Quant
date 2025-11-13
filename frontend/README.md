# 前端方案（仅供内部自用）

> 目标：提供一个轻量的 Web 控制台，用于本地查看指标、盯盘池和执行结果，不对外发布，仅在开发机/内网运行。

## 技术栈建议
- **框架**：React + Vite（或 Next.js 单页），开发体验好、可快速热更新。
- **设计语言**：Ant Design / MUI 任意一套即可，主要关注数据表格与图表组件。
- **状态管理**：React Query（拉本地 API 或读取 CSV 的服务器端转换接口）。
- **图表**：ECharts 或 Recharts，方便展示净值曲线、胜率等。

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

## 页面结构（初版）
1. **仪表盘**：显示最新市场环境、回测 KPI、当前持仓/盯盘数量。
2. **Watchlist**：表格+筛选，按 tier/env/signal_score 排序；支持勾选“加入观察池”。
3. **Watch Pool / 执行**：按 `status`（active/stale/trading）分组，展示 last_seen、env_score，并结合 pending orders 提示下一步动作。
4. **信号详情**：查看某只 ETF 的历史信号、回测成绩（以折线或柱状展示）。
5. **系统状态**：展示最近一次全量刷新、日更、活跃池更新、执行管线运行时间，方便排查。

## 开发步骤
1. **搭建脚手架**：`cd frontend && npm create vite@latest quant-frontend -- --template react-ts`（或 Next.js）。
2. **建立 API 代理**：可先写 `frontend/mock/` 读取 CSV 转 JSON，未来再接真实后端。
3. **实现页面骨架**：路由/布局/侧边菜单，先把仪表盘、Watchlist、执行列表做出基础表格。
4. **引入图表**：接入 ECharts/Recharts，展示市场环境及回测曲线。
5. **交互优化**：加入筛选/排序、状态标签、导出等功能；必要时可把 watch_pool 的“正在交易”状态回写（通过 CLI 或 API）。

> 注意：此前端仅供个人/内部使用，不对外暴露。运行时建议通过本地 Node 服务器或静态托管（如 `npm run dev`），并限制网络访问范围。 
