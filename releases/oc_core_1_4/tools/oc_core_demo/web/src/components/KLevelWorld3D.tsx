import { useEffect, useMemo, useState } from "react";
import type { KLevelWorld } from "../types";
import { Canvas3D } from "./Canvas3D";

export function KLevelWorld3D({ worlds, levelId }: { worlds: KLevelWorld[]; levelId: string }) {
  const world = worlds.find((item) => item.level_id === levelId) ?? worlds[0];
  const [selected, setSelected] = useState(world?.nodes[0]?.id ?? "");
  useEffect(() => {
    if (world?.nodes[0]?.id) setSelected(world.nodes[0].id);
  }, [world?.world_id]);
  const selectedNode = world?.nodes.find((node) => node.id === selected) ?? world?.nodes[0];
  const links = useMemo(() => world?.links.map((link) => ({ ...link, weight: link.weight })) ?? [], [world]);
  if (!world) return <div className="note danger">No K-level 3D world data generated.</div>;
  return (
    <div className="k-world-panel">
      <div className="section-header compact-header">
        <div>
          <p className="eyebrow">rotatable continuum world</p>
          <h3>{world.title}</h3>
          <p>{world.meaning}</p>
        </div>
        <div className="hash-badge">world {world.world_hash.slice(0, 12)}</div>
      </div>
      <Canvas3D
        nodes={world.nodes}
        links={links}
        selected={selected}
        onSelect={setSelected}
        highlight={world.kill_options}
        testId="k-world-3d-canvas"
        autoRotate
      />
      <div className="note-grid compact-notes">
        <div className="note"><strong>Selected node</strong><br />{selectedNode?.label}<small>{selectedNode?.role}</small></div>
        <div className="note"><strong>Replay / closure</strong><br />{world.replay_status} / {world.closure_status}<small>{world.artifact_sha256?.slice(0, 18) || "no artifact hash"}</small></div>
        <div className="note danger"><strong>Nonclaim</strong><br />{world.nonclaim_boundary}</div>
      </div>
    </div>
  );
}
