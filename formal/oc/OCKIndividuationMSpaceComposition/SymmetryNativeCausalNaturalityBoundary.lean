import OCKIndividuationMSpaceComposition.SymmetryNativeCausalFamilyClosure
import Mathlib.Data.Bool.Basic

namespace OCKIndividuationMSpaceComposition

universe uMechanism uIntervention uOutcome

namespace NativeCausalNaturalityBoundary

open ActiveConstraintModel

variable {Mechanism : Type uMechanism}
variable {Intervention : Type uIntervention}
variable {Outcome : Type uOutcome}

/-!
# Causal naturality under a structure-preserving carrier relabeling

The existing causal kernel is generated from `InternalDependency`.  This
slice supplies the smallest symmetry interface needed to transport that
kernel: an equivalence of mechanism carriers together with an explicit iff
preserving `InternalDependency`.  The transport theorem is derived by
induction on `GeneratedKernel`; the correspondence is not baked into the
definition of generation.

The boundary is equally important.  An arbitrary carrier equivalence need not
preserve `InternalDependency`, so no causal naturality follows from a bare
relabeling.  A concrete Boolean model with one declared port witnesses this
failure.  No action, rank, dimension, exchange, or continuum structure is
introduced.
-/

structure CausalRelabeling
    (model : ActiveConstraintModel Mechanism Intervention Outcome) where
  equiv : Mechanism ≃ Mechanism
  dependency_iff : ∀ current next,
    InternalDependency model current next ↔
      InternalDependency model (equiv current) (equiv next)

def CausalRelabeling.symm
    (relabeling : CausalRelabeling model) : CausalRelabeling model where
  equiv := relabeling.equiv.symm
  dependency_iff := by
    intro current next
    simpa using
      (relabeling.dependency_iff (relabeling.equiv.symm current)
        (relabeling.equiv.symm next)).symm

theorem generatedKernel_relabel
    (relabeling : CausalRelabeling model)
    {root target : Mechanism} :
    GeneratedKernel model root target →
      GeneratedKernel model (relabeling.equiv root)
        (relabeling.equiv target) := by
  intro generated
  induction generated with
  | ofRoot => exact .ofRoot
  | @ofInternalDependency current next previous dependency inductionHypothesis =>
      exact .ofInternalDependency inductionHypothesis
        ((relabeling.dependency_iff current next).mp dependency)

theorem generatedKernel_relabel_iff
    (relabeling : CausalRelabeling model)
    {root target : Mechanism} :
    GeneratedKernel model root target ↔
      GeneratedKernel model (relabeling.equiv root)
        (relabeling.equiv target) := by
  constructor
  · exact generatedKernel_relabel relabeling
  · intro generated
    have back :=
      generatedKernel_relabel (relabeling.symm)
        (root := relabeling.equiv root) (target := relabeling.equiv target)
        generated
    simpa [CausalRelabeling.symm] using back

theorem familyGenerated_relabel_iff
    (relabeling : CausalRelabeling model)
    {seed : Set Mechanism} {target : Mechanism} :
    familyGenerated model seed target ↔
      familyGenerated model (relabeling.equiv '' seed)
        (relabeling.equiv target) := by
  constructor
  · rintro ⟨root, rootMember, generated⟩
    refine ⟨relabeling.equiv root, ?_,
      (generatedKernel_relabel relabeling generated)⟩
    exact ⟨root, rootMember, rfl⟩
  · rintro ⟨mappedRoot, mappedMember, generated⟩
    rcases mappedMember with ⟨root, rootMember, rootEq⟩
    subst mappedRoot
    refine ⟨root, rootMember, ?_⟩
    apply (generatedKernel_relabel_iff relabeling).mpr
    simpa using generated

theorem familyGenerated_relabel_root
    (relabeling : CausalRelabeling model)
    (root target : Mechanism) :
    familyGenerated model ({root} : Set Mechanism) target ↔
      familyGenerated model ({relabeling.equiv root} : Set Mechanism)
        (relabeling.equiv target) := by
  simpa using (familyGenerated_relabel_iff relabeling
    (seed := ({root} : Set Mechanism)) (target := target))

/-! ## A concrete boundary for a bare carrier equivalence -/

def boundaryModel : ActiveConstraintModel Bool Unit Bool where
  response := fun current _ => current
  responseWithout := fun current support _ =>
    if support = true then !current else current
  port := fun mechanism => mechanism = true

def boolFlip : Bool ≃ Bool where
  toFun := fun value => !value
  invFun := fun value => !value
  left_inv := by intro value; cases value <;> rfl
  right_inv := by intro value; cases value <;> rfl

@[simp] theorem boolFlip_false : boolFlip false = true := rfl

@[simp] theorem boolFlip_true : boolFlip true = false := rfl

theorem boundaryModel_not_dependency_preserving_under_flip :
    ¬ (∀ current next,
      InternalDependency boundaryModel current next ↔
        InternalDependency boundaryModel (boolFlip current)
          (boolFlip next)) := by
  intro preserves
  have mismatch := preserves false true
  have reverse : InternalDependency boundaryModel
      (boolFlip false) (boolFlip true) := by
    rw [boolFlip_false, boolFlip_true]
    refine ⟨by simp [boundaryModel], Or.inr ?_⟩
    exact ⟨{
      intervention := (),
      changes := by simp [boundaryModel]
    }⟩
  have forward := mismatch.mpr reverse
  simpa [InternalDependency, boundaryModel] using forward

end NativeCausalNaturalityBoundary

end OCKIndividuationMSpaceComposition
