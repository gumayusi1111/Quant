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
