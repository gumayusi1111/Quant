import { NextResponse } from "next/server";
import fs from "fs/promises";
import { readCsvSafe } from "@/lib/read-csv";
import { resolveDataPath } from "@/lib/data-root";

const FILE_PATH = "universe/active_universe.csv";

function toNumber(value: string | undefined): number | null {
  if (value === undefined) return null;
  const num = Number(value);
  return Number.isFinite(num) ? num : null;
}

function average(values: number[]) {
  if (!values.length) return null;
  const total = values.reduce((sum, val) => sum + val, 0);
  return total / values.length;
}

export async function GET() {
  const rows = await readCsvSafe(FILE_PATH);
  const stat = await fs.stat(resolveDataPath(FILE_PATH)).catch(() => null);

  const amounts = rows
    .map((row) => toNumber(row.mean_amount_60))
    .filter((value): value is number => value !== null);

  const tradeRatios = rows
    .map((row) => toNumber(row.trade_days_ratio_60))
    .filter((value): value is number => value !== null);

  const ranges = rows
    .map((row) => toNumber(row.median_range_60))
    .filter((value): value is number => value !== null);

  return NextResponse.json({
    data: rows,
    meta: {
      updatedAt: stat?.mtime?.toISOString() ?? null,
      total: rows.length,
      avgAmount60: average(amounts),
      avgTradeRatio60: average(tradeRatios),
      avgRange60: average(ranges),
    },
  });
}
