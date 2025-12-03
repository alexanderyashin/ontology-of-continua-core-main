#!/usr/bin/env python3
import os
import sys
import textwrap

import yaml  # pip install pyyaml

# === НАСТРОЙКИ ======================================

# По умолчанию читаем master_core_structure.yaml из корня проекта.
# Можно передать другой путь первым аргументом:
#   python tools/generate_core_from_yaml.py path/to/your.yaml
STRUCTURE_FILE = sys.argv[1] if len(sys.argv) > 1 else "master_core_structure.yaml"

# Сюда вставь свой реальный плейсхолдер из "Codeblock click to copy".
# Можно оставить как есть и потом заменить.
PLACEHOLDER_TEMPLATE = textwrap.dedent("""\
% ================================================================
% ==== FILE: content/k_levels/klevels_master.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/k_levels/klevels_master.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Overview}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/k_levels/k0.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  K-level Module: K0
%  File: content/k_levels/k0.tex
%  Status: EMPTY — STRUCTURAL SKELETON
% ==============================

\section{$K_0$ Overview}
\section{State Space $\Omega(K_0)$}
\section{Boundary $\partial\Omega(K_0)$}
\section{Axes $A(K_0)$}
\section{Potentials $P(K_0)$}
\section{Thresholds $\Theta(K_0)$}
\section{Flows $J(K_0)$}
\section{Cycles $C(K_0)$}
\section{Time $\tau(K_0)$}
\section{Continuumness $k(K_0)$}
\section{Structural Tension $T(K_0)$}
\section{Energy $E(K_0)$}
\section{Operators on $K_0$ ($\Psi$, $\Phi$, $\Lambda$, $U$, $\Chi$)}
\section{Processes on $K_0$}
\section{Predictions for $K_0$}
\section{Experiments for $K_0$}
\section{Collapse and Death of $K_0$}
\section{Falsifiability of $K_0$}
\section{Branching / Ontological Position of $K_0$}
\section{Relation to M-spaces}


% ================================================================
% ==== FILE: content/k_levels/k1.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  K-level Module: K1
%  File: content/k_levels/k1.tex
%  Status: EMPTY — STRUCTURAL SKELETON
% ==============================

\section{$K_1$ Overview}
\section{State Space $\Omega(K_1)$}
\section{Boundary $\partial\Omega(K_1)$}
\section{Axes $A(K_1)$}
\section{Potentials $P(K_1)$}
\section{Thresholds $\Theta(K_1)$}
\section{Flows $J(K_1)$}
\section{Cycles $C(K_1)$}
\section{Time $\tau(K_1)$}
\section{Continuumness $k(K_1)$}
\section{Structural Tension $T(K_1)$}
\section{Energy $E(K_1)$}
\section{Operators on $K_1$ ($\Psi$, $\Phi$, $\Lambda$, $U$, $\Chi$)}
\section{Processes on $K_1$}
\section{Predictions for $K_1$}
\section{Experiments for $K_1$}
\section{Collapse and Death of $K_1$}
\section{Falsifiability of $K_1$}
\section{Branching / Ontological Position of $K_1$}
\section{Relation to M-spaces}


% ================================================================
% ==== FILE: content/k_levels/k2.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  K-level Module: K2
%  File: content/k_levels/k2.tex
%  Status: EMPTY — STRUCTURAL SKELETON
% ==============================

\section{$K_2$ Overview}
\section{State Space $\Omega(K_2)$}
\section{Boundary $\partial\Omega(K_2)$}
\section{Axes $A(K_2)$}
\section{Potentials $P(K_2)$}
\section{Thresholds $\Theta(K_2)$}
\section{Flows $J(K_2)$}
\section{Cycles $C(K_2)$}
\section{Time $\tau(K_2)$}
\section{Continuumness $k(K_2)$}
\section{Structural Tension $T(K_2)$}
\section{Energy $E(K_2)$}
\section{Operators on $K_2$ ($\Psi$, $\Phi$, $\Lambda$, $U$, $\Chi$)}
\section{Processes on $K_2$}
\section{Predictions for $K_2$}
\section{Experiments for $K_2$}
\section{Collapse and Death of $K_2$}
\section{Falsifiability of $K_2$}
\section{Branching / Ontological Position of $K_2$}
\section{Relation to M-spaces}


% ================================================================
% ==== FILE: content/k_levels/k3.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  K-level Module: K3
%  File: content/k_levels/k3.tex
%  Status: EMPTY — STRUCTURAL SKELETON
% ==============================

\section{$K_3$ Overview}
\section{State Space $\Omega(K_3)$}
\section{Boundary $\partial\Omega(K_3)$}
\section{Axes $A(K_3)$}
\section{Potentials $P(K_3)$}
\section{Thresholds $\Theta(K_3)$}
\section{Flows $J(K_3)$}
\section{Cycles $C(K_3)$}
\section{Time $\tau(K_3)$}
\section{Continuumness $k(K_3)$}
\section{Structural Tension $T(K_3)$}
\section{Energy $E(K_3)$}
\section{Operators on $K_3$ ($\Psi$, $\Phi$, $\Lambda$, $U$, $\Chi$)}
\section{Processes on $K_3$}
\section{Predictions for $K_3$}
\section{Experiments for $K_3$}
\section{Collapse and Death of $K_3$}
\section{Falsifiability of $K_3$}
\section{Branching / Ontological Position of $K_3$}
\section{Relation to M-spaces}


% ================================================================
% ==== FILE: content/k_levels/k4.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  K-level Module: K4
%  File: content/k_levels/k4.tex
%  Status: EMPTY — STRUCTURAL SKELETON
% ==============================

\section{$K_4$ Overview}
\section{State Space $\Omega(K_4)$}
\section{Boundary $\partial\Omega(K_4)$}
\section{Axes $A(K_4)$}
\section{Potentials $P(K_4)$}
\section{Thresholds $\Theta(K_4)$}
\section{Flows $J(K_4)$}
\section{Cycles $C(K_4)$}
\section{Time $\tau(K_4)$}
\section{Continuumness $k(K_4)$}
\section{Structural Tension $T(K_4)$}
\section{Energy $E(K_4)$}
\section{Operators on $K_4$ ($\Psi$, $\Phi$, $\Lambda$, $U$, $\Chi$)}
\section{Processes on $K_4$}
\section{Predictions for $K_4$}
\section{Experiments for $K_4$}
\section{Collapse and Death of $K_4$}
\section{Falsifiability of $K_4$}
\section{Branching / Ontological Position of $K_4$}
\section{Relation to M-spaces}


% ================================================================
% ==== FILE: content/k_levels/k5.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  K-level Module: K5
%  File: content/k_levels/k5.tex
%  Status: EMPTY — STRUCTURAL SKELETON
% ==============================

\section{$K_5$ Overview}
\section{State Space $\Omega(K_5)$}
\section{Boundary $\partial\Omega(K_5)$}
\section{Axes $A(K_5)$}
\section{Potentials $P(K_5)$}
\section{Thresholds $\Theta(K_5)$}
\section{Flows $J(K_5)$}
\section{Cycles $C(K_5)$}
\section{Time $\tau(K_5)$}
\section{Continuumness $k(K_5)$}
\section{Structural Tension $T(K_5)$}
\section{Energy $E(K_5)$}
\section{Operators on $K_5$ ($\Psi$, $\Phi$, $\Lambda$, $U$, $\Chi$)}
\section{Processes on $K_5$}
\section{Predictions for $K_5$}
\section{Experiments for $K_5$}
\section{Collapse and Death of $K_5$}
\section{Falsifiability of $K_5$}
\section{Branching / Ontological Position of $K_5$}
\section{Relation to M-spaces}


% ================================================================
% ==== FILE: content/k_levels/k6.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  K-level Module: K6
%  File: content/k_levels/k6.tex
%  Status: EMPTY — STRUCTURAL SKELETON
% ==============================

\section{$K_6$ Overview}
\section{State Space $\Omega(K_6)$}
\section{Boundary $\partial\Omega(K_6)$}
\section{Axes $A(K_6)$}
\section{Potentials $P(K_6)$}
\section{Thresholds $\Theta(K_6)$}
\section{Flows $J(K_6)$}
\section{Cycles $C(K_6)$}
\section{Time $\tau(K_6)$}
\section{Continuumness $k(K_6)$}
\section{Structural Tension $T(K_6)$}
\section{Energy $E(K_6)$}
\section{Operators on $K_6$ ($\Psi$, $\Phi$, $\Lambda$, $U$, $\Chi$)}
\section{Processes on $K_6$}
\section{Predictions for $K_6$}
\section{Experiments for $K_6$}
\section{Collapse and Death of $K_6$}
\section{Falsifiability of $K_6$}
\section{Branching / Ontological Position of $K_6$}
\section{Relation to M-spaces}


% ================================================================
% ==== FILE: content/k_levels/k7.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  K-level Module: K7
%  File: content/k_levels/k7.tex
%  Status: EMPTY — STRUCTURAL SKELETON
% ==============================

\section{$K_7$ Overview}
\section{State Space $\Omega(K_7)$}
\section{Boundary $\partial\Omega(K_7)$}
\section{Axes $A(K_7)$}
\section{Potentials $P(K_7)$}
\section{Thresholds $\Theta(K_7)$}
\section{Flows $J(K_7)$}
\section{Cycles $C(K_7)$}
\section{Time $\tau(K_7)$}
\section{Continuumness $k(K_7)$}
\section{Structural Tension $T(K_7)$}
\section{Energy $E(K_7)$}
\section{Operators on $K_7$ ($\Psi$, $\Phi$, $\Lambda$, $U$, $\Chi$)}
\section{Processes on $K_7$}
\section{Predictions for $K_7$}
\section{Experiments for $K_7$}
\section{Collapse and Death of $K_7$}
\section{Falsifiability of $K_7$}
\section{Branching / Ontological Position of $K_7$}
\section{Relation to M-spaces}


% ================================================================
% ==== FILE: content/k_levels/k8.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  K-level Module: K8
%  File: content/k_levels/k8.tex
%  Status: EMPTY — STRUCTURAL SKELETON
% ==============================

\section{$K_8$ Overview}
\section{State Space $\Omega(K_8)$}
\section{Boundary $\partial\Omega(K_8)$}
\section{Axes $A(K_8)$}
\section{Potentials $P(K_8)$}
\section{Thresholds $\Theta(K_8)$}
\section{Flows $J(K_8)$}
\section{Cycles $C(K_8)$}
\section{Time $\tau(K_8)$}
\section{Continuumness $k(K_8)$}
\section{Structural Tension $T(K_8)$}
\section{Energy $E(K_8)$}
\section{Operators on $K_8$ ($\Psi$, $\Phi$, $\Lambda$, $U$, $\Chi$)}
\section{Processes on $K_8$}
\section{Predictions for $K_8$}
\section{Experiments for $K_8$}
\section{Collapse and Death of $K_8$}
\section{Falsifiability of $K_8$}
\section{Branching / Ontological Position of $K_8$}
\section{Relation to M-spaces}


% ================================================================
% ==== FILE: content/k_levels/k9.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  K-level Module: K9
%  File: content/k_levels/k9.tex
%  Status: EMPTY — STRUCTURAL SKELETON
% ==============================

\section{$K_9$ Overview}
\section{State Space $\Omega(K_9)$}
\section{Boundary $\partial\Omega(K_9)$}
\section{Axes $A(K_9)$}
\section{Potentials $P(K_9)$}
\section{Thresholds $\Theta(K_9)$}
\section{Flows $J(K_9)$}
\section{Cycles $C(K_9)$}
\section{Time $\tau(K_9)$}
\section{Continuumness $k(K_9)$}
\section{Structural Tension $T(K_9)$}
\section{Energy $E(K_9)$}
\section{Operators on $K_9$ ($\Psi$, $\Phi$, $\Lambda$, $U$, $\Chi$)}
\section{Processes on $K_9$}
\section{Predictions for $K_9$}
\section{Experiments for $K_9$}
\section{Collapse and Death of $K_9$}
\section{Falsifiability of $K_9$}
\section{Branching / Ontological Position of $K_9$}
\section{Relation to M-spaces}


% ================================================================
% ==== FILE: content/k_levels/k10.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  K-level Module: K10
%  File: content/k_levels/k10.tex
%  Status: EMPTY — STRUCTURAL SKELETON
% ==============================

\section{$K_{10}$ Overview}
\section{State Space $\Omega(K_{10})$}
\section{Boundary $\partial\Omega(K_{10})$}
\section{Axes $A(K_{10})$}
\section{Potentials $P(K_{10})$}
\section{Thresholds $\Theta(K_{10})$}
\section{Flows $J(K_{10})$}
\section{Cycles $C(K_{10})$}
\section{Time $\tau(K_{10})$}
\section{Continuumness $k(K_{10})$}
\section{Structural Tension $T(K_{10})$}
\section{Energy $E(K_{10})$}
\section{Operators on $K_{10}$ ($\Psi$, $\Phi$, $\Lambda$, $U$, $\Chi$)}
\section{Processes on $K_{10}$}
\section{Predictions for $K_{10}$}
\section{Experiments for $K_{10}$}
\section{Collapse and Death of $K_{10}$}
\section{Falsifiability of $K_{10}$}
\section{Branching / Ontological Position of $K_{10}$}
\section{Relation to M-spaces}


% ================================================================
% ==== FILE: content/k_levels/k11.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  K-level Module: K11
%  File: content/k_levels/k11.tex
%  Status: EMPTY — STRUCTURAL SKELETON
% ==============================

\section{$K_{11}$ Overview}
\section{State Space $\Omega(K_{11})$}
\section{Boundary $\partial\Omega(K_{11})$}
\section{Axes $A(K_{11})$}
\section{Potentials $P(K_{11})$}
\section{Thresholds $\Theta(K_{11})$}
\section{Flows $J(K_{11})$}
\section{Cycles $C(K_{11})$}
\section{Time $\tau(K_{11})$}
\section{Continuumness $k(K_{11})$}
\section{Structural Tension $T(K_{11})$}
\section{Energy $E(K_{11})$}
\section{Operators on $K_{11}$ ($\Psi$, $\Phi$, $\Lambda$, $U$, $\Chi$)}
\section{Processes on $K_{11}$}
\section{Predictions for $K_{11}$}
\section{Experiments for $K_{11}$}
\section{Collapse and Death of $K_{11}$}
\section{Falsifiability of $K_{11}$}
\section{Branching / Ontological Position of $K_{11}$}
\section{Relation to M-spaces}


% ================================================================
% ==== FILE: content/k_levels/k12.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  K-level Module: K12
%  File: content/k_levels/k12.tex
%  Status: EMPTY — STRUCTURAL SKELETON
% ==============================

\section{$K_{12}$ Overview}
\section{State Space $\Omega(K_{12})$}
\section{Boundary $\partial\Omega(K_{12})$}
\section{Axes $A(K_{12})$}
\section{Potentials $P(K_{12})$}
\section{Thresholds $\Theta(K_{12})$}
\section{Flows $J(K_{12})$}
\section{Cycles $C(K_{12})$}
\section{Time $\tau(K_{12})$}
\section{Continuumness $k(K_{12})$}
\section{Structural Tension $T(K_{12})$}
\section{Energy $E(K_{12})$}
\section{Operators on $K_{12}$ ($\Psi$, $\Phi$, $\Lambda$, $U$, $\Chi$)}
\section{Processes on $K_{12}$}
\section{Predictions for $K_{12}$}
\section{Experiments for $K_{12}$}
\section{Collapse and Death of $K_{12}$}
\section{Falsifiability of $K_{12}$}
\section{Branching / Ontological Position of $K_{12}$}
\section{Relation to M-spaces}


% ================================================================
% ==== FILE: content/m_spaces/mspaces_master.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/m_spaces/mspaces_master.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Overview}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/m_spaces/m0.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/m_spaces/m0.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{$M_0$ Overview}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/m_spaces/m1.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/m_spaces/m1.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{$M_1$ Overview}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/m_spaces/m2.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/m_spaces/m2.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{$M_2$ Overview}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/m_spaces/m3.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/m_spaces/m3.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{$M_3$ Overview}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/m_spaces/m4.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/m_spaces/m4.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{$M_4$ Overview}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/m_spaces/m5.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/m_spaces/m5.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{$M_5$ Overview}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/m_spaces/m6.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/m_spaces/m6.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{$M_6$ Overview}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/m_spaces/m7.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/m_spaces/m7.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{$M_7$ Overview}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/m_spaces/m8.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/m_spaces/m8.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{$M_8$ Overview}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/m_spaces/m9.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/m_spaces/m9.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{$M_9$ Overview}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/m_spaces/m10.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/m_spaces/m10.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{$M_{10}$ Overview}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/m_spaces/m11.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/m_spaces/m11.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{$M_{11}$ Overview}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/m_spaces/m12.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/m_spaces/m12.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{$M_{12}$ Overview}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/processes/processes_master.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/processes/processes_master.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Overview}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/processes/processes_k0.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/processes/processes_k0.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Processes on $K_0$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/processes/processes_k1.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/processes/processes_k1.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Processes on $K_1$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/processes/processes_k2.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/processes/processes_k2.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Processes on $K_2$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/processes/processes_k3.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/processes/processes_k3.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Processes on $K_3$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/processes/processes_k4.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/processes/processes_k4.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Processes on $K_4$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/processes/processes_k5.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/processes/processes_k5.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Processes on $K_5$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/processes/processes_k6.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/processes/processes_k6.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Processes on $K_6$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/processes/processes_k7.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/processes/processes_k7.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Processes on $K_7$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/processes/processes_k8.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/processes/processes_k8.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Processes on $K_8$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/processes/processes_k9.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/processes/processes_k9.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Processes on $K_9$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/processes/processes_k10.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/processes/processes_k10.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Processes on $K_{10}$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/processes/processes_k11.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/processes/processes_k11.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Processes on $K_{11}$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/processes/processes_k12.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/processes/processes_k12.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Processes on $K_{12}$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/jets/jets_master.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/jets/jets_master.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Overview}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/jets/jets_k0.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/jets/jets_k0.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Jets on $K_0$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/jets/jets_k1.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/jets/jets_k1.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Jets on $K_1$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/jets/jets_k2.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/jets/jets_k2.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Jets on $K_2$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/jets/jets_k3.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/jets/jets_k3.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Jets on $K_3$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/jets/jets_k4.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/jets/jets_k4.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Jets on $K_4$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/jets/jets_k5.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/jets/jets_k5.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Jets on $K_5$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/jets/jets_k6.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/jets/jets_k6.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Jets on $K_6$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/jets/jets_k7.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/jets/jets_k7.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Jets on $K_7$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/jets/jets_k8.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/jets/jets_k8.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Jets on $K_8$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/jets/jets_k9.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/jets/jets_k9.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Jets on $K_9$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/jets/jets_k10.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/jets/jets_k10.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Jets on $K_{10}$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/jets/jets_k11.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/jets/jets_k11.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Jets on $K_{11}$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/jets/jets_k12.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/jets/jets_k12.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Jets on $K_{12}$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/cycles/cycles_master.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/cycles/cycles_master.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Overview}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/cycles/cycles_k0.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/cycles/cycles_k0.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cycles on $K_0$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/cycles/cycles_k1.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/cycles/cycles_k1.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cycles on $K_1$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/cycles/cycles_k2.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/cycles/cycles_k2.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cycles on $K_2$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/cycles/cycles_k3.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/cycles/cycles_k3.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cycles on $K_3$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/cycles/cycles_k4.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/cycles/cycles_k4.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cycles on $K_4$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/cycles/cycles_k5.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/cycles/cycles_k5.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cycles on $K_5$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/cycles/cycles_k6.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/cycles/cycles_k6.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cycles on $K_6$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/cycles/cycles_k7.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/cycles/cycles_k7.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cycles on $K_7$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/cycles/cycles_k8.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/cycles/cycles_k8.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cycles on $K_8$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/cycles/cycles_k9.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/cycles/cycles_k9.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cycles on $K_9$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/cycles/cycles_k10.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/cycles/cycles_k10.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cycles on $K_{10}$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/cycles/cycles_k11.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/cycles/cycles_k11.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cycles on $K_{11}$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/cycles/cycles_k12.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/cycles/cycles_k12.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cycles on $K_{12}$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/falsifiability/falsifiability_master.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/falsifiability/falsifiability_master.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Overview}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/falsifiability/falsifiability_k0.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/falsifiability/falsifiability_k0.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Falsifiability of $K_0$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/falsifiability/falsifiability_k1.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/falsifiability/falsifiability_k1.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Falsifiability of $K_1$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/falsifiability/falsifiability_k2.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/falsifiability/falsifiability_k2.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Falsifiability of $K_2$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/falsifiability/falsifiability_k3.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/falsifiability/falsifiability_k3.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Falsifiability of $K_3$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/falsifiability/falsifiability_k4.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/falsifiability/falsifiability_k4.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Falsifiability of $K_4$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/falsifiability/falsifiability_k5.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/falsifiability/falsifiability_k5.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Falsifiability of $K_5$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/falsifiability/falsifiability_k6.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/falsifiability/falsifiability_k6.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Falsifiability of $K_6$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/falsifiability/falsifiability_k7.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/falsifiability/falsifiability_k7.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Falsifiability of $K_7$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/falsifiability/falsifiability_k8.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/falsifiability/falsifiability_k8.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Falsifiability of $K_8$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/falsifiability/falsifiability_k9.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/falsifiability/falsifiability_k9.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Falsifiability of $K_9$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/falsifiability/falsifiability_k10.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/falsifiability/falsifiability_k10.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Falsifiability of $K_{10}$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/falsifiability/falsifiability_k11.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/falsifiability/falsifiability_k11.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Falsifiability of $K_{11}$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/falsifiability/falsifiability_k12.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/falsifiability/falsifiability_k12.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Falsifiability of $K_{12}$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/predictions/predictions_master.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/predictions/predictions_master.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Overview}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/predictions/predictions_k0.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/predictions/predictions_k0.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Predictions for $K_0$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/predictions/predictions_k1.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/predictions/predictions_k1.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Predictions for $K_1$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/predictions/predictions_k2.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/predictions/predictions_k2.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Predictions for $K_2$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/predictions/predictions_k3.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/predictions/predictions_k3.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Predictions for $K_3$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/predictions/predictions_k4.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/predictions/predictions_k4.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Predictions for $K_4$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/predictions/predictions_k5.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/predictions/predictions_k5.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Predictions for $K_5$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/predictions/predictions_k6.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/predictions/predictions_k6.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Predictions for $K_6$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/predictions/predictions_k7.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/predictions/predictions_k7.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Predictions for $K_7$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/predictions/predictions_k8.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/predictions/predictions_k8.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Predictions for $K_8$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/predictions/predictions_k9.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/predictions/predictions_k9.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Predictions for $K_9$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/predictions/predictions_k10.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/predictions/predictions_k10.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Predictions for $K_{10}$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/predictions/predictions_k11.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/predictions/predictions_k11.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Predictions for $K_{11}$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/predictions/predictions_k12.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/predictions/predictions_k12.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Predictions for $K_{12}$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/experiments/experiments_master.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/experiments/experiments_master.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Overview}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/experiments/experiments_k0.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/experiments/experiments_k0.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Experiments for $K_0$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/experiments/experiments_k1.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/experiments/experiments_k1.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Experiments for $K_1$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/experiments/experiments_k2.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/experiments/experiments_k2.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Experiments for $K_2$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/experiments/experiments_k3.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/experiments/experiments_k3.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Experiments for $K_3$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/experiments/experiments_k4.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/experiments/experiments_k4.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Experiments for $K_4$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/experiments/experiments_k5.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/experiments/experiments_k5.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Experiments for $K_5$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/experiments/experiments_k6.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/experiments/experiments_k6.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Experiments for $K_6$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/experiments/experiments_k7.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/experiments/experiments_k7.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Experiments for $K_7$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/experiments/experiments_k8.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/experiments/experiments_k8.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Experiments for $K_8$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/experiments/experiments_k9.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/experiments/experiments_k9.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Experiments for $K_9$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/experiments/experiments_k10.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/experiments/experiments_k10.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Experiments for $K_{10}$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/experiments/experiments_k11.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/experiments/experiments_k11.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Experiments for $K_{11}$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/experiments/experiments_k12.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/experiments/experiments_k12.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Experiments for $K_{12}$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/crossk/crossk_master.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/crossk/crossk_master.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Overview}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/crossk/crossk_k0.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/crossk/crossk_k0.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cross-level Structures Involving $K_0$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/crossk/crossk_k1.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/crossk/crossk_k1.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cross-level Structures Involving $K_1$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/crossk/crossk_k2.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/crossk/crossk_k2.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cross-level Structures Involving $K_2$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/crossk/crossk_k3.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/crossk/crossk_k3.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cross-level Structures Involving $K_3$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/crossk/crossk_k4.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/crossk/crossk_k4.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cross-level Structures Involving $K_4$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/crossk/crossk_k5.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/crossk/crossk_k5.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cross-level Structures Involving $K_5$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/crossk/crossk_k6.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/crossk/crossk_k6.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cross-level Structures Involving $K_6$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/crossk/crossk_k7.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/crossk/crossk_k7.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cross-level Structures Involving $K_7$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/crossk/crossk_k8.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/crossk/crossk_k8.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cross-level Structures Involving $K_8$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/crossk/crossk_k9.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/crossk/crossk_k9.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cross-level Structures Involving $K_9$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/crossk/crossk_k10.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/crossk/crossk_k10.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cross-level Structures Involving $K_{10}$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/crossk/crossk_k11.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/crossk/crossk_k11.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cross-level Structures Involving $K_{11}$}
% PLACEHOLDER — TO BE FILLED


% ================================================================
% ==== FILE: content/crossk/crossk_k12.tex
% ================================================================

% ==============================
%  Ontology of Continua — Core
%  PLACEHOLDER MODULE
%  File: content/crossk/crossk_k12.tex
%  Status: EMPTY — TO BE FILLED
% ==============================

\section{Cross-level Structures Involving $K_{12}$}
% PLACEHOLDER — TO BE FILLED


""")

# Если хочешь, чтобы в начале файла был \section/\subsection — включи:
ADD_LATEX_HEADER = True

# ====================================================


def load_nodes(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Поддержка разных стилей YAML:
    #  - верхний уровень = dict с ключом "root" или "sections"
    #  - или просто список нод
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "root" in data:
            return data["root"]
        if "sections" in data:
            return data["sections"]
    raise SystemExit("Не могу понять структуру YAML. Ожидал list или ключ root/sections.")


def ensure_dir_for_file(filepath: str):
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def make_latex_header(title: str, level: int) -> str:
    """
    level 0 -> \section
    level 1 -> \subsection
    level 2 -> \subsubsection
    дальше -> \paragraph
    """
    if not ADD_LATEX_HEADER:
        return ""

    if level == 0:
        cmd = r"\section"
    elif level == 1:
        cmd = r"\subsection"
    elif level == 2:
        cmd = r"\subsubsection"
    else:
        cmd = r"\paragraph"

    return f"{cmd}{{{title}}}\n\n"


def create_file_if_missing(filepath: str, title: str, level: int):
    ensure_dir_for_file(filepath)

    if os.path.exists(filepath):
        print(f"[skip   ] {filepath} (уже существует)")
        return

    header = make_latex_header(title, level)
    content = PLACEHOLDER_TEMPLATE
    if header:
        content = content + header

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[create ] {filepath}")


def walk_nodes(nodes, level=0):
    for node in nodes:
        file = node.get("file")
        if not file:
            # На всякий случай пропускаем ноды без file
            continue

        title = node.get("title") or os.path.splitext(os.path.basename(file))[0]
        create_file_if_missing(file, title, level)

        children = node.get("children") or node.get("subsections") or []
        if children:
            walk_nodes(children, level=level + 1)


def main():
    if not os.path.exists(STRUCTURE_FILE):
        raise SystemExit(f"YAML не найден: {STRUCTURE_FILE}")

    print(f"Использую YAML структуру: {STRUCTURE_FILE}")
    nodes = load_nodes(STRUCTURE_FILE)
    walk_nodes(nodes)
    print("\nГотово: все недостающие .tex-файлы созданы (существующие не трогали).")


if __name__ == "__main__":
    main()
