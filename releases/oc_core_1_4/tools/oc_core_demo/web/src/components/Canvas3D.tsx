import { useEffect, useMemo, useRef, useState } from "react";
import type { PointerEvent, WheelEvent } from "react";

export type SceneNode = {
  id: string;
  label: string;
  role?: string;
  cluster?: string;
  x: number;
  y: number;
  z?: number;
  size?: number;
  health?: number;
};

export type SceneLink = {
  source: string;
  target: string;
  relation?: string;
  weight?: number;
  flow_channel?: string;
};

const COLORS: Record<string, string> = {
  structural: "#2563eb",
  "proof-only": "#7c3aed",
  simulatable: "#0f766e",
  calculator: "#ca8a04",
  "proof-browser": "#dc2626",
  "continuum-core": "#2563eb",
  boundary: "#0f766e",
  invariant: "#7c3aed",
  "domain-projection": "#ca8a04",
  "critical-support": "#dc2626",
  dependency: "#64748b",
  "collapse-terminal": "#111827"
};

function rotate(node: SceneNode, yaw: number, pitch: number) {
  const z = node.z ?? 0;
  const cosY = Math.cos(yaw);
  const sinY = Math.sin(yaw);
  const cosP = Math.cos(pitch);
  const sinP = Math.sin(pitch);
  const x1 = node.x * cosY - z * sinY;
  const z1 = node.x * sinY + z * cosY;
  const y1 = node.y * cosP - z1 * sinP;
  const z2 = node.y * sinP + z1 * cosP;
  return { x: x1, y: y1, z: z2 };
}

export function Canvas3D({
  nodes,
  links,
  selected,
  onSelect,
  highlight = [],
  testId,
  autoRotate = false
}: {
  nodes: SceneNode[];
  links: SceneLink[];
  selected?: string;
  onSelect?: (id: string) => void;
  highlight?: string[];
  testId: string;
  autoRotate?: boolean;
}) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [yaw, setYaw] = useState(0.62);
  const [pitch, setPitch] = useState(0.34);
  const [zoom, setZoom] = useState(1);
  const [hovered, setHovered] = useState("");
  const dragRef = useRef<{ x: number; y: number; yaw: number; pitch: number; moved: boolean } | null>(null);
  const projectedRef = useRef<Array<{ id: string; label: string; x: number; y: number; r: number }>>([]);
  const highlightSet = useMemo(() => new Set(highlight), [highlight]);

  useEffect(() => {
    if (!autoRotate) return;
    const timer = window.setInterval(() => setYaw((value) => value + 0.012), 32);
    return () => window.clearInterval(timer);
  }, [autoRotate]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.max(1, Math.round(rect.width * dpr));
    canvas.height = Math.max(1, Math.round(rect.height * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const width = rect.width;
    const height = rect.height;
    ctx.clearRect(0, 0, width, height);
    const gradient = ctx.createLinearGradient(0, 0, width, height);
    gradient.addColorStop(0, "#f8fbff");
    gradient.addColorStop(1, "#eef6ff");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);
    const maxExtent = Math.max(1, ...nodes.map((node) => Math.hypot(node.x, node.y, node.z ?? 0)));
    const scale = Math.min(width, height) * 0.36 * zoom / maxExtent;
    const rotated = new Map(nodes.map((node) => [node.id, rotate(node, yaw, pitch)]));
    const project = (node: SceneNode) => {
      const point = rotated.get(node.id) ?? rotate(node, yaw, pitch);
      const depth = 1 / (1 + Math.max(-0.78, point.z / (maxExtent * 5)));
      return {
        x: width / 2 + point.x * scale * depth,
        y: height / 2 + point.y * scale * depth,
        z: point.z,
        depth
      };
    };
    const projected = nodes.map((node) => ({ node, ...project(node) })).sort((a, b) => a.z - b.z);
    ctx.lineCap = "round";
    for (const link of links) {
      const source = nodes.find((node) => node.id === link.source);
      const target = nodes.find((node) => node.id === link.target);
      if (!source || !target) continue;
      const a = project(source);
      const b = project(target);
      const active = highlightSet.has(link.source) || highlightSet.has(link.target) || selected === link.source || selected === link.target;
      ctx.strokeStyle = active ? "#dc2626" : link.flow_channel === "failure" ? "#fca5a5" : "#c8d7e8";
      ctx.lineWidth = active ? 2.8 : Math.max(0.8, (link.weight ?? 0.6) * 1.8);
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();
    }
    projectedRef.current = [];
    for (const item of projected) {
      const role = item.node.role ?? item.node.cluster ?? "structural";
      const color = COLORS[role] ?? "#2563eb";
      const isHovered = item.node.id === hovered;
      const isSelected = item.node.id === selected;
      const isHot = isSelected || isHovered || highlightSet.has(item.node.id);
      const health = item.node.health ?? 1;
      const radius = Math.max(4, (item.node.size ?? 8) * 0.55 * item.depth + (isHot ? 5 : 2));
      const halo = Math.max(10, radius * 1.75 + 2);
      const clickSize = isHovered || isSelected ? 20 : 10;
      ctx.beginPath();
      if (isHot) {
        const ring = item.node.id === selected ? "#dc2626" : "#2563eb";
        ctx.strokeStyle = ring;
        ctx.lineWidth = 2.2;
        ctx.beginPath();
        ctx.arc(item.x, item.y, halo, 0, Math.PI * 2);
        ctx.globalAlpha = isSelected ? 0.45 : 0.25;
        ctx.stroke();
        ctx.globalAlpha = 1;
      }
      ctx.beginPath();
      ctx.fillStyle = isHot ? "#dc2626" : color;
      ctx.globalAlpha = Math.max(0.35, health);
      ctx.arc(item.x, item.y, radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = 1;
      ctx.lineWidth = isHot ? 3 : 1;
      ctx.strokeStyle = isHot ? "#7f1d1d" : "#ffffff";
      ctx.stroke();
      if (isHot || radius > 8.5) {
        ctx.fillStyle = "#172033";
        ctx.font = "600 12px Inter, system-ui, sans-serif";
        ctx.fillText(item.node.label.slice(0, 42), item.x + radius + 4, item.y - radius);
      }
      projectedRef.current.push({ id: item.node.id, label: item.node.label, x: item.x, y: item.y, r: clickSize });
    }
    ctx.strokeStyle = "#d8e1ea";
    ctx.lineWidth = 1;
    ctx.strokeRect(0.5, 0.5, width - 1, height - 1);
  }, [nodes, links, selected, hovered, highlightSet, yaw, pitch, zoom]);

  function pointerPosition(event: PointerEvent<HTMLCanvasElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    return { x: event.clientX - rect.left, y: event.clientY - rect.top };
  }

  function findHit(point: { x: number; y: number }) {
    return projectedRef.current
      .map((item) => ({ ...item, d: Math.hypot(item.x - point.x, item.y - point.y) }))
      .filter((item) => item.d <= item.r)
      .sort((a, b) => a.d - b.d)[0];
  }

  function handleWheel(event: WheelEvent<HTMLCanvasElement>) {
    event.preventDefault();
    const direction = event.deltaY > 0 ? -1 : 1;
    setZoom((value) => Math.max(0.42, Math.min(4.2, value * (direction > 0 ? 1.12 : 0.89))));
  }

  return (
    <div className="canvas-3d-wrapper">
      <div className="canvas-toolbar">
        <button
          type="button"
          onClick={() => {
            setYaw(0.62);
            setPitch(0.34);
            setZoom(1);
          }}
        >
          Reset view
        </button>
        <span>{hovered ? `Hover: ${projectedRef.current.find((item) => item.id === hovered)?.label ?? hovered}` : "Drag rotate / wheel zoom / click node"}</span>
        <b>{Math.round(zoom * 100)}%</b>
      </div>
      <canvas
        ref={canvasRef}
        className="canvas-3d"
        data-testid={testId}
        title={hovered ? projectedRef.current.find((item) => item.id === hovered)?.label ?? hovered : "Drag to rotate, wheel to zoom, click a node"}
        style={{ cursor: hovered ? "pointer" : "grab" }}
        onWheel={handleWheel}
        onPointerDown={(event) => {
          const point = pointerPosition(event);
          dragRef.current = { ...point, yaw, pitch, moved: false };
          event.currentTarget.setPointerCapture(event.pointerId);
        }}
        onPointerMove={(event) => {
          const point = pointerPosition(event);
          const drag = dragRef.current;
          if (!drag) {
            setHovered(findHit(point)?.id ?? "");
            return;
          }
          const dx = point.x - drag.x;
          const dy = point.y - drag.y;
          if (Math.hypot(dx, dy) > 5) drag.moved = true;
          setYaw(drag.yaw + dx * 0.008);
          setPitch(Math.max(-1.2, Math.min(1.2, drag.pitch + dy * 0.008)));
        }}
        onPointerUp={(event) => {
          const point = pointerPosition(event);
          const drag = dragRef.current;
          const isDrag = Boolean(drag?.moved);
          const hit = findHit(point);
          if (hit && onSelect && !isDrag) onSelect(hit.id);
          setHovered(hit?.id ?? "");
          dragRef.current = null;
        }}
        onPointerLeave={() => {
          setHovered("");
          dragRef.current = null;
        }}
      />
    </div>
  );
}
