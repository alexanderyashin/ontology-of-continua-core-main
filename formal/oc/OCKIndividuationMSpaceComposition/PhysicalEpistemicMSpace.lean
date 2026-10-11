import Mathlib.Data.Fin.Basic
import Mathlib.Data.Set.Lattice
import Mathlib.Tactic.NormNum

namespace OCKIndividuationMSpaceComposition

/-!
# Physical versus optic-relative continuation spaces

The two spaces are represented separately even in the finite kernel.  The
module intentionally proves independence by explicit witnesses rather than
asserting a generic monotonicity law.
-/

def StrictSubset {State : Type*} (left right : Set State) : Prop :=
  left ⊆ right ∧ ∃ state, state ∈ right ∧ state ∉ left

structure ContinuationSnapshot (State : Type*) where
  physical : Set State
  epistemic : Set State

def snapshotZero : ContinuationSnapshot (Fin 2) :=
  { physical := ({0} : Set (Fin 2)), epistemic := Set.univ }

def snapshotOne : ContinuationSnapshot (Fin 2) :=
  { physical := Set.univ, epistemic := ({0} : Set (Fin 2)) }

/-- Physical possibility can expand while the current optic-relative
continuation set contracts.  Thus one generic expansion/contraction law for
both M-spaces is false. -/
theorem physical_expansion_epistemic_contraction_countermodel :
    StrictSubset snapshotZero.physical snapshotOne.physical ∧
      StrictSubset snapshotOne.epistemic snapshotZero.epistemic := by
  constructor
  · constructor
    · intro state _
      exact Set.mem_univ state
    · refine ⟨1, Set.mem_univ 1, ?_⟩
      simp [snapshotZero]
  · constructor
    · intro state _
      exact Set.mem_univ state
    · refine ⟨1, ?_, ?_⟩
      · exact Set.mem_univ 1
      · intro impossible
        simp [snapshotOne] at impossible

/-- A change in physical possibilities need not change the epistemic set when
the optic and evidence are unchanged. -/
theorem physical_contraction_epistemic_stasis_countermodel :
    ∃ (before after : ContinuationSnapshot (Fin 2)),
      StrictSubset after.physical before.physical ∧
        after.epistemic = before.epistemic := by
  let before : ContinuationSnapshot (Fin 2) :=
    { physical := Set.univ, epistemic := Set.univ }
  refine ⟨before, snapshotZero, ?_, ?_⟩
  · constructor
    · intro state stateIsZero
      exact Set.mem_univ state
    · refine ⟨1, Set.mem_univ 1, ?_⟩
      simp [snapshotZero]
  · rfl

end OCKIndividuationMSpaceComposition
