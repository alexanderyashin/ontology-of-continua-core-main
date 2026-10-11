import OCKIndividuationMSpaceComposition.KAxisAndCurrentKBridge

namespace OCKIndividuationMSpaceComposition

universe uState

/-!
# Parameterised cardinality of context-derived K levels

K levels are SCC classes of a declared, sound resolution relation.  This
module supplies the missing constructive cardinality result: every finite
count is realised by a typed scientific context.  Thus a count is neither a
primitive ontological constant nor a matter of taste: for a finite domain it
is the cardinality of the derived quotient, to be certified by an exact atlas.
-/

/-- A minimal finite K-resolution context with one candidate per K level. -/
def discreteKResolutionContext (n : Nat) : KResolutionContext (Fin n) where
  Candidate := Fin n
  profile := fun _ left right => left ≠ right
  ResolutionStep := fun source target => source = target
  resolutionStep_sound := by
    intro source target same
    subst target
    exact atLeastAsDiscriminating_refl _

/-- Equality-only resolution has no hidden multi-candidate reachability. -/
theorem equality_resolution_reachable_iff
    {State : Type uState} {first second : State} :
    RelationReachable (fun source target : State => source = target) first second ↔
      first = second := by
  constructor
  · intro reachable
    induction reachable with
    | root => rfl
    | tail previous edge inductionHypothesis =>
        exact inductionHypothesis.trans edge
  · intro same
    subst second
    exact .root

/-- The derived K-level quotient of the discrete context is exactly `Fin n`. -/
def discreteKDerivedLevelEquiv (n : Nat) :
    (discreteKResolutionContext n).ContextDerivedKLevel ≃ Fin n where
  toFun := Quotient.lift id (by
    intro first second sameLevel
    exact equality_resolution_reachable_iff.mp sameLevel.1)
  invFun := fun candidate =>
    (discreteKResolutionContext n).contextDerivedKLevel candidate
  left_inv := by
    intro level
    refine Quotient.inductionOn level ?_
    intro candidate
    rfl
  right_inv := by
    intro candidate
    rfl

/--
For every finite `n`, a sound K-resolution context with exactly `n` derived
K levels exists.  A proposed universal fixed K count therefore requires extra
domain evidence beyond the generic OC mechanics.
-/
theorem every_finite_k_level_count_is_realisable (n : Nat) :
    Nonempty ((discreteKResolutionContext n).ContextDerivedKLevel ≃ Fin n) :=
  ⟨discreteKDerivedLevelEquiv n⟩

/-- The identity atlas is exact for the `n`-level discrete context. -/
theorem discrete_k_level_identity_atlas_exact (n : Nat) :
    AtlasExact (discreteKResolutionContext n).ResolutionStep (fun i : Fin n => i) := by
  constructor
  · intro first second sameLevel
    exact equality_resolution_reachable_iff.mp (Quotient.exact sameLevel).1
  · intro level
    refine Quotient.inductionOn level ?_
    intro candidate
    exact ⟨candidate, rfl⟩

/--
No additional axis is silently identified with K resolution: changing the
resolution relation is exactly what can change the level quotient.
-/
theorem discrete_k_level_count_is_axis_relative (n : Nat) :
    ∃ context : KResolutionContext.{0, 0} (Fin n),
      Nonempty (context.ContextDerivedKLevel ≃ Fin n) :=
  ⟨discreteKResolutionContext n, every_finite_k_level_count_is_realisable n⟩

end OCKIndividuationMSpaceComposition
