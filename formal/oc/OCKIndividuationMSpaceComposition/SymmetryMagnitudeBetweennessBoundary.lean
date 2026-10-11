import OCKIndividuationMSpaceComposition.SymmetryDistinctionThreePointMagnitudeBoundary
import OCKIndividuationMSpaceComposition.SymmetryDistinctionDimensionBoundary

namespace OCKIndividuationMSpaceComposition

universe uCarrier

namespace PrimitiveDistinction

/-!
# A bounded magnitude does not determine betweenness

The three-point magnitude boundary supplies two finite Nat-valued magnitude
models on `Fin 3`.  The earlier dimension boundary supplies two strictness-level
relations on the same carrier.  This module combines those facts without
introducing an order, topology, path, completeness, continuum, or intrinsic
dimension.  It isolates the missing bridge: magnitude-like laws and minimal
strictness are compatible, but neither interface derives the other.
-/

/-- A deliberately weak joint model: a Nat magnitude satisfies its bounded
metric-like laws and a relation satisfies only the minimal strictness law.
No compatibility between numeric magnitude and betweenness is smuggled in. -/
def NatMagnitudeStrictBetweenModel {Point : Type uCarrier}
    (magnitude : Point → Point → Nat)
    (Between : Point → Point → Point → Prop) : Prop :=
  NatMagnitudeAxioms magnitude ∧ StrictBetweenLaw Between

theorem finThreeDiscreteMagnitude_witnessed_model :
    NatMagnitudeStrictBetweenModel finThreeDiscreteMagnitude
      finThreeWitnessedBetween := by
  exact ⟨finThreeDiscreteMagnitude_axioms, finThreeWitnessedBetween_strict⟩

theorem finThreeDiscreteMagnitude_empty_model :
    NatMagnitudeStrictBetweenModel finThreeDiscreteMagnitude
      finThreeEmptyBetween := by
  exact ⟨finThreeDiscreteMagnitude_axioms, finThreeEmptyBetween_strict⟩

/-- The same bounded magnitude on the same three-point carrier supports both a
witnessed and an empty strictness-level relation.  Therefore those magnitude
laws alone do not force a middle point, much less full geometric betweenness.
This is a countermodel to an implication, not a claim that either relation is
canonical. -/
theorem finThreeMagnitude_does_not_force_betweenness :
    NatMagnitudeStrictBetweenModel finThreeDiscreteMagnitude
        finThreeWitnessedBetween ∧
      NatMagnitudeStrictBetweenModel finThreeDiscreteMagnitude
        finThreeEmptyBetween ∧
      (∃ middle,
        finThreeWitnessedBetween finThreeEndpointDistinction.first middle
          finThreeEndpointDistinction.second) ∧
      ¬ (∃ middle,
        finThreeEmptyBetween finThreeEndpointDistinction.first middle
          finThreeEndpointDistinction.second) := by
  exact ⟨finThreeDiscreteMagnitude_witnessed_model,
    finThreeDiscreteMagnitude_empty_model,
    thirdPoint_does_not_determine_betweenness.1,
    thirdPoint_does_not_determine_betweenness.2⟩

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
