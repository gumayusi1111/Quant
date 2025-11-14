import { NextResponse } from "next/server";
import fs from "fs/promises";
import { readCsvSafe } from "@/lib/read-csv";
import { resolveDataPath } from "@/lib/data-root";

const FILE_PATH = "master/etf_master.csv";

function parseDate(value: string | undefined, defaultValue: Date) {
  if (!value) return defaultValue;
  const normalized = value.trim();
  if (!normalized) return defaultValue;
  // expect YYYYMMDD
  if (/^\d{8}$/.test(normalized)) {
    const year = Number(normalized.slice(0, 4));
    const month = Number(normalized.slice(4, 6)) - 1;
    const day = Number(normalized.slice(6, 8));
    return new Date(year, month, day);
  }
  const fallback = new Date(normalized);
  return Number.isNaN(fallback.getTime()) ? defaultValue : fallback;
}

export async function GET() {
  const rows = await readCsvSafe(FILE_PATH);
  const filePath = resolveDataPath(FILE_PATH);
  const stat = await fs.stat(filePath).catch(() => null);
  const now = new Date();
  const threshold = new Date(now);
  threshold.setDate(now.getDate() - 30);

  const newWithin30d = rows.filter((row) => {
    const date = parseDate(row.list_date, new Date(0));
    return date >= threshold;
  }).length;

  const anomalyCount = rows.filter((row) => !row.ts_code || !row.name).length;

  return NextResponse.json({
    data: rows,
    meta: {
      updatedAt: stat ? stat.mtime.toISOString() : null,
      newWithin30d,
      anomalyCount,
    },
  });
}
