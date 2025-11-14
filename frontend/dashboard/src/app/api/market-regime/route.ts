import { NextResponse } from "next/server";
import fs from "fs/promises";
import { readCsvSafe } from "@/lib/read-csv";
import { resolveDataPath } from "@/lib/data-root";

const REGIME_FILE = "backtests/market_regime.csv";
const SEGMENT_FILE = "backtests/market_regime_segments.csv";
const ORDERED_REGIMES = ["bull", "sideways", "bear"] as const;

type RegimeKey = (typeof ORDERED_REGIMES)[number];

interface RegimeRow {
  date: string;
  regime: RegimeKey;
}

interface SegmentRow {
  regime: RegimeKey;
  start: string;
  end: string;
  days?: string;
}

const REGIME_ALIAS: Record<RegimeKey, string> = {
  bull: "牛市 / 上升趋势",
  sideways: "震荡 / 平衡区间",
  bear: "熊市 / 下行趋势",
};

const COLOR_HINT: Record<RegimeKey, string> = {
  bull: "#15803d",
  sideways: "#2563eb",
  bear: "#b91c1c",
};

function normalizeDate(value: string | undefined): string {
  if (!value) return "";
  const digits = String(value).replace(/\D/g, "");
  if (digits.length !== 8) return value;
  const year = digits.slice(0, 4);
  const month = digits.slice(4, 6);
  const day = digits.slice(6, 8);
  return `${year}-${month}-${day}`;
}

function sortByDate(a: RegimeRow, b: RegimeRow) {
  return a.date.localeCompare(b.date);
}

function withDefaults(rows: RegimeRow[]): RegimeRow[] {
  return rows
    .map((row) => ({
      date: row.date ?? "",
      regime: (row.regime ?? "sideways") as RegimeKey,
    }))
    .filter((row) => row.date);
}

function calcDistribution(rows: RegimeRow[], windowSize: number) {
  const start = Math.max(rows.length - windowSize, 0);
  const slice = rows.slice(start);
  const base: Record<RegimeKey, number> = {
    bull: 0,
    sideways: 0,
    bear: 0,
  };
  slice.forEach((row) => {
    base[row.regime] += 1;
  });
  return { windowSize: slice.length, counts: base };
}

function calcStreak(rows: RegimeRow[]): number {
  if (!rows.length) return 0;
  const current = rows[rows.length - 1];
  let count = 0;
  for (let i = rows.length - 1; i >= 0; i -= 1) {
    if (rows[i].regime !== current.regime) break;
    count += 1;
  }
  return count;
}

function parseSegments(raw: Record<string, string>[]): SegmentRow[] {
  return raw
    .map((row) => ({
      regime: (row.regime ?? "sideways") as RegimeKey,
      start: row.start,
      end: row.end,
      days: row.days,
    }))
    .filter((row) => row.start && row.end);
}

function toNumber(value: string | undefined): number | null {
  const num = Number(value);
  return Number.isFinite(num) ? num : null;
}

export async function GET() {
  const [regimeRows, segmentRows] = await Promise.all([
    readCsvSafe(REGIME_FILE),
    readCsvSafe(SEGMENT_FILE),
  ]);

  if (!regimeRows.length) {
    return NextResponse.json(
      { data: null, message: "market_regime.csv 尚无记录" },
      { status: 200 },
    );
  }

  const rows = withDefaults(regimeRows as RegimeRow[]).sort(sortByDate);
  const latest = rows[rows.length - 1];
  const distribution30d = calcDistribution(rows, 30);
  const historyWindow = rows.slice(-60).map((row) => ({
    date: normalizeDate(row.date),
    regime: row.regime,
    color: COLOR_HINT[row.regime],
  }));

  const segments = parseSegments(segmentRows).sort((a, b) =>
    a.start.localeCompare(b.start),
  );
  const currentSegment = segments.length ? segments[segments.length - 1] : null;
  const previousSegment =
    segments.length > 1 ? segments[segments.length - 2] : null;
  const streakDays = currentSegment?.regime === latest.regime
    ? toNumber(currentSegment.days) ?? calcStreak(rows)
    : calcStreak(rows);

  const updatedStat = await fs.stat(resolveDataPath(REGIME_FILE)).catch(() => null);

  return NextResponse.json({
    data: {
      current: {
        regime: latest.regime,
        regimeLabel: REGIME_ALIAS[latest.regime],
        date: normalizeDate(latest.date),
        since: normalizeDate(currentSegment?.start ?? latest.date),
        streakDays,
        summary: REGIME_ALIAS[latest.regime],
      },
      previous: previousSegment
        ? {
            regime: previousSegment.regime,
            regimeLabel: REGIME_ALIAS[previousSegment.regime],
            end: normalizeDate(previousSegment.end),
            days: toNumber(previousSegment.days),
          }
        : null,
      distribution30d,
      history: {
        window: historyWindow.length,
        points: historyWindow,
      },
      meta: {
        updatedAt: updatedStat?.mtime?.toISOString() ?? null,
        totalRows: rows.length,
      },
    },
  });
}
