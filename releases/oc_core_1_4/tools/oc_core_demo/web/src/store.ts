import { create } from "zustand";

export type ViewId =
  | "journey"
  | "guided"
  | "workbench"
  | "km"
  | "wiki"
  | "formula"
  | "klevels"
  | "worldline"
  | "cascade"
  | "benchmarks"
  | "graph"
  | "proof"
  | "gaps"
  | "objections"
  | "whyoc"
  | "practical"
  | "trust"
  | "mission"
  | "surface"
  | "reviewer";

type ExhibitState = {
  view: ViewId;
  selectedConcept: string;
  selectedSimulation: string;
  selectedTarget: string;
  selectedFormulaId: string;
  selectedFormulaSearch: string;
  selectedWikiSearch: string;
  selectedKLevel: string;
  selectedSystem: string;
  selectedDomain: string;
  graphQuery: string;
  setView: (view: ViewId) => void;
  setSelectedConcept: (id: string) => void;
  setSelectedSimulation: (id: string) => void;
  setSelectedTarget: (id: string) => void;
  setSelectedFormulaId: (id: string) => void;
  setSelectedFormulaSearch: (query: string) => void;
  setSelectedWikiSearch: (query: string) => void;
  setSelectedKLevel: (id: string) => void;
  setSelectedSystem: (id: string) => void;
  setSelectedDomain: (id: string) => void;
  setGraphQuery: (query: string) => void;
};

export const useExhibitStore = create<ExhibitState>((set) => ({
  view: "journey",
  selectedConcept: "continuum",
  selectedSimulation: "worldline_birth_evolution_collapse",
  selectedTarget: "OC14-N001",
  selectedFormulaId: "",
  selectedFormulaSearch: "",
  selectedWikiSearch: "",
  selectedKLevel: "K0",
  selectedSystem: "civilization",
  selectedDomain: "PHYSICS",
  graphQuery: "",
  setView: (view) => set({ view }),
  setSelectedConcept: (selectedConcept) => set({ selectedConcept }),
  setSelectedSimulation: (selectedSimulation) => set({ selectedSimulation }),
  setSelectedTarget: (selectedTarget) => set({ selectedTarget }),
  setSelectedFormulaId: (selectedFormulaId) => set({ selectedFormulaId }),
  setSelectedFormulaSearch: (selectedFormulaSearch) => set({ selectedFormulaSearch }),
  setSelectedWikiSearch: (selectedWikiSearch) => set({ selectedWikiSearch }),
  setSelectedKLevel: (selectedKLevel) => set({ selectedKLevel }),
  setSelectedSystem: (selectedSystem) => set({ selectedSystem }),
  setSelectedDomain: (selectedDomain) => set({ selectedDomain }),
  setGraphQuery: (graphQuery) => set({ graphQuery })
}));
