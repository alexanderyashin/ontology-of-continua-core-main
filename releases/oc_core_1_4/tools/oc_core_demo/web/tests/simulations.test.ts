import { describe, expect, it } from "vitest";
import { stableHash } from "../src/data";
import { evidenceSufficiency, transitionPressure } from "../src/simulations";

describe("simulation runtime", () => {
  it("produces deterministic transition series", () => {
    const first = transitionPressure({ initial_coherence: 0.52, transition_pressure: 0.64, corrective_capacity: 0.38, coupling_drag: 0.44, steps: 30 });
    const second = transitionPressure({ coupling_drag: 0.44, corrective_capacity: 0.38, transition_pressure: 0.64, initial_coherence: 0.52, steps: 30 });
    expect(first.series).toHaveLength(31);
    expect(first.score).toBe(second.score);
    expect(stableHash(first)).toBe(stableHash(second));
  });

  it("keeps evidence sufficiency in bounded bands", () => {
    const result = evidenceSufficiency({ source_binding: 0.82, dependency_closure: 0.76, verification_strength: 0.7, nonclaim_clarity: 0.68 });
    expect(result.band).toBe("strong");
    expect(result.score).toBeGreaterThan(0.7);
  });
});
