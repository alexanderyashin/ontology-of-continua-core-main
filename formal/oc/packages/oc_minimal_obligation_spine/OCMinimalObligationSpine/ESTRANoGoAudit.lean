import Init

namespace OCMinimalObligationSpine

/-!
FORMAL_COUNTERMODEL_AUDIT_OF_EXISTING_ESTRA_DRAFT

This file audits only the literal, overstrong readings of existing ESTRA
draft claims.  It does not introduce a new No-Go family and it does not refute
any repaired theorem that adds the missing faithfulness, nondegeneracy,
topological, or coupling assumptions.

Audited sources:

* `archive/legacy_open_repo/preprints/
  jphq_06_structural_tension_nonoptimizable/sections/
  04_impossibility_theorems.tex`
* `archive/legacy_open_repo/preprints/
  jphq_08_limits_of_intervention/sections/
  03_definition_intervention_operator.tex`
* `archive/legacy_open_repo/preprints/
  jphq_08_limits_of_intervention/sections/04_limit_theorems.tex`
* `archive/legacy_open_repo/preprints/
  jphq_08_limits_of_intervention/sections/05_proof_sketches.tex`

The first countermodel shows that bare existence of a scalar objective or an
order cannot be denied without a semantic representation condition.  The
second countermodel instantiates exactly the stated intervention predicates on
a finite carrier and shows that they do not imply the advertised disjunction.
-/

def estraNoGoAuditClassification : String :=
  "FORMAL_COUNTERMODEL_AUDIT_OF_EXISTING_ESTRA_DRAFT"

universe u

/-! ## JPHQ06: literal objective/order non-existence is too strong -/

/-- A scalar function exists on every carrier, independently of its structure. -/
def constantScalarObjective (A : Type u) : A -> Int := fun _ => 0

theorem constantScalarObjective_exists (A : Type u) :
    Nonempty (A -> Int) :=
  ⟨constantScalarObjective A⟩

/-- The missing nondegeneracy condition: some two states receive distinct values. -/
def ObjectiveNondegenerate {A : Type u} (objective : A -> Int) : Prop :=
  Exists fun left => Exists fun right => Not (objective left = objective right)

/-- The constant witness is deliberately not a faithful/nondegenerate objective. -/
theorem constantScalarObjective_not_nondegenerate (A : Type u) :
    Not (ObjectiveNondegenerate (constantScalarObjective A)) := by
  intro h
  rcases h with ⟨left, right, valuesDiffer⟩
  exact valuesDiffer rfl

/-- Minimal data for a total preorder; antisymmetry is intentionally absent. -/
structure TotalPreorderWitness (A : Type u) where
  rel : A -> A -> Prop
  refl : forall value, rel value value
  trans : forall {left middle right},
    rel left middle -> rel middle right -> rel left right
  total : forall left right, rel left right ∨ rel right left

/-- The indiscriminate relation is a total preorder on every carrier. -/
def trivialTotalPreorder (A : Type u) : TotalPreorderWitness A where
  rel := fun _ _ => True
  refl := fun _ => True.intro
  trans := fun _ _ => True.intro
  total := fun _ _ => Or.inl True.intro

theorem totalPreorder_exists_without_tension_semantics (A : Type u) :
    Nonempty (TotalPreorderWitness A) :=
  ⟨trivialTotalPreorder A⟩

/-- Minimal data for a partial order. -/
structure PartialOrderWitness (A : Type u) where
  rel : A -> A -> Prop
  refl : forall value, rel value value
  trans : forall {left middle right},
    rel left middle -> rel middle right -> rel left right
  antisymm : forall {left right}, rel left right -> rel right left -> left = right

/-- Equality supplies a partial order without any threshold or phase primitive. -/
def equalityPartialOrder (A : Type u) : PartialOrderWitness A where
  rel := Eq
  refl := fun _ => rfl
  trans := fun leftMiddle middleRight => Eq.trans leftMiddle middleRight
  antisymm := fun leftRight _ => leftRight

theorem partialOrder_exists_without_tension_semantics (A : Type u) :
    Nonempty (PartialOrderWitness A) :=
  ⟨equalityPartialOrder A⟩

/-! ## JPHQ08: the stated predicates do not imply the No-Free disjunction -/

namespace JPHQ08LiteralAudit

/-- A finite two-state admissible carrier. -/
abbrev State := Bool

/-- Both states satisfy the threshold. -/
def theta (_ : State) : Int := 0

/-- A nonempty, proper boundary predicate on the admissible carrier. -/
def boundary (state : State) : Prop := state = true

/-- A full-domain, constant, therefore non-bijective intervention. -/
def constantIntervention (_ : State) : State := false

/-- Constant observables expose the missing coupling assumptions. -/
def continuity (_ : State) : Int := 0
def phase (_ : State) : Bool := false

def InjectiveMap {A B : Type u} (f : A -> B) : Prop :=
  forall ⦃left right⦄, f left = f right -> left = right

def SurjectiveMap {A B : Type u} (f : A -> B) : Prop :=
  forall target, Exists fun source => f source = target

def BijectiveMap {A B : Type u} (f : A -> B) : Prop :=
  InjectiveMap f ∧ SurjectiveMap f

/-- For a bijection this is equivalent to invariance of the boundary set. -/
def BoundaryInvariant (f : State -> State) : Prop :=
  forall state, boundary (f state) ↔ boundary state

/--
Literal formalization of "acts across" for a full-domain intervention: no
boundary-preserving automorphism can restrict to the intervention.
-/
def ActsAcrossBoundary (intervention : State -> State) : Prop :=
  Not (Exists fun extension : State -> State =>
    BijectiveMap extension ∧
    BoundaryInvariant extension ∧
    forall state, extension state = intervention state)

def ThetaPreserving (intervention : State -> State) : Prop :=
  forall state, theta state <= 0 -> theta (intervention state) <= 0

def ContinuityNondecreasing (intervention : State -> State) : Prop :=
  forall state, continuity state <= continuity (intervention state)

def PhasePreserving (intervention : State -> State) : Prop :=
  forall state, phase (intervention state) = phase state

theorem boundary_is_nonempty_and_proper :
    boundary true ∧ Not (boundary false) := by
  simp [boundary]

theorem constantIntervention_not_injective :
    Not (InjectiveMap constantIntervention) := by
  intro injective
  have impossible : false = true := injective (left := false) (right := true) rfl
  cases impossible

theorem constantIntervention_acts_across :
    ActsAcrossBoundary constantIntervention := by
  intro extensionExists
  rcases extensionExists with ⟨extension, bijective, _, agrees⟩
  have imagesEqual : extension false = extension true := by
    rw [agrees false, agrees true]
    rfl
  have impossible : false = true := bijective.1 imagesEqual
  cases impossible

theorem constantIntervention_theta_preserving :
    ThetaPreserving constantIntervention := by
  simp [ThetaPreserving, theta]

theorem constantIntervention_continuity_nondecreasing :
    ContinuityNondecreasing constantIntervention := by
  simp [ContinuityNondecreasing, continuity]

theorem constantIntervention_phase_preserving :
    PhasePreserving constantIntervention := by
  intro _
  rfl

/--
Finite countermodel to the literal JPHQ08 No-Free implication: the intervention
acts across the declared boundary, preserves thresholds, never decreases the
constant continuity observable, and preserves the constant phase observable.
-/
theorem finite_constant_intervention_countermodel :
    boundary true ∧
    Not (boundary false) ∧
    ActsAcrossBoundary constantIntervention ∧
    ThetaPreserving constantIntervention ∧
    ContinuityNondecreasing constantIntervention ∧
    PhasePreserving constantIntervention := by
  exact ⟨
    rfl,
    by simp [boundary],
    constantIntervention_acts_across,
    constantIntervention_theta_preserving,
    constantIntervention_continuity_nondecreasing,
    constantIntervention_phase_preserving
  ⟩

end JPHQ08LiteralAudit

/-!
Audit limits:

* The JPHQ06 witnesses establish existence only; they do not represent
  structural tension faithfully and do not make it scientifically optimizable.
* The JPHQ08 carrier is finite and the boundary predicate is supplied exactly
  as the draft definition permits.  No topology connects that predicate to
  `theta`, and no axiom connects either observable to boundary crossing.
* Consequently the countermodel targets only the implication from the written
  definitions.  A repaired theorem may exclude it by adding explicit topology,
  local geometry, nonconstant/faithful observables, or coupling axioms.
* No empirical, physical, domain, novelty, or canonical-release claim is made.
-/

end OCMinimalObligationSpine
