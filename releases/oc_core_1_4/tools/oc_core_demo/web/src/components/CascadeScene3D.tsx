import { useEffect, useMemo, useState } from "react";
import type { SystemModel } from "../types";
import { killCascade } from "../simulations";
import { stableHash } from "../data";
import { Canvas3D } from "./Canvas3D";

export function CascadeScene3D({ system, killNode, shock, mode, speed }: { system: SystemModel; killNode: string; shock: number; mode: "selected" | "weakest"; speed: number }) {
  const result = useMemo(() => killCascade(system, killNode, shock, mode), [system, killNode, shock, mode]);
  const [frame, setFrame] = useState(0);
  useEffect(() => {
    setFrame(0);
    const delay = Math.max(80, 900 / Math.max(0.25, speed));
    const timer = window.setInterval(() => {
      setFrame((value) => (value >= result.events.length - 1 ? value : value + 1));
    }, delay);
    return () => window.clearInterval(timer);
  }, [result, speed]);
  const activePath = result.events.slice(0, frame + 1).map((event) => event.node);
  const health = new Map(result.events.slice(0, frame + 1).map((event) => [event.node, event.residual_coherence]));
  const nodes = (system.nodes ?? []).map((node) => ({
    ...node,
    health: health.get(node.id) ?? 1,
    role: activePath.includes(node.id) ? "critical-support" : node.role
  }));
  return (
    <div className="cascade-3d-shell">
      <Canvas3D nodes={nodes} links={system.edges ?? []} selected={activePath.at(-1)} highlight={activePath} testId="kill-cascade-3d-canvas" />
      <div className="cascade-readout">
        <strong>{result.status}</strong>
        <span>trigger {result.trigger}</span>
        <span>connectivity loss {result.connectivity_loss.toFixed(3)}</span>
        <span>hash {stableHash({ system: system.id, trigger: result.trigger, shock, mode, path: result.path }).slice(0, 12)}</span>
      </div>
    </div>
  );
}
