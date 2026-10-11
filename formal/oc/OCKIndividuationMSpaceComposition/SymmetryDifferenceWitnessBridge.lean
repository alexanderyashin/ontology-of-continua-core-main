import OCKIndividuationMSpaceComposition.ConstraintGeneratedObject
import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinction

namespace OCKIndividuationMSpaceComposition

universe uMechanism uIntervention uOutcome

/-!
# From an intervention difference witness to a local symmetry axis

`DifferenceWitness` is an existing OC causal object: removing a support changes
the response of a target under a typed intervention.  Its only mathematical
content about outcomes is an inequality.  This module proves that the two
unequal outcomes generate the same canonical local two-side axis as every
primitive distinction.

The result is deliberately local.  It does not turn the intervention, target,
support or complete outcome space into a symmetric mechanism.  A global free
outcome swap follows only when the two witnessed outcomes exhaust the outcome
carrier, or when the separately proved complement-pairing premise is supplied.
-/

namespace DifferenceWitness

/-- The actual/removal-response inequality as a relation-level primitive
distinction.  The relation is plain inequality and contains no operation. -/
def toIrreflexiveDistinctionWitness
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {target support : Mechanism}
    (witness : DifferenceWitness model target support) :
    IrreflexiveDistinctionWitness Outcome where
  relation := (· ≠ ·)
  irreflexive := fun _ selfNe => selfNe rfl
  first := model.response target witness.intervention
  second := model.responseWithout target support witness.intervention
  witnessed := witness.changes

/-- Forget causal provenance only after extracting the exact outcome
distinction.  The original `DifferenceWitness` remains the provenance source. -/
def toPrimitiveDistinction
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {target support : Mechanism}
    (witness : DifferenceWitness model target support) :
    PrimitiveDistinction Outcome :=
  witness.toIrreflexiveDistinctionWitness.toPrimitiveDistinction

@[simp] theorem toPrimitiveDistinction_first
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {target support : Mechanism}
    (witness : DifferenceWitness model target support) :
    witness.toPrimitiveDistinction.first =
      model.response target witness.intervention := by
  rfl

@[simp] theorem toPrimitiveDistinction_second
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {target support : Mechanism}
    (witness : DifferenceWitness model target support) :
    witness.toPrimitiveDistinction.second =
      model.responseWithout target support witness.intervention := by
  rfl

/-- The generated outcome axis is exactly the actual and removal responses. -/
abbrev OutcomeAxis
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {target support : Mechanism}
    (witness : DifferenceWitness model target support) :=
  witness.toPrimitiveDistinction.Axis

/-- The response difference derives a fixed-point-free involution on its
two-outcome axis; none is present in `DifferenceWitness`. -/
noncomputable def toLocalFixedPointFreeInvolution
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {target support : Mechanism}
    (witness : DifferenceWitness model target support) :
    FixedPointFreeInvolution witness.OutcomeAxis :=
  witness.toPrimitiveDistinction.toFixedPointFreeInvolution

/-- The response difference derives a local two-point R3 torsor. -/
noncomputable def toLocalR3Torsor
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {target support : Mechanism}
    (witness : DifferenceWitness model target support) :
    R3C2OrientationTorsorInterface witness.OutcomeAxis Unit Unit :=
  witness.toPrimitiveDistinction.toR3Torsor

/-- The local admissible automorphism algebra is exactly C₂. -/
noncomputable def localAdmissibleAutomorphismsEquivBool
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {target support : Mechanism}
    (witness : DifferenceWitness model target support) :
    R3AdmissibleEndomorphism witness.toLocalR3Torsor ≃ Bool :=
  witness.toPrimitiveDistinction.generatedAdmissibleAutomorphismsEquivBool

/-- The derived local swap sends the actual response to the removal response. -/
theorem localSwap_actual
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {target support : Mechanism}
    (witness : DifferenceWitness model target support) :
    witness.toPrimitiveDistinction.axisSwap
        witness.toPrimitiveDistinction.axisFirst =
      witness.toPrimitiveDistinction.axisSecond := by
  simp

/-- And applying it again returns the actual response. -/
theorem localSwap_removal
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {target support : Mechanism}
    (witness : DifferenceWitness model target support) :
    witness.toPrimitiveDistinction.axisSwap
        witness.toPrimitiveDistinction.axisSecond =
      witness.toPrimitiveDistinction.axisFirst := by
  simp

/-- Choosing the actual response as base gives it negative polarity. -/
theorem generatedPolarity_actual
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {target support : Mechanism}
    (witness : DifferenceWitness model target support) :
    witness.toPrimitiveDistinction.generatedPolarity
        witness.toPrimitiveDistinction.axisFirst = false := by
  simp

/-- The removal response is the positive partner in that chosen coordinate. -/
theorem generatedPolarity_removal
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {target support : Mechanism}
    (witness : DifferenceWitness model target support) :
    witness.toPrimitiveDistinction.generatedPolarity
        witness.toPrimitiveDistinction.axisSecond = true := by
  simp

/-- Exact global boundary: the canonical ambient transposition generated by
this one causal difference is free on all outcomes iff those two outcomes
exhaust the outcome type. -/
theorem globalPairSwap_free_iff_outcomeCoverage
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {target support : Mechanism}
    (witness : DifferenceWitness model target support) :
    (∀ outcome : Outcome,
        witness.toPrimitiveDistinction.pairSwap outcome ≠ outcome) ↔
      witness.toPrimitiveDistinction.CoversCarrier :=
  witness.toPrimitiveDistinction.pairSwap_fixedPointFree_iff_coversCarrier

/-- A causal difference alone proves no global free action whenever a third
outcome lies outside the witnessed pair. -/
theorem thirdOutcome_blocks_canonical_globalFreeness
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {target support : Mechanism}
    (witness : DifferenceWitness model target support)
    (third : Outcome)
    (notActual : third ≠ witness.toPrimitiveDistinction.first)
    (notRemoval : third ≠ witness.toPrimitiveDistinction.second) :
    witness.toPrimitiveDistinction.pairSwap third = third :=
  witness.toPrimitiveDistinction.pairSwap_outside third notActual notRemoval

end DifferenceWitness

end OCKIndividuationMSpaceComposition
