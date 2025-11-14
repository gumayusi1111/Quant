export type PoolRow = Record<string, string>;

const SUSPEND_VALUES = new Set(["S", "1", "SUSPEND", "Y"]);

export function isSuspended(row: PoolRow): boolean {
  const flag = (row.is_suspend || row.trade_status || row.status || "").toUpperCase();
  return flag !== "" && SUSPEND_VALUES.has(flag);
}

export function isDelisted(row: PoolRow): boolean {
  const delist = row.delist_date || row.delist || "";
  return Boolean(delist && delist !== "00000000");
}

export function resolveStatus(row: PoolRow): string {
  if (isDelisted(row)) return "退市";
  if (isSuspended(row)) return "停牌";
  const raw = row.list_status || row.status || "";
  if (raw) return raw;
  return "在市";
}

const EXCHANGE_MAP: Record<string, string> = {
  SZ: "深交所",
  SZSE: "深交所",
  SZA: "深交所",
  E: "深交所",
  SH: "上交所",
  SSE: "上交所",
  SHA: "上交所",
  S: "上交所",
};

export function resolveExchange(row: PoolRow): string {
  const raw = row.exchange || row.market || row.list_exchange || "";
  if (!raw) return "";
  const upper = raw.toUpperCase();
  return EXCHANGE_MAP[upper] || raw;
}

export function resolveDelistDate(row: PoolRow): string {
  if (!isDelisted(row)) return "";
  return row.delist_date || row.delist || "";
}
