import path from "path";

export const DATA_ROOT =
  process.env.QUANT_DATA_ROOT ??
  path.resolve(process.cwd(), "..", "..", "data");

export function resolveDataPath(relativePath: string): string {
  return path.join(DATA_ROOT, relativePath);
}
