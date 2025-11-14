import { NextResponse } from "next/server";
import { readCsv } from "@/lib/read-csv";

export async function GET() {
  const rows = await readCsv("watchlists/watchlist_today.csv");
  return NextResponse.json({ data: rows });
}
