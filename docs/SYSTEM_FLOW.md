# 系统流程与完成度追踪

> 目标：先把整条流水线（数据 → 活跃 → 环境 → 筛选 → 策略 → 执行 → 回测）跑通，再逐步打磨策略质量。以下按流程节点说明当前状态与下一步计划。

## 流程总览

| 序号 | 环节 | 当前状态 | 说明 / 下一步 |
| ---- | ---- | -------- | ------------- |
| 1 | **全量池刷新** | ✅ 完成 | TuShare/ChinaData 定期刷新 `data/master/etf_master.csv`，含 2020-至今日 K；需要在 `--auto` 中检测 60 天是否到期后自动触发。 |
| 2 | **日线 & 指标缓存** | ✅ 完成 | `data/daily/*.csv` 与 `data/indicators/*.csv` 每日增量更新，指标体系已覆盖 20+ 技术指标。 |
| 3 | **活跃池筛选** | ✅ 完成 | `data/universe/active_universe.csv` 约 200 只，依据流动性/上市天数/波动硬过滤；后续可根据经验再调门槛。 |
| 4 | **市场环境检测** | ✅ 完成 | `main.py --market-regime` 输出 bull/sideways/bear 到 `data/backtests/market_regime.csv`；需在 nightly/auto 里确保每日更新。 |
| 5 | **环境感知盯盘筛选** | ✅ 完成 | `universe_filters/{bull,sideways,bear}.py` 已上线，watchlist 依据当前 regime 过滤，并同步写入盯盘池。 |
| 6 | **策略信号层** | ⚠️ 部分完成 | watchlist/backtest 会按环境调用 bull/sideways/bear 策略，但侧向/熊市逻辑仍需迭代、验证与打分优化。 |
| 7 | **盯盘池管理** | ✅ 完成 | `data/watchlists/watch_pool.csv` 记录 first/last_seen、tier、env、状态与过期机制，watchlist pipeline 每日维护。 |
| 8 | **执行（分钟级）** | ⚠️ 初版完成 | 新增 `pipelines.execution` + `execution.rules`：可读取 watch_pool、合并 5min bars 并生成 `pending_orders`。下一步是增强执行策略与真实下单联动。 |
| 9 | **回测 & 绩效监控** | ⚠️ 部分完成 | Watchlist 回测已能统计 A/B/C，但卖点只有 bull 版本，且未拆 regime；待策略分流后同步更新，增加按环境的胜率/回撤统计。 |
|10 | **自动调度** | ⚠️ 部分完成 | `--auto` 已串基本流水线，但尚未检查“全量刷新到期/盯盘池更新/执行记录”。需扩展自动化脚本并写入状态日志。 |

## 下一步行动（按优先级）

1. **策略分环境深化**  
   - 优化 Sideways/Bear 策略逻辑、评分与卖点，结合回测结果调参，确保三种环境都能稳定输出高质量信号。

2. **分钟级执行 → 实盘化**  
   - 将 `pending_orders` 接入真实下单/模拟撮合，补充 VWAP/回踩等执行规则，并提供执行日志与失败重试。

3. **回测升级**  
   - 让回测读取新策略输出，统计 bull/sideways/bear 三类表现，加入最大回撤/夏普/胜率（按 tier）等指标，验证闭环。

4. **自动化与监控**  
   - 扩展 `--auto`：检测全量刷新到期、每日 market_regime 更新、盯盘池维护、执行队列生成；同步写状态日志方便排查。

完成上述关键节点后，系统即可实现“策略一般但链路完整”的运行，再逐步优化阈值、信号与风控即可。***
