---
title: Ontology of Continua Core 1.3.3
subtitle: Bounded external-review scientific release
author: Alexander Yashin
date: 2026-05-01
---

# Ontology of Continua Core 1.3.3

Version: 1.3.3
Tag: v1.3.3
DOI: 10.5281/zenodo.19965913
Zenodo record: https://zenodo.org/records/19965913


## Release Boundary

OC Core 1.3.3 is a bounded external-review scientific release. It contains a typed model foundation, theorem/proof evidence, a Lean-checked subset, finite-model semantics, target-blind numeric reconstruction rows, comparator positioning, adversarial-review closure, and journal owner-review packets.

The release does not claim final completion of every future scientific projection. It does not submit journal packages. It does not claim universal superiority over all modern science. Those broader ambitions remain in the background research program and require additional evidence before public promotion.

The public GitHub and Zenodo publication is owner-approved for this release phase. Journal submissions, email campaigns, and Software Heritage actions require separate approval.


## Lean Formalization Subset

The Lean subset is a machine-checked subset of the OC 1.3.3 theorem surface. The release does not claim that every mathematical or empirical statement is fully formalized in Lean.
- **certificate state:** 
- **theorem ref total:** 10
- **missing theorem ref total:** 
- **Lean file:** formal/lean/OC133V12.lean

Selected declaration excerpt:

```lean
namespace OC133V12

inductive Status where
 | pass
 | fail
deriving DecidableEq, Repr

inductive CycleMode where
 | maintenance
 | renewal
 | replay
 | regulatory
 | degenerate
deriving DecidableEq, Repr

inductive MorphismClass where
 | identity
 | residue
 | rebirth
deriving DecidableEq, Repr

inductive Component where
 | carrier
 | realization
 | lawfulPossibility
 | liveness
 | residue
 | morphisms
 | boundaries
 | operators
 | cycles
 | dimension
 | kFunctional
deriving DecidableEq, Repr

inductive AdjacentK where
 | k0_k1
 | k1_k2
 | k2_k3
 | k3_k4
 | k4_k5
 | k5_k6
 | k6_k7
 | k7_k8
 | k8_k9
 | k9_k10
 | k10_k11
 | k11_k12
deriving DecidableEq, Repr

def boolStatus (b : Bool) : Status :=
 if b then Status.pass else Status.fail

structure Resolution (S : Type) where
 cell : S -> Nat

structure RawSeparation (S : Type) where
 separated : S -> S -> Bool

def sameCell {S : Type} (rho : Resolution S) (a b : S) : Prop :=
 rho.cell a = rho.cell b

def distinguished {S : Type} (rho : Resolution S) (a b : S) : Prop :=
 rho.cell a != rho.cell b

theorem k0_same_cell_not_distinguished {S : Type} (rho : Resolution S) (a b : S) :
 sameCell rho a b -> distinguished rho a b = False := by
 intro h
 unfold distinguished
 rw [h]
 simp

theorem k0_distinguished_requires_resolved_delta {S : Type} (rho : Resolution S) (a b : S) :
 distinguished rho a b -> sameCell rho a b -> False := by
 intro hd hs
 rw [k0_same_cell_not_distinguished rho a b hs] at hd
 exact hd

theorem k0_resolution_does_not_force_raw_separation {S : Type}
 (rho : Resolution S) (raw : RawSeparation S) (a b : S) :
 sameCell rho a b -> raw.separated a b = true -> distinguished rho a b = False := by
 intro hs _
 exact k0_same_cell_not_distinguished rho a b hs

inductive K0CounterPoint where
 | a
 | b
deriving DecidableEq, Repr

def k0CounterResolution : Resolution K0CounterPoint :=
 { cell := fun _ => 0 }

def k0CounterRawSeparation : RawSeparation K0CounterPoint :=
 { separated := fun x y => decide (x != y) }

theorem k0_countermodel_raw_separation_not_resolution_distinction :
 sameCell k0CounterResolution K0CounterPoint.a K0CounterPoint.b /\
 k0CounterRawSeparation.separated K0CounterPoint.a K0CounterPoint.b = true /\
 distinguished k0CounterResolution K0CounterPoint.a K0CounterPoint.b = False := by
 exact And.intro rfl (And.intro (by decide) (k0_same_cell_not_distinguished k0CounterResolution K0CounterPoint.a K0CounterPoint.b rfl))

structure MaintenanceEvidence where
 obligationChecked : Bool
 supportAvailable : Bool

def nonVacuousMaintenance (m : MaintenanceEvidence) : Prop :=
 m.obligationChecked = true /\ m.supportAvailable = true

structure Realization where
 Carrier : Type
 admissible : Carrier -> Bool
 live : Carrier -> Bool
 cycle : Carrier -> Option CycleMode
 maintenance : Carrier -> Option MaintenanceEvidence

def maintenanceWitnessed (R : Realization) (x : R.Carrier) : Prop :=
 exists m, R.maintenance x = some m /\ nonVacuousMaintenance m

def cycleWitnessed (R : Realization) (x : R.Carrier) : Prop :=
 match R.cycle x with
 | none => False
 | some CycleMode.degenerate => maintenanceWitnessed R x
 | some _ => True

def supportWitnessed (R : Realization) (x : R.Carrier) : Prop :=
 cycleWitnessed R x \/ maintenanceWitnessed R x

def eligibleLive (R : Realization) (x : R.Carrier) : Prop :=
 R.admissible x = true /\ R.live x = true /\ supportWitnessed R x

theorem eligible_live_requires_cycle (R : Realization) (x : R.Carrier) :
 eligibleLive R x -> supportWitnessed R x := by
 intro h
 exact h.right.right

theorem eligible_live_requires_cycle_or_maintenance (R : Realization) (x : R.Carrier) :
 eligibleLive R x -> cycleWitnessed R x \/ maintenanceWitnessed R x := by
 intro h
 exact h.right.right

theorem eligible_live_requires_admissible (R : Realization) (x : R.Carrier) :
 eligibleLive R x -> R.admissible x = true := by
 intro h
 exact h.left

theorem cycle_mode_required_for_eligible_live (R : Realization) (x : R.Carrier) :
 eligibleLive R x -> (R.maintenance x = none) -> R.cycle x != none := by
 intro h hm
 cases h.right.right with
 | inl hc =>
 unfold cycleWitnessed at hc
 cases hcyc : R.cycle x with
 | none =>
 rw [hcyc] at hc
 cases hc
 | some c =>
 simp
 | inr hmnt =>
 rcases hmnt with ⟨m, hsome, _⟩
 rw [hm] at hsome
 cases hsome

structure Lifecycle (S Residue NewLive : Type) where
 admissible : S -> Bool
 live : S -> Bool
 death : S -> Bool
 deathBlocksLive : forall x : S, death x = true -> live x = false
 residueOf : S -> Option Residue
 rebirthOf : Residue -> Option NewLive
 identityInvariant : S -> NewLive -> Bool
 sourceToken : S -> Nat
 residueToken : Residue -> Nat
 newLiveToken : NewLive -> Nat
 sourceTokenInjective : forall x y : S, sourceToken x = sourceToken y -> x = y
 residueTokenInjective : forall x y : Residue, residueToken x = residueToken y -> x = y
 newLiveTokenInjective : forall x y : NewLive, newLiveToken x = newLiveToken y -> x = y

theorem declared_death_blocks_live {S Residue NewLive : Type}
 (L : Lifecycle S Residue NewLive) (x : S) :
 L.death x = true -> L.live x = false := by
 intro h
 exact L.deathBlocksLive x h

theorem death_live_conflict_impossible {S Residue NewLive : Type}
 (L : Lifecycle S Residue NewLive) (x : S) :
 L.death x = true -> L.live x = true -> False := by
 intro hdeath hlive
 have hblocked : L.live x = false := L.deathBlocksLive x hdeath
 rw [hlive] at hblocked
 cases hblocked

theorem residue_rebirth_are_typed_source_target_relations {S Residue NewLive : Type}
 (L : Lifecycle S Residue NewLive) (x : S) (r : Residue) (y : NewLive) :
 L.residueOf x = some r -> L.rebirthOf r = some y -> L.death x = true ->
 L.live x = false /\ L.residueOf x = some r /\ L.rebirthOf r = some y := by
 intro hres hreb hdeath
 exact And.intro (declared_death_blocks_live L x hdeath) (And.intro hres hreb)

theorem lifecycle_source_tokens_bind_carrier_endpoint {S Residue NewLive : Type}
 (L : Lifecycle S Residue NewLive) (x y : S) :
 L.sourceToken x = L.sourceToken y -> x = y := by
 exact L.sourceTokenInjective x y

theorem lifecycle_rebirth_tokens_bind_target_endpoint {S Residue NewLive : Type}
 (L : Lifecycle S Residue NewLive) (x y : NewLive) :
 L.newLiveToken x = L.newLiveToken y -> x = y := by
 exact L.newLiveTokenInjective x y

structure MorphismEvidence where
 sourceToken : Nat
 residueToken : Option Nat
 targetToken : Nat
 mclass : MorphismClass
 invariantPreserved : Bool

def isIdentityMorphism (m : MorphismEvidence) : Prop :=
 m.mclass = MorphismClass.identity /\
 m.invariantPreserved = true /\
 m.residueToken = none /\
 m.sourceToken = m.targetToken
```


## Executable Finite-Model Evidence

The finite-model runner computes semantic verdicts from model facts and mutation controls. The public summary below omits internal publication-control rows and preserves the semantic proof evidence.
- **verdict:** 
- **failure total:** 0
- **semantic evaluator:** True
- **mutation control total:** 6
- **K-transition negative total:** 12

### FM-T133-K0-RES-POS

- **case type:** theorem_case
- **observed verdict:** ACCEPT
- **expected verdict:** ACCEPT
- **failure total:** 
- **witness:** 

### FM-T133-K0-RES-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-OMEGA-STATUS-POS

- **case type:** theorem_case
- **observed verdict:** ACCEPT
- **expected verdict:** ACCEPT
- **failure total:** 
- **witness:** 

### FM-T133-OMEGA-STATUS-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-OMEGA-IDENTITY-EQUIVOCATION-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-K-ZERO-POS

- **case type:** theorem_case
- **observed verdict:** ACCEPT
- **expected verdict:** ACCEPT
- **failure total:** 
- **witness:** 

### FM-T133-K-ZERO-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-K-ZERO-OBSTRUCTION-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-K-ZERO-LIVE-SUPPORT-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-BOUNDARY-POS

- **case type:** theorem_case
- **observed verdict:** ACCEPT
- **expected verdict:** ACCEPT
- **failure total:** 
- **witness:** 

### FM-T133-BOUNDARY-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-HYBRID-POS

- **case type:** theorem_case
- **observed verdict:** ACCEPT
- **expected verdict:** ACCEPT
- **failure total:** 
- **witness:** 

### FM-T133-HYBRID-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-HYBRID-NO-GUARD-STEP-POS

- **case type:** theorem_case
- **observed verdict:** ACCEPT
- **expected verdict:** ACCEPT
- **failure total:** 
- **witness:** 

### FM-T133-HYBRID-NO-GUARD-STEP-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-HYBRID-GUARD-MISSING-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-HYBRID-GUARD-NONBOOLEAN-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-HYBRID-GUARD-VALUE-MISMATCH-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-HYBRID-RESET-SOURCE-MODE-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-HYBRID-RESET-TARGET-MODE-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-HYBRID-SMOOTH-CHART-POS

- **case type:** theorem_case
- **observed verdict:** ACCEPT
- **expected verdict:** ACCEPT
- **failure total:** 
- **witness:** 

### FM-T133-HYBRID-SMOOTH-CHART-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-HYBRID-PROOF-UPDATE-POS

- **case type:** theorem_case
- **observed verdict:** ACCEPT
- **expected verdict:** ACCEPT
- **failure total:** 
- **witness:** 

### FM-T133-HYBRID-PROOF-UPDATE-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-HYBRID-SMOOTH-LOCAL-LAW-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-HYBRID-PROOF-NO-RULE-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-DIM-POS

- **case type:** theorem_case
- **observed verdict:** ACCEPT
- **expected verdict:** ACCEPT
- **failure total:** 
- **witness:** 

### FM-T133-DIM-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-CYCLE-POS

- **case type:** theorem_case
- **observed verdict:** ACCEPT
- **expected verdict:** ACCEPT
- **failure total:** 
- **witness:** 

### FM-T133-CYCLE-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-REBIRTH-NONIDENTITY-POS

- **case type:** theorem_case
- **observed verdict:** ACCEPT
- **expected verdict:** ACCEPT
- **failure total:** 
- **witness:** 

### FM-T133-ID-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-RESIDUE-POS

- **case type:** theorem_case
- **observed verdict:** ACCEPT
- **expected verdict:** ACCEPT
- **failure total:** 
- **witness:** 

### FM-T133-ID-RESIDUE-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-IDENTITY-POS

- **case type:** theorem_case
- **observed verdict:** ACCEPT
- **expected verdict:** ACCEPT
- **failure total:** 
- **witness:** 

### FM-T133-MIN-POS

- **case type:** theorem_case
- **observed verdict:** ACCEPT
- **expected verdict:** ACCEPT
- **failure total:** 
- **witness:** 

### FM-T133-MIN-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-KLEVEL-POS

- **case type:** theorem_case
- **observed verdict:** ACCEPT
- **expected verdict:** ACCEPT
- **failure total:** 
- **witness:** 

### FM-T133-KLEVEL-NEG

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-IDENTITY-INV-FALSE-END-FALSE-RES-FALSE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-IDENTITY-INV-FALSE-END-FALSE-RES-FALSE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-IDENTITY-INV-FALSE-END-FALSE-RES-TRUE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-IDENTITY-INV-FALSE-END-FALSE-RES-TRUE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-IDENTITY-INV-FALSE-END-TRUE-RES-FALSE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** ACCEPT
- **expected verdict:** ACCEPT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-IDENTITY-INV-FALSE-END-TRUE-RES-FALSE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-IDENTITY-INV-FALSE-END-TRUE-RES-TRUE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-IDENTITY-INV-FALSE-END-TRUE-RES-TRUE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-IDENTITY-INV-TRUE-END-FALSE-RES-FALSE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-IDENTITY-INV-TRUE-END-FALSE-RES-FALSE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-IDENTITY-INV-TRUE-END-FALSE-RES-TRUE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-IDENTITY-INV-TRUE-END-FALSE-RES-TRUE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-IDENTITY-INV-TRUE-END-TRUE-RES-FALSE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-IDENTITY-INV-TRUE-END-TRUE-RES-FALSE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** ACCEPT
- **expected verdict:** ACCEPT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-IDENTITY-INV-TRUE-END-TRUE-RES-TRUE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-IDENTITY-INV-TRUE-END-TRUE-RES-TRUE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-RESIDUE-INV-FALSE-END-FALSE-RES-FALSE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-RESIDUE-INV-FALSE-END-FALSE-RES-FALSE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-RESIDUE-INV-FALSE-END-FALSE-RES-TRUE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-RESIDUE-INV-FALSE-END-FALSE-RES-TRUE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-RESIDUE-INV-FALSE-END-TRUE-RES-FALSE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-RESIDUE-INV-FALSE-END-TRUE-RES-FALSE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-RESIDUE-INV-FALSE-END-TRUE-RES-TRUE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** ACCEPT
- **expected verdict:** ACCEPT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-RESIDUE-INV-FALSE-END-TRUE-RES-TRUE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-RESIDUE-INV-TRUE-END-FALSE-RES-FALSE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-RESIDUE-INV-TRUE-END-FALSE-RES-FALSE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-RESIDUE-INV-TRUE-END-FALSE-RES-TRUE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-RESIDUE-INV-TRUE-END-FALSE-RES-TRUE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-RESIDUE-INV-TRUE-END-TRUE-RES-FALSE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-RESIDUE-INV-TRUE-END-TRUE-RES-FALSE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-RESIDUE-INV-TRUE-END-TRUE-RES-TRUE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** ACCEPT
- **expected verdict:** ACCEPT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-RESIDUE-INV-TRUE-END-TRUE-RES-TRUE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-REBIRTH-INV-FALSE-END-FALSE-RES-FALSE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-REBIRTH-INV-FALSE-END-FALSE-RES-FALSE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-REBIRTH-INV-FALSE-END-FALSE-RES-TRUE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** ACCEPT
- **expected verdict:** ACCEPT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-REBIRTH-INV-FALSE-END-FALSE-RES-TRUE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-REBIRTH-INV-FALSE-END-TRUE-RES-FALSE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-REBIRTH-INV-FALSE-END-TRUE-RES-FALSE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-REBIRTH-INV-FALSE-END-TRUE-RES-TRUE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-REBIRTH-INV-FALSE-END-TRUE-RES-TRUE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-REBIRTH-INV-TRUE-END-FALSE-RES-FALSE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-REBIRTH-INV-TRUE-END-FALSE-RES-FALSE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-REBIRTH-INV-TRUE-END-FALSE-RES-TRUE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** ACCEPT
- **expected verdict:** ACCEPT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-REBIRTH-INV-TRUE-END-FALSE-RES-TRUE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-REBIRTH-INV-TRUE-END-TRUE-RES-FALSE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-REBIRTH-INV-TRUE-END-TRUE-RES-FALSE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-REBIRTH-INV-TRUE-END-TRUE-RES-TRUE-CLAIM-FALSE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-T133-ID-TT-REBIRTH-INV-TRUE-END-TRUE-RES-TRUE-CLAIM-TRUE

- **case type:** theorem_case
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### FM-MIN-carrier

- **case type:** component_keep_drop_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-MIN-realization

- **case type:** component_keep_drop_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-MIN-lawful_possibility

- **case type:** component_keep_drop_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-MIN-liveness

- **case type:** component_keep_drop_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-MIN-residue

- **case type:** component_keep_drop_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-MIN-morphisms

- **case type:** component_keep_drop_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-MIN-boundaries

- **case type:** component_keep_drop_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-MIN-operators

- **case type:** component_keep_drop_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-MIN-cycles

- **case type:** component_keep_drop_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-MIN-dimension

- **case type:** component_keep_drop_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-MIN-k

- **case type:** component_keep_drop_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K0_to_K1

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K0_to_K1-NEG

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K1_to_K2

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K1_to_K2-NEG

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K2_to_K3

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K2_to_K3-NEG

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K3_to_K4

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K3_to_K4-NEG

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K4_to_K5

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K4_to_K5-NEG

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K5_to_K6

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K5_to_K6-NEG

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K6_to_K7

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K6_to_K7-NEG

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K7_to_K8

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K7_to_K8-NEG

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K8_to_K9

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K8_to_K9-NEG

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K9_to_K10

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K9_to_K10-NEG

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K10_to_K11

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K10_to_K11-NEG

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K11_to_K12

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### FM-KLEVEL-K11_to_K12-NEG

- **case type:** adjacent_k_transition_witness
- **observed verdict:** 
- **expected verdict:** 
- **failure total:** 
- **witness:** 

### MUTATION-LABEL-ONLY-MIN

- **case type:** mutation_control
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### MUTATION-FLAG-ORACLE-BOUNDARY

- **case type:** mutation_control
- **observed verdict:** REJECT_FLAG_ORACLE_INPUT
- **expected verdict:** REJECT_FLAG_ORACLE_INPUT
- **failure total:** 
- **witness:** 

### MUTATION-WRONG-WITNESS-KLEVEL

- **case type:** mutation_control
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### MUTATION-WRONG-KLEVEL-TEXT

- **case type:** mutation_control
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### MUTATION-DUPLICATED-KLEVEL

- **case type:** mutation_control
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 

### MUTATION-MISSING-KLEVEL-CRITERION

- **case type:** mutation_control
- **observed verdict:** REJECT
- **expected verdict:** REJECT
- **failure total:** 
- **witness:** 


## Target-Blind Numeric Evidence

The empirical section reports bounded target-blind reconstruction rows over pinned official snapshots. These rows support model-core external review; they do not claim complete domain validation.
- **lane total:** 5
- **failure total:** 0
- **support policy:** Rows are target-blind held-out reconstructions over pinned official snapshots. They support bounded numeric reconstruction claims only, not broad domain validation or novelty.
- **domain validation policy:** NO_EMPIRICAL_PASS_FROM_OFFICIAL_SNAPSHOT_REPLAY_QA

### Physics - OC133-TARGETBLIND-PHYSICS-001

- **snapshot:** validation/_raw/physics_nist_constants.txt
- **target-blind split:** Planck constant and speed of light rows are visible; inverse-meter joule relationship row is withheld until scoring
- **formula:** Planck_constant * speed_of_light
- **predicted value:** 1.9864458571489286e-25
- **observed value:** 1.986445857e-25
- **uncertainty:** 1e-33
- **residual:** 1.4892870576445277e-35
- **comparator baseline:** unit-incompatible Planck-constant-only negative control
- **comparator residual:** 1.9864458503739297e-25
- **negative control:** drop the speed-of-light factor and require a larger residual
- **falsifier:** Residual exceeds display-truncation tolerance or Planck-only control is not worse
- **snapshot hash:** 77fb90e66c40db3e6eb16630bc9c88e4c7c8beddbe5e71be406f2f26e3f67e67
- **replay hash:** a83ea273ef65d6136ad7c0dfe2f7d870822fe15a062a47ae906a7d46705a0cf1
- **support scope:** target-blind reconstruction of a held-out CODATA relationship from exact defining constants; not a novel physics law

### Chemistry - OC133-TARGETBLIND-CHEMISTRY-001

- **snapshot:** validation/_raw/chemistry_pubchem_water.txt
- **target-blind split:** formula field is visible; MolecularWeight target is withheld until scoring
- **formula:** 2*atomic_weight(H)+atomic_weight(O)
- **predicted value:** 18.01528
- **observed value:** 18.015
- **uncertainty:** 0.02
- **residual:** 0.000280000000000058
- **comparator baseline:** CO2 molecular-weight negative control against water target
- **comparator residual:** 25.994500000000002
- **negative control:** replace H2O by CO2 and require larger residual
- **falsifier:** Residual exceeds declared uncertainty or CO2 control is not worse than formula reconstruction
- **snapshot hash:** 316ed3babcf1b5fd6580fc2922881bf553b5971de33b72f268d943529bce293f
- **replay hash:** c115a6d84fdad856976f60ad6d2fb4c9f9c397f994c7eafb09526f944004469d
- **support scope:** target-blind reconstruction of a held-out official snapshot field; not a novel chemistry law

### Biology - OC133-TARGETBLIND-BIOLOGY-001

- **snapshot:** validation/_raw/biology_ncbi_geo_platform.txt
- **target-blind split:** NCBI ESearch retstart/idlist fields are visible; retmax pagination target is withheld until scoring
- **formula:** retstart + len(idlist)
- **predicted value:** 20.0
- **observed value:** 20.0
- **uncertainty:** 0.0
- **residual:** 0.0
- **comparator baseline:** use total hit count as pagination-size negative control
- **comparator residual:** 43988.0
- **negative control:** replace page-size reconstruction by total hit count and require a larger residual
- **falsifier:** Retmax differs from retstart plus returned id count or total-count control is not worse
- **snapshot hash:** f205645ec097af8972f7c70f4753a5d7eb154c4283e9caa454235843974bfda4
- **replay hash:** 6606a563b35116d6852bc936618757a29873c52e59541a0928546bc863cd4ecb
- **support scope:** target-blind reconstruction of a held-out NCBI/GEO API snapshot field; not a biological mechanism law

### Systems - OC133-TARGETBLIND-SYSTEMS-001

- **snapshot:** validation/_raw/systems_world_bank_gdp.txt
- **target-blind split:** 2021-2023 train rows predict withheld 2024 World Bank WDI target
- **formula:** GDP_2023 + (GDP_2023-GDP_2021)/2
- **predicted value:** 111042234099108.1
- **observed value:** 110982661180013.0
- **uncertainty:** 1109826611800.1301
- **residual:** 59572919095.09375
- **comparator baseline:** last-observation carry-forward GDP_2023
- **comparator residual:** 4241013358949.0
- **negative control:** last-observation baseline must have larger residual
- **falsifier:** Held-out residual exceeds 1 percent of observed target or comparator is not worse
- **snapshot hash:** 52a3dcef732b262251662f20923d00ba8d4df239cce96097abf67ee6b15ff12b
- **replay hash:** 778ffef9592179e6062fad4b770d02612408603c70455f734c423475ff704be4
- **support scope:** retrospective target-blind holdout over pinned WDI rows; not a prospective macroeconomic law

### Mathematics - OC133-TARGETBLIND-MATHEMATICS-001

- **snapshot:** proofs/FINITE_MODEL_CHECKS_1_3_3.json
- **target-blind split:** finite theorem-case rows are visible; aggregate machine_checked_subset_total is withheld until scoring
- **formula:** count_unique(theorem_id where case_type='theorem_case' and observed_verdict='ACCEPT' and passed=true)
- **predicted value:** 10.0
- **observed value:** 10.0
- **uncertainty:** 0.0
- **residual:** 0.0
- **comparator baseline:** positive_case_total negative control, which counts non-theorem support rows too
- **comparator residual:** 11.0
- **negative control:** replace theorem-id aggregate by positive_case_total and require a larger residual
- **falsifier:** Unique accepted theorem-case count differs from machine_checked_subset_total or broad positive-case control is not worse
- **snapshot hash:** 46ac711a2e86375ed333ce5c8a8b1b810f1f5b052fa657fb1508dbe7831b2f49
- **replay hash:** 050e21ffb0f2a5b73ea7faab51da781bbe66adc6bc6376941bb0a0e4eda293f2
- **support scope:** target-blind reconstruction of a finite proof-corpus aggregate; not a full-science program truth proof or empirical law

### Replay Audit - Biology

- **verdict:** NUMERIC_REPLAY_QA_NOT_DOMAIN_VALIDATION
- **failure total:** 0
- **source log:** validation/numeric_predictions/OC133_NUMERIC_REPLAY_LOG.json

- **row:** OC133-NUM-BIO-GEO-COUNT
- **snapshot opened:** True
- **computed residual:** 0.0
- **negative control rejected:** True

### Replay Audit - Chemistry

- **verdict:** NUMERIC_REPLAY_QA_NOT_DOMAIN_VALIDATION
- **failure total:** 0
- **source log:** validation/numeric_predictions/OC133_NUMERIC_REPLAY_LOG.json

- **row:** OC133-NUM-CHEM-WEBBOOK-H2O
- **snapshot opened:** True
- **computed residual:** 0.0
- **negative control rejected:** True

- **row:** OC133-NUM-CHEM-H2O
- **snapshot opened:** True
- **computed residual:** 0.0
- **negative control rejected:** True

### Replay Audit - Mathematics

- **verdict:** NUMERIC_REPLAY_QA_NOT_DOMAIN_VALIDATION
- **failure total:** 0
- **source log:** validation/numeric_predictions/OC133_NUMERIC_REPLAY_LOG.json

- **row:** OC133-NUM-MATH-FINITE
- **snapshot opened:** True
- **computed residual:** 0.0
- **negative control rejected:** True

### Replay Audit - Physics

- **verdict:** NUMERIC_REPLAY_QA_NOT_DOMAIN_VALIDATION
- **failure total:** 0
- **source log:** validation/numeric_predictions/OC133_NUMERIC_REPLAY_LOG.json

- **row:** OC133-NUM-PHYS-C
- **snapshot opened:** True
- **computed residual:** 0.0
- **negative control rejected:** True

### Replay Audit - Systems

- **verdict:** NUMERIC_REPLAY_QA_NOT_DOMAIN_VALIDATION
- **failure total:** 0
- **source log:** validation/numeric_predictions/OC133_NUMERIC_REPLAY_LOG.json

- **row:** OC133-NUM-SYS-WDI-GDP
- **snapshot opened:** True
- **computed residual:** 0.0
- **negative control rejected:** True


## Journal Owner-Review Packages

Eight venue packets are included for owner review. They are not submitted by this release action. Each packet contains a package manifest, cover letter draft, checklist, reproducibility/data statement, conflict/funding statement, AI assistance disclosure, and venue-fit note.
- **package total:** 8
- **recommended package total:** 2

### FOUNDATIONS_OF_SCIENCE

- **package status:** OWNER_REVIEW_READY_FOR_OWNER_REVIEW
- **submission allowed:** False
- **journal submissions allowed:** False
- **recommended:** 

### SYNTHESE

- **package status:** OWNER_REVIEW_READY_FOR_OWNER_REVIEW
- **submission allowed:** False
- **journal submissions allowed:** False
- **recommended:** 

### FOUNDATIONS_OF_PHYSICS

- **package status:** OWNER_REVIEW_READY_FOR_OWNER_REVIEW
- **submission allowed:** False
- **journal submissions allowed:** False
- **recommended:** 

### PHYSICAL_REVIEW_RESEARCH

- **package status:** OWNER_REVIEW_READY_FOR_OWNER_REVIEW
- **submission allowed:** False
- **journal submissions allowed:** False
- **recommended:** 

### ACS_OMEGA

- **package status:** OWNER_REVIEW_READY_FOR_OWNER_REVIEW
- **submission allowed:** False
- **journal submissions allowed:** False
- **recommended:** 

### ACTA_BIOTHEORETICA

- **package status:** OWNER_REVIEW_READY_FOR_OWNER_REVIEW
- **submission allowed:** False
- **journal submissions allowed:** False
- **recommended:** 

### PLOS_COMPUTATIONAL_BIOLOGY

- **package status:** OWNER_REVIEW_READY_FOR_OWNER_REVIEW
- **submission allowed:** False
- **journal submissions allowed:** False
- **recommended:** 

### GLOBAL_JOURNAL_OF_FLEXIBLE_SYSTEMS_MANAGEMENT

- **package status:** OWNER_REVIEW_READY_FOR_OWNER_REVIEW
- **submission allowed:** False
- **journal submissions allowed:** False
- **recommended:**
