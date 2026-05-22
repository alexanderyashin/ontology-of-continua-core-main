import type { Atlas } from "./types";

export async function loadAtlas(): Promise<Atlas> {
  const candidates = [
    "/data/oc_universe_atlas_v010.json",
    "/data/oc_universe_atlas.json"
  ];
  let lastStatus = 0;
  for (const path of candidates) {
    const response = await fetch(path);
    if (response.ok) {
      const atlas = (await response.json()) as Atlas;
      try {
        const reviewPaths: readonly string[] = [];
        for (const reviewPath of reviewPaths) {
          const review = await fetch(reviewPath);
          if (review.ok) {
            return { ...atlas, cerberus_review: await review.json() } as Atlas;
          }
        }
      } catch {
        return atlas;
      }
      return atlas;
    }
    lastStatus = response.status;
  }
  throw new Error(`Failed to load OC universe atlas. Tried ${candidates.length} candidates; last status: ${lastStatus}`);
}

function canonical(input: unknown): string {
  if (input === null || typeof input !== "object") return JSON.stringify(input);
  if (Array.isArray(input)) return `[${input.map((item) => canonical(item)).join(",")}]`;
  const record = input as Record<string, unknown>;
  return `{${Object.keys(record).sort().map((key) => `${JSON.stringify(key)}:${canonical(record[key])}`).join(",")}}`;
}

export function stableHash(input: unknown): string {
  const text = canonical(input);
  let hash = 2166136261;
  for (let index = 0; index < text.length; index += 1) {
    hash ^= text.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}
