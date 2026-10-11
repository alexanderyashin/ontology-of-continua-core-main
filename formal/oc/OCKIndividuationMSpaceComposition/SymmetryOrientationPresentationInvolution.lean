import OCKIndividuationMSpaceComposition.SymmetryCanonicalFiniteRankOrientationInvariant

namespace OCKIndividuationMSpaceComposition

universe uIndex uCarrier

namespace PrimitiveDistinction

/-!
# The involution of orientation presentations

An ordered endpoint pair is a presentation of an unordered primitive
distinction.  The preceding orientation-invariance layer showed that swapping
the displayed endpoints leaves the generated permutation and finite Boolean
action unchanged.  This layer records the algebraic fact that the presentation
operation itself is an involution, both for one distinction and pointwise for a
finite family.

This is intentionally weaker than a global torsor claim: it concerns only the
redundancy of the ordered presentation and derives no new carrier points,
transitivity, or global dimension.
-/

theorem reverseLabels_involutive {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    distinction.reverseLabels.reverseLabels = distinction := by
  cases distinction
  rfl

namespace DisjointDistinctionFamily

variable {Index : Type uIndex} {Carrier : Type uCarrier}
variable [Fintype Index] [DecidableEq Index]
variable [Fintype Carrier] [DecidableEq Carrier]

/-- Applying the family presentation reversal twice restores every displayed
primitive distinction. -/
theorem reverseLabelsFamily_twice_distinction
    (family : DisjointDistinctionFamily Index Carrier) (index : Index) :
    (reverseLabelsFamily (reverseLabelsFamily family)).distinction index =
      family.distinction index := by
  simpa [reverseLabelsFamily] using
    (PrimitiveDistinction.reverseLabels_involutive (family.distinction index))

/-- Double reversal leaves the actual mask action unchanged. -/
theorem reverseLabelsFamily_twice_maskPermutation
    (family : DisjointDistinctionFamily Index Carrier) (mask : Index -> Bool) :
    (reverseLabelsFamily (reverseLabelsFamily family)).maskPermutation mask =
      family.maskPermutation mask := by
  calc
    (reverseLabelsFamily (reverseLabelsFamily family)).maskPermutation mask =
        (reverseLabelsFamily family).maskPermutation mask :=
      reverseLabelsFamily_maskPermutation (reverseLabelsFamily family) mask
    _ = family.maskPermutation mask :=
      reverseLabelsFamily_maskPermutation family mask

/-- Double reversal leaves the factorized product action unchanged. -/
theorem reverseLabelsFamily_twice_maskPermutationProduct
    (family : DisjointDistinctionFamily Index Carrier) (mask : Index -> Bool) :
    (reverseLabelsFamily (reverseLabelsFamily family)).maskPermutationProduct mask =
      family.maskPermutationProduct mask := by
  calc
    (reverseLabelsFamily (reverseLabelsFamily family)).maskPermutationProduct mask =
        (reverseLabelsFamily family).maskPermutationProduct mask :=
      reverseLabelsFamily_maskPermutationProduct (reverseLabelsFamily family) mask
    _ = family.maskPermutationProduct mask :=
      reverseLabelsFamily_maskPermutationProduct family mask

end DisjointDistinctionFamily

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
