import fs from "fs/promises";
import { parse } from "csv-parse/sync";
import { resolveDataPath } from "./data-root";

export async function readCsv(relativePath: string) {
  const target = resolveDataPath(relativePath);
  const content = await fs.readFile(target, "utf8");
  const records = parse(content, {
    columns: true,
    skipEmptyLines: true,
    trim: true,
  }) as Record<string, string>[];
  return records;
}

export async function readCsvSafe(relativePath: string) {
  try {
    const rows = await readCsv(relativePath);
    return rows;
  } catch (error) {
    return [];
  }
}
