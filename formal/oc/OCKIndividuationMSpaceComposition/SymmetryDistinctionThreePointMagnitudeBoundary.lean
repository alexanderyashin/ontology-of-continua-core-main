import OCKIndividuationMSpaceComposition.SymmetryDistinctionDimensionBoundary
import Mathlib.Data.Fin.Basic
import Mathlib.Data.Fintype.Basic
import Mathlib.Tactic.FinCases
import Mathlib.Tactic.NormNum

namespace OCKIndividuationMSpaceComposition

universe uCarrier

namespace PrimitiveDistinction

/-!
# Three-point magnitude is not fixed by a primitive pair

The two-point boundary module proves that a generated primitive axis has one
off-diagonal magnitude grade and no strict internal point.  This companion
adds the nearest quantitative boundary beyond that result.  On the same
three-point carrier, with the same primitive endpoint pair, two explicit
natural-valued magnitudes satisfy the same finite metric-like laws while
assigning different values to the endpoint pair.

The laws below are deliberately only a bounded magnitude interface: zero
diagonal, symmetry, separation, and the triangle inequality.  They do not
assume or define an order, betweenness, topology, path, completeness,
continuum, or intrinsic dimension.  The countermodel therefore shows that a
third carrier point is not enough to select a quantitative geometry.
-/

/-! ## A deliberately bounded magnitude interface -/

/-- The finite metric-like laws used by this countermodel.  This is not a
`MetricSpace` structure and carries no topology or interpolation operation. -/
def NatMagnitudeAxioms {Point : Type uCarrier}
    (magnitude : Point → Point → Nat) : Prop :=
  (∀ point, magnitude point point = 0) ∧
    (∀ left right, magnitude left right = magnitude right left) ∧
    (∀ left right, magnitude left right = 0 ↔ left = right) ∧
    (∀ left middle right,
      magnitude left right ≤ magnitude left middle + magnitude middle right)

/-! ## Two explicit magnitudes on the same three-point carrier -/

/-- The discrete magnitude: every distinct pair has the same grade. -/
def finThreeDiscreteMagnitude (left right : Fin 3) : Nat :=
  if left = right then 0 else 1

/-- A path-shaped magnitude on the same carrier: the distinguished endpoints
have grade two, while each adjacent pair has grade one. -/
def finThreeEndpointLongMagnitude (left right : Fin 3) : Nat :=
  if left = right then 0
  else if (left = 0 ∧ right = 2) ∨ (left = 2 ∧ right = 0) then 2
  else 1

/-! ## Independent law checks -/

theorem finThreeDiscreteMagnitude_self (point : Fin 3) :
    finThreeDiscreteMagnitude point point = 0 := by
  simp [finThreeDiscreteMagnitude]

theorem finThreeDiscreteMagnitude_symmetric (left right : Fin 3) :
    finThreeDiscreteMagnitude left right =
      finThreeDiscreteMagnitude right left := by
  by_cases same : left = right
  · subst right
    simp [finThreeDiscreteMagnitude]
  · have reverseDifferent : right ≠ left := Ne.symm same
    simp [finThreeDiscreteMagnitude, same, reverseDifferent]

theorem finThreeDiscreteMagnitude_separates (left right : Fin 3) :
    finThreeDiscreteMagnitude left right = 0 ↔ left = right := by
  simp [finThreeDiscreteMagnitude]

theorem finThreeDiscreteMagnitude_triangle (left middle right : Fin 3) :
    finThreeDiscreteMagnitude left right ≤
      finThreeDiscreteMagnitude left middle +
        finThreeDiscreteMagnitude middle right := by
  fin_cases left <;> fin_cases middle <;> fin_cases right <;>
    norm_num [finThreeDiscreteMagnitude]

theorem finThreeDiscreteMagnitude_axioms :
    NatMagnitudeAxioms finThreeDiscreteMagnitude := by
  refine ⟨?_, ?_, ?_, ?_⟩
  · exact finThreeDiscreteMagnitude_self
  · exact finThreeDiscreteMagnitude_symmetric
  · exact finThreeDiscreteMagnitude_separates
  · exact finThreeDiscreteMagnitude_triangle

theorem finThreeEndpointLongMagnitude_self (point : Fin 3) :
    finThreeEndpointLongMagnitude point point = 0 := by
  simp [finThreeEndpointLongMagnitude]

theorem finThreeEndpointLongMagnitude_symmetric (left right : Fin 3) :
    finThreeEndpointLongMagnitude left right =
      finThreeEndpointLongMagnitude right left := by
  fin_cases left <;> fin_cases right <;> decide

theorem finThreeEndpointLongMagnitude_separates (left right : Fin 3) :
    finThreeEndpointLongMagnitude left right = 0 ↔ left = right := by
  fin_cases left <;> fin_cases right <;> decide

theorem finThreeEndpointLongMagnitude_triangle (left middle right : Fin 3) :
    finThreeEndpointLongMagnitude left right ≤
      finThreeEndpointLongMagnitude left middle +
        finThreeEndpointLongMagnitude middle right := by
  fin_cases left <;> fin_cases middle <;> fin_cases right <;> decide

theorem finThreeEndpointLongMagnitude_axioms :
    NatMagnitudeAxioms finThreeEndpointLongMagnitude := by
  refine ⟨?_, ?_, ?_, ?_⟩
  · exact finThreeEndpointLongMagnitude_self
  · exact finThreeEndpointLongMagnitude_symmetric
  · exact finThreeEndpointLongMagnitude_separates
  · exact finThreeEndpointLongMagnitude_triangle

/-! ## The quantitative non-uniqueness boundary -/

/-- The same primitive endpoints receive different grades in the two valid
three-point magnitudes.  The first value is the discrete normalization; the
second is the length-two path normalization. -/
theorem finThreeEndpointMagnitude_values :
    finThreeDiscreteMagnitude finThreeEndpointDistinction.first
        finThreeEndpointDistinction.second = 1 ∧
      finThreeEndpointLongMagnitude finThreeEndpointDistinction.first
        finThreeEndpointDistinction.second = 2 := by
  norm_num [finThreeEndpointDistinction, finThreeDiscreteMagnitude,
    finThreeEndpointLongMagnitude, Fin.ext_iff]

/-- A primitive endpoint pair plus a third carrier point does not determine a
unique symmetric, separating, triangular numeric magnitude.  This is an
explicit countermodel, not a claim that either normalization is canonical on
an arbitrary carrier. -/
theorem thirdPoint_does_not_determine_magnitude_scale :
    finThreeEndpointDistinction.first ≠ finThreeEndpointDistinction.second ∧
      NatMagnitudeAxioms finThreeDiscreteMagnitude ∧
      NatMagnitudeAxioms finThreeEndpointLongMagnitude ∧
      finThreeDiscreteMagnitude finThreeEndpointDistinction.first
          finThreeEndpointDistinction.second ≠
        finThreeEndpointLongMagnitude finThreeEndpointDistinction.first
          finThreeEndpointDistinction.second := by
  refine ⟨finThreeEndpointDistinction.separated,
    finThreeDiscreteMagnitude_axioms, finThreeEndpointLongMagnitude_axioms,
    ?_⟩
  norm_num [finThreeEndpointDistinction, finThreeDiscreteMagnitude,
    finThreeEndpointLongMagnitude, Fin.ext_iff]

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
