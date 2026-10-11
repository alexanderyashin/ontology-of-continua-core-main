import OCKIndividuationMSpaceComposition.SymmetryIntrinsicFinitaryRank

namespace OCKIndividuationMSpaceComposition

universe uToken

namespace IntrinsicFinitaryRank

variable {Token : Type uToken} [DecidableEq Token]

/-!
# Closure naturality under admissible relabeling

The finite rank theorem already proves that a closure-preserving relabeling
does not change relative rank.  This companion result exposes the stronger
object-level statement: the entire finite closure is transported to the
closure of the transported seed.  Thus symmetry acts on the dependence
structure before rank is measured; rank invariance is a consequence rather
than the only retained fact.
-/

namespace FinitaryDistinctionClosure.Relabeling

/-- A closure-preserving relabeling commutes with finite closure. -/
theorem close_image_eq_image_close
    {closure : FinitaryDistinctionClosure Token}
    (relabeling : closure.Relabeling)
    (seed : Finset Token) :
    closure.close (seed.image relabeling.relabel) =
      (closure.close seed).image relabeling.relabel := by
  classical
  ext mapped
  constructor
  · intro mappedMember
    let original := relabeling.relabel.symm mapped
    have mapsBack : relabeling.relabel original = mapped := by
      exact relabeling.relabel.apply_symm_apply mapped
    have originalMember : original ∈ closure.close seed := by
      apply (relabeling.preserves_generatedness seed original).mp
      rw [mapsBack]
      exact mappedMember
    exact Finset.mem_image.mpr ⟨original, originalMember, mapsBack⟩
  · intro mappedMember
    rcases Finset.mem_image.mp mappedMember with
      ⟨original, originalMember, rfl⟩
    exact (relabeling.preserves_generatedness seed original).mpr originalMember

/-- Membership in the closure is equivariant pointwise under relabeling. -/
theorem mem_close_image_iff
    {closure : FinitaryDistinctionClosure Token}
    (relabeling : closure.Relabeling)
    (seed : Finset Token) (token : Token) :
    relabeling.relabel token ∈ closure.close (seed.image relabeling.relabel) ↔
      token ∈ closure.close seed :=
  relabeling.preserves_generatedness seed token

end FinitaryDistinctionClosure.Relabeling

end IntrinsicFinitaryRank

end OCKIndividuationMSpaceComposition
