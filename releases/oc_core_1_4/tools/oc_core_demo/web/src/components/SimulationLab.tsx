import { useMemo, useState } from "react";
import { line, scaleLinear } from "d3";
import type { SimulationSpec } from "../types";
import { runSimulation } from "../simulations";
import { stableHash } from "../data";

function defaultParams(spec: SimulationSpec): Record<string, number> {
  const params: Record<string, number> = {};
  for (const [key, block] of Object.entries(spec.parameters)) {
    if (typeof block.default === "number") params[key] = block.default;
  }
  return params;
}

export function SimulationLab({ specs, selectedId, onSelect }: { specs: SimulationSpec[]; selectedId: string; onSelect: (id: string) => void }) {
  const spec = specs.find((item) => item.id === selectedId) ?? specs[0];
  const [params, setParams] = useState<Record<string, number>>(() => defaultParams(spec));
  const [scrub, setScrub] = useState(100);
  const result = useMemo(() => runSimulation(spec.id, params), [spec.id, params]);
  const visibleSeries = result.series.slice(0, Math.max(2, Math.ceil((result.series.length * scrub) / 100)));
  const x = scaleLinear().domain([0, Math.max(...result.series.map((point) => point.step), 1)]).range([24, 416]);
  const yMax = Math.max(1, ...result.series.map((point) => point.value));
  const y = scaleLinear().domain([0, yMax]).range([190, 18]);
  const path = line<{ step: number; value: number }>()
    .x((point) => x(point.step))
    .y((point) => y(point.value))(visibleSeries) ?? "";

  function setParam(key: string, value: number) {
    setParams((current) => ({ ...current, [key]: value }));
  }

  return (
    <section className="view-grid simulation-view">
      <aside className="rail">
        <h2>Simulation Lab</h2>
        {specs.map((item) => (
          <button
            className={item.id === spec.id ? "nav-pill active" : "nav-pill"}
            key={item.id}
            onClick={() => {
              onSelect(item.id);
              setParams(defaultParams(item));
              setScrub(100);
            }}
          >
            {item.title}
          </button>
        ))}
      </aside>
      <main className="panel big-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">{spec.visual_type}</p>
            <h2>{spec.title}</h2>
            <p>{spec.purpose}</p>
          </div>
          <div className="hash-badge">hash {stableHash({ spec: spec.id, params, result })}</div>
        </div>
        <div className="sim-layout">
          <div className="plot-card">
            <svg viewBox="0 0 440 220" className="plot-svg" data-testid="simulation-plot">
              <rect x="0" y="0" width="440" height="220" rx="10" fill="#f8fbff" />
              {[0.25, 0.5, 0.75].map((tick) => (
                <line key={tick} x1="24" x2="416" y1={y(tick * yMax)} y2={y(tick * yMax)} stroke="#dbe4ee" />
              ))}
              <path d={path} fill="none" stroke="#2563eb" strokeWidth="4" strokeLinecap="round" />
              {visibleSeries.map((point, index) => (
                index % Math.ceil(visibleSeries.length / 8) === 0 ? <circle key={point.step} cx={x(point.step)} cy={y(point.value)} r="4" fill="#0f766e" /> : null
              ))}
              <text x="24" y="210" fill="#64748b">step</text>
              <text x="12" y="24" fill="#64748b">state</text>
            </svg>
            <div className="sim-summary">
              <span>{result.band}</span>
              <strong>{Number(result.score).toFixed(3)}</strong>
            </div>
          </div>
          <div className="control-card">
            <h3>Parameters</h3>
            {Object.entries(spec.parameters).map(([key, block]) => {
              if (typeof block.default !== "number") return null;
              return (
                <label className="slider-row" key={key}>
                  <span>{key.replaceAll("_", " ")}</span>
                  <input
                    type="range"
                    min={block.min ?? 0}
                    max={block.max ?? 1}
                    step={block.type === "integer" ? 1 : 0.01}
                    value={params[key] ?? block.default}
                    onChange={(event) => setParam(key, Number(event.target.value))}
                  />
                  <b>{params[key]}</b>
                </label>
              );
            })}
            <label className="slider-row">
              <span>timeline scrub</span>
              <input type="range" min="5" max="100" value={scrub} onChange={(event) => setScrub(Number(event.target.value))} />
              <b>{scrub}%</b>
            </label>
            <button className="command" onClick={() => setParams(defaultParams(spec))}>Reset</button>
          </div>
        </div>
        <div className="note-grid">
          <div className="note"><strong>Interpretation</strong><br />{result.interpretation}</div>
          <div className="note"><strong>Boundary</strong><br />{spec.limits[0]}</div>
          <div className="note"><strong>Evidence refs</strong><br />{spec.evidence_refs.join(", ")}</div>
        </div>
      </main>
    </section>
  );
}
