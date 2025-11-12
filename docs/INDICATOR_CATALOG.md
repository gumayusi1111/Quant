## 指标目录（默认参数）

- 默认使用 `close_front_adj` 作为价格列，必要时可手动传入原始价。
- 周期单位为交易日，可根据策略调整。

| 指标 | 函数 | 默认参数/输出 | 说明 |
|------|------|----------------|------|
| MA | `ma(price, window)` | 5 / 10 / 20 / 30 / 60 | 简单移动均线 |
| EMA | `ema(price, span)` | 单周期 EMA | 指数移动平均 |
| EXPMA | `expma(price)` | 5 / 10 / 20 / 60 → `ma1~ma4` | 指数平滑线 |
| MACD | `macd(price)` | 12,26,9 → `dif/dea/macd` | 经典趋势指标 |
| BOLL | `boll(price)` | 20,2 → `boll_upper/mid/lower` | 布林带 |
| KDJ | `kdj(high, low, close)` | 9,3,3 → `K/D/J` | 随机指标 |
| RSI | `rsi(price,(6,12,24))` | 输出 `rsi6/12/24` | 动量指标 |
| WR | `wr(high,low,close,(10,6))` | 输出 `wr1/wr2`（20/80 为默认参考线） | 威廉指标 |
| DMI/ADX | `dmi(high,low,close)` | 14,6 → `+DI/-DI/ADX/ADXR` | 趋向指标 |
| BIAS | `bias(price)` | (6,12,24) → `bias1~3` | 乖离率（正负 3/6% 自行参照） |
| ASI | `asi(open,high,low,close)` | 累积 + MA10 → `ASI/ASIT` | 累积摆动指标 |
| VR | `vr(close,volume)` | 26（日） | 成交量比率 |
| ARBR | `arbr(high,low,open,close)` | 26 → `AR/BR` | 人气/意愿 |
| DPO | `dpo(price)` | (20,10,6) → `DPO/MADPO` | 区间震荡 |
| TRIX | `trix(price)` | 12,20 → `TRIX/TRMA` | 三重指数平均 |
| DMA | `dma(price)` | 10,50,10 → `DDD/AMA` | 差离/平滑 |
| BBI | `bbi(price)` | 3/6/12/24 | 多空平衡 |
| MTM | `mtm(price)` | 12,6 → `MTM/MTMMA` | 动量指标 |
| OBV | `obv(close,volume)` | MA30 → `OBV/MAOBV` | 量价累积 |
| SAR | `sar(high,low)` | step=0.02, max=0.2 | 抛物线转向 |
| BOLL (兼容) | `bollinger_bands(price)` | 20 | 旧接口 |

*默认使用 `*_front_adj` 价格列（如 `close_front_adj`）。*

调用示例：

```python
from src.indicator_engine import macd, kdj, rsi, wr

price = df["close_front_adj"]
macd_df = macd(price)
kdj_df = kdj(df["high_front_adj"], df["low_front_adj"], price)
rsi_df = rsi(price, periods=(6, 12, 24))
wr_df = wr(df["high_front_adj"], df["low_front_adj"], price, periods=(10, 6))
```
