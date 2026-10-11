import OCKIndividuationMSpaceComposition.SymmetryNativeCausalNaturalityBoundary

namespace OCKIndividuationMSpaceComposition

universe uMechanism uIntervention uOutcome

namespace NativeCausalWitnessNaturalityBoundary

open ActiveConstraintModel
open NativeCausalNaturalityBoundary

variable {Mechanism : Type uMechanism}
variable {Intervention : Type uIntervention}
variable {Outcome : Type uOutcome}

/-!
# Semantic witness naturality for the causal relation

`SymmetryNativeCausalNaturalityBoundary` supplied relation-level naturality
once `InternalDependency` preservation was explicit.  This slice gives a
smaller model-level interface for obtaining that premise from the actual OC
fields: carrier, intervention and outcome equivalences preserve `response`,
`responseWithout`, and `port`.  The essential-difference witness and the
internal-dependency relation are then transported by proof.

The Boolean boundary keeps the distinction honest: a carrier flip can preserve
the entire `InternalDependency` relation while changing `response`.  Therefore
relation naturality cannot be upgraded to model naturality without semantic
field-preservation premises.

No generated-kernel, action, rank, dimension, exchange, or continuum claim is
added here; generated-kernel transport remains the G4 result.
-/

structure CausalWitnessRelabeling
    (model : ActiveConstraintModel Mechanism Intervention Outcome) where
  mechanismEquiv : Mechanism ≃ Mechanism
  interventionEquiv : Intervention ≃ Intervention
  outcomeEquiv : Outcome ≃ Outcome
  response_transport : ∀ current intervention,
    model.response (mechanismEquiv current) (interventionEquiv intervention) =
      outcomeEquiv (model.response current intervention)
  responseWithout_transport : ∀ current support intervention,
    model.responseWithout (mechanismEquiv current) (mechanismEquiv support)
        (interventionEquiv intervention) =
      outcomeEquiv (model.responseWithout current support intervention)
  port_iff : ∀ current,
    model.port current ↔ model.port (mechanismEquiv current)

def CausalWitnessRelabeling.symm
    (relabeling : CausalWitnessRelabeling model) :
    CausalWitnessRelabeling model where
  mechanismEquiv := relabeling.mechanismEquiv.symm
  interventionEquiv := relabeling.interventionEquiv.symm
  outcomeEquiv := relabeling.outcomeEquiv.symm
  response_transport := by
    intro current intervention
    have h := relabeling.response_transport
      (relabeling.mechanismEquiv.symm current)
      (relabeling.interventionEquiv.symm intervention)
    have h' := congrArg relabeling.outcomeEquiv.symm h.symm
    simpa using h'
  responseWithout_transport := by
    intro current support intervention
    have h := relabeling.responseWithout_transport
      (relabeling.mechanismEquiv.symm current)
      (relabeling.mechanismEquiv.symm support)
      (relabeling.interventionEquiv.symm intervention)
    have h' := congrArg relabeling.outcomeEquiv.symm h.symm
    simpa using h'
  port_iff := by
    intro current
    simpa using
      (relabeling.port_iff (relabeling.mechanismEquiv.symm current)).symm

theorem essentialDependency_relabel
    (relabeling : CausalWitnessRelabeling model)
    {target support : Mechanism} :
    EssentialDependency model target support →
      EssentialDependency model (relabeling.mechanismEquiv target)
        (relabeling.mechanismEquiv support) := by
  rintro ⟨witness⟩
  refine ⟨{
    intervention := relabeling.interventionEquiv witness.intervention
    changes := ?_
  }⟩
  intro equality
  apply witness.changes
  apply relabeling.outcomeEquiv.injective
  calc
    relabeling.outcomeEquiv (model.response target witness.intervention) =
        model.response (relabeling.mechanismEquiv target)
          (relabeling.interventionEquiv witness.intervention) :=
      (relabeling.response_transport target witness.intervention).symm
    _ = model.responseWithout (relabeling.mechanismEquiv target)
          (relabeling.mechanismEquiv support)
          (relabeling.interventionEquiv witness.intervention) := equality
    _ = relabeling.outcomeEquiv
          (model.responseWithout target support witness.intervention) :=
      relabeling.responseWithout_transport target support witness.intervention

theorem essentialDependency_relabel_iff
    (relabeling : CausalWitnessRelabeling model)
    {target support : Mechanism} :
    EssentialDependency model target support ↔
      EssentialDependency model (relabeling.mechanismEquiv target)
        (relabeling.mechanismEquiv support) := by
  constructor
  · exact essentialDependency_relabel relabeling
  · intro mapped
    have back := essentialDependency_relabel (relabeling.symm)
      (target := relabeling.mechanismEquiv target)
      (support := relabeling.mechanismEquiv support) mapped
    simpa [CausalWitnessRelabeling.symm] using back

theorem internalDependency_relabel
    (relabeling : CausalWitnessRelabeling model)
    {current next : Mechanism} :
    InternalDependency model current next →
      InternalDependency model (relabeling.mechanismEquiv current)
        (relabeling.mechanismEquiv next) := by
  intro dependency
  refine ⟨?_, ?_⟩
  · intro mappedPort
    exact dependency.1 ((relabeling.port_iff next).mpr mappedPort)
  · rcases dependency.2 with left | right
    · exact Or.inl ((essentialDependency_relabel_iff relabeling).mp left)
    · exact Or.inr ((essentialDependency_relabel_iff relabeling).mp right)

theorem internalDependency_relabel_iff
    (relabeling : CausalWitnessRelabeling model)
    {current next : Mechanism} :
    InternalDependency model current next ↔
      InternalDependency model (relabeling.mechanismEquiv current)
        (relabeling.mechanismEquiv next) := by
  constructor
  · exact internalDependency_relabel relabeling
  · intro mapped
    have back := internalDependency_relabel (relabeling.symm)
      (current := relabeling.mechanismEquiv current)
      (next := relabeling.mechanismEquiv next)
    have original := back mapped
    simpa [CausalWitnessRelabeling.symm] using original

/-! ## Relation naturality alone is too weak -/

def responseBlindModel : ActiveConstraintModel Bool Unit Bool where
  response := fun current _ => current
  responseWithout := fun current _ _ => !current
  port := fun _ => False

theorem responseBlindModel_internalDependency_all
    (current next : Bool) :
    InternalDependency responseBlindModel current next := by
  refine ⟨by simp [responseBlindModel], Or.inl ?_⟩
  exact ⟨{
    intervention := (),
    changes := by
      intro equality
      cases current <;> simp [responseBlindModel] at equality
  }⟩

theorem responseBlindModel_relation_flip_invariant :
    ∀ current next,
      InternalDependency responseBlindModel current next ↔
        InternalDependency responseBlindModel (boolFlip current)
          (boolFlip next) := by
  intro current next
  constructor
  · intro _
    exact responseBlindModel_internalDependency_all _ _
  · intro _
    exact responseBlindModel_internalDependency_all _ _

theorem relation_naturality_does_not_force_response_naturality :
    (∀ current next,
      InternalDependency responseBlindModel current next ↔
        InternalDependency responseBlindModel (boolFlip current)
          (boolFlip next)) ∧
    ¬ (∀ current intervention,
      responseBlindModel.response (boolFlip current) intervention =
        responseBlindModel.response current intervention) := by
  refine ⟨responseBlindModel_relation_flip_invariant, ?_⟩
  intro responsePreserved
  have mismatch := responsePreserved false ()
  simpa [responseBlindModel] using mismatch

end NativeCausalWitnessNaturalityBoundary

end OCKIndividuationMSpaceComposition
