## Quant

Bootstrap structure for the ETF Quant System described in `docs/`. The goal right
now is a clean folder layout so we can gradually fill in every module (data
fetcher, indicators, signals, strategies, risk, backtest, reports, scheduler).

### Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy config\tokens.template.json config\tokens.json  # 备份模板，敏感 token 写在真实文件
python main.py --nightly   # 运行夜间流程占位实现
```

> token 已搬移至 `config/tokens.json`（被 `.gitignore` 忽略）。如需分享格式，请编辑模板文件而非真实 token。

### Full Pool Refresh (每 ~60 天)

```bash
python main.py --full-pool
```

- Pipeline 会检查 `data/master/etf_master.csv` 的更新时间，若超过 `refresh_interval_days`（默认 60）则重建 master/active 模板，并提示需要补齐近 90 天日K。
- 会自动调用 chinadata 的 `etf_basic` 与 `fund_daily` 接口，把 ETF 基础信息和近 90 天日线写入 `data/master/` 与 `data/daily/`。
- 建议在首次部署或长期未更新数据时执行一次（请求量较大，确保 token 有权限）。

### Active Pool Refresh (每 ~7 天)

```bash
python main.py --active-pool
```

- 基于 `data/master` + `data/daily` 计算近 60 日的流动性/稳定性指标，筛出 150–300 只活跃 ETF。
- 规则详见 `docs/ACTIVE_POOL_RULES.md`，可通过 `config/settings.json -> active_pool.filters` 调整阈值。
- 输出写入 `data/universe/active_universe.csv`，日志记录筛选数量与耗时。

### Indicator Batch

```bash
python main.py --indicators
```

- 读取 `data/daily/` 缓存，使用 `src/indicator_engine` 计算 MA/EXPMA/MACD/KDJ/RSI/BOLL/WR/DMI/BOLL/DPO/TRIX/DMA/BBI/MTM/OBV/ASI 等指标。
- 默认仅对活跃池 (`data/universe/active_universe.csv`) 中的 ETF 生成指标；如需全量可在脚本中传入 symbol 列表。
- 每个 `ts_code` 生成一个 `data/indicators/{ts_code}.csv` 结果文件，默认使用 `*_front_adj` 价格，保留 6 位小数。
- 具体指标与参数详见 `docs/INDICATOR_CATALOG.md`。

### Watchlist（根据指标筛选）

```bash
python main.py --watchlist
```

- 读取活跃池及其指标，筛选满足「MA 多头 + MACD 金叉 + KDJ 未过热」等条件的 ETF，并结合 RSI/BOLL/WR/OBV 做进一步确认。
- 输出 `data/watchlists/watchlist_today.csv`，包含 `ts_code/date/close/pct_chg/score/tier/...` 等字段，供盘前/盘中盯盘。
- 按流动性 + 波动率 + 价位等指标自动打 `tier`：A（高流动/低波动，优先执行）、B（等待确认）、C（高波动或量能不足）。可在 `src/pipelines/watchlist.py` 中调整阈值。
- 规则可在 `src/pipelines/watchlist.py` 中调整，当前逻辑为第一版试运行。

### Watchlist Backtest（验证信号胜率）

```bash
python main.py --backtest-watchlist
```

- 会遍历每个 ETF 的历史指标，逐日复现 watchlist 筛选条件，并计算 1/3/5 日的前瞻收益。
- 原始信号写入 `data/backtests/watchlist_signals.csv`；结合卖出规则生成的真实交易写入 `data/backtests/watchlist_trades.csv`（含进出场时间、收益、持仓天数、退出原因）。
- 汇总统计写入 `data/backtests/watchlist_summary*.csv`（整体/年份/行情段），展示胜率、平均/中位收益，用于调参或复盘。

### Providers & Tokens

- `tushare.token`（822...）：官方 Tushare 包，只能请求历史分钟行情；相关逻辑放在
  `src/data_fetcher/`，不可用于日线。
- `chinadata.token`（b3...）：chinadata 包，用于获取日 K 以及其他行情。
- 所有 provider 绑定写在 `config/settings.json` → `providers` 区域方便切换。

### Source Control

项目托管在 **GitHub**（不是 Gitee）。所有脚本/文档在描述远程仓库或 CI/CD 时务必指向 GitHub。

### Directory Layout

```
config/                 # settings.json + tokens(.json/.template)
data/
  ├─ master/            # etf_master.csv（每 ~60 天重建；模板已提供）
  ├─ universe/          # active_universe.csv（活跃池）
  ├─ daily/             # 每只 ETF 的日K CSV，含原始价 + 前/后复权价 + 复权因子
  ├─ indicators/        # 技术指标 CSV 输出（每个 ts_code 一份）
  ├─ backtests/         # watchlist 信号、交易、统计与市场环境
  ├─ minute/            # 观察池分钟数据，按 ts_code/日期/频率组织
  ├─ logs/              # signal_log.csv 等流水日志（模板、生成品）
  └─ watchlists/        # watchlist_today.csv 等名单
docs/                   # 架构 / 数据流程 / 规则文档
                        # 指标清单：docs/INDICATOR_CATALOG.md
outputs/                # 报告或可视化结果
src/
  ├─ data_fetcher/      # tushare/chinadata 调用封装
  ├─ indicator_engine/  # 趋势、量能、波动指标
  ├─ signal_generator/  # 规则、打分、信号
  ├─ strategy_etf/      # 策略逻辑
  ├─ risk_control/      # 止盈止损、仓位分配
  ├─ backtester/        # 回测引擎与分析
  ├─ report_builder/    # 报告与可视化
  ├─ scheduler/         # nightly / intraday 调度
  ├─ pipelines/         # 全量库、活跃池、日更、盘中等流程
  └─ utils/             # config / logger / io 等公用工具
```

### Next Steps

1. Replace placeholder implementations with real logic (Tushare/ChinaData client,
   indicator calculations, strategy rules, etc.).
2. Flesh out scheduler tasks to wire the full pipeline: fetch data → compute
   indicators → signals → strategy execution → risk checks → backtest → report.
3. Expand tests/notebooks once core modules stabilize.

### 开发规则

- 必须遵循 `docs/PROJECT_RULES.md`：禁止硬编码、配置集中管理、单文件 ≤250 行、保持高内聚低耦合，并及时维护 Markdown。
- 推送到 GitHub 远程前需要所有者确认；删除文件或进行大改动前也要先沟通。
- 测试脚本统一放在 `tests/` 下；任何新文件都要放在对应子目录，根目录保持干净。
- 新增/调整模块后，记得同步更新 README 或相关 docs，删除过期的说明文件。
- 当需要拉长历史测试窗口（例如 2020 起）时，可先运行：

```bash
python main.py --backfill-daily
python main.py --indicators
python main.py --backtest-watchlist
python main.py --market-regime
python main.py --auto            # 自动检查并串行执行必要的刷新
```

- `--backfill-daily` 会依据 `config/settings.json -> history_backfill.start_date` 为全量 ETF 重建日线缓存。
- 重跑指标后，再执行回测即可获得更长区间的样本。
- `--market-regime` 根据 `market_guard` 的多指标组合（MA60/MA120、MACD、RSI、波动率等）输出每日行情状态（bull / bear / sideways），若缺少基准 ETF 会自动用活跃池等权指数。写入 `data/backtests/market_regime.csv` 与 `market_regime_segments.csv`。
- `--auto` 会按顺序检查“全量池 / 日线缓存 / 活跃池 / 指标 / 盯盘名单”的更新时间，只有在超出阈值时才触发相应流程，最后始终生成当日 watchlist，方便定时任务调用。
