import OCKIndividuationMSpaceComposition.KMContextContinuationCoherence
import OCKIndividuationMSpaceComposition.EnterpriseDynamicsBridge

namespace OCKIndividuationMSpaceComposition

open OCMinimalObligationSpine
open scoped BigOperators

universe uLiftCarrier uLiftCandidate uRepairCandidate

/-!
# K/M-context continuation to enterprise-carrier support

The enterprise carrier is a domain projection of terminal states, not an
additional primitive identity and not a label manufactured by K/M rank.  Once
that projection is fixed, exact context/continuation coherence transports the
complete reachable carrier support across every tied K/M minimum.  This gives
sound exclusions and, for singleton support, a point prediction.

The support results adapt the conservative abstraction principle: an abstract
carrier support may overapproximate reachable concrete terminal states, but it
must never assign positive admissible mass to a formally excluded carrier.
-/

/-- A carrier is reachable for one K/M candidate when some admitted terminal
state in its bounded future has that fixed enterprise projection. -/
def KMContextContinuationInterpretation.carrierFutureAt
    {K : CurrentK}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    (interpretation : KMContextContinuationInterpretation liftSearch)
    (observeCarrier : interpretation.State → EnterpriseCarrier)
    (candidate : liftSearch.Candidate)
    (carrier : EnterpriseCarrier) : Prop :=
  ∃ target,
    interpretation.predictiveInterpretation.targetFutureAt candidate target ∧
    observeCarrier target = carrier

/-- Exact context/continuation coherence transports not only concrete target
states but also their fixed enterprise-carrier projection. -/
theorem context_coherence_carrierFuture_iff
    {K : CurrentK}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {interpretation : KMContextContinuationInterpretation liftSearch}
    {left right : liftSearch.Candidate}
    (coherence : ContextContinuationCoherence interpretation left right)
    (observeCarrier : interpretation.State → EnterpriseCarrier)
    (carrier : EnterpriseCarrier) :
    interpretation.carrierFutureAt observeCarrier left carrier ↔
      interpretation.carrierFutureAt observeCarrier right carrier := by
  constructor
  · rintro ⟨target, future, projection⟩
    exact ⟨target,
      (context_coherence_targetFuture_iff coherence target).mp future,
      projection⟩
  · rintro ⟨target, future, projection⟩
    exact ⟨target,
      (context_coherence_targetFuture_iff coherence target).mpr future,
      projection⟩

/-- Under the explicit v67 context/continuation contract, the entire
set-valued enterprise-carrier future is point-identified across the tied K/M
model class. -/
theorem km_context_continuation_coherence_implies_carrier_point_identified
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (interpretation : KMContextContinuationInterpretation liftSearch)
    (observeCarrier : interpretation.State → EnterpriseCarrier)
    (coherent : KMTiedContextContinuationCoherent resolution interpretation) :
    KMPointIdentified resolution
      (interpretation.carrierFutureAt observeCarrier) := by
  apply km_coherence_implies_point_identified
  intro candidate tied carrier
  exact context_coherence_carrierFuture_iff
    (coherent candidate tied) observeCarrier carrier

/-- The OC-derived carrier support is the support of the selected minimum
after the state-to-carrier projection has been fixed. -/
def KMDerivedEnterpriseCarrierSupport
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (interpretation : KMContextContinuationInterpretation liftSearch)
    (observeCarrier : interpretation.State → EnterpriseCarrier)
    (carrier : EnterpriseCarrier) : Prop :=
  interpretation.carrierFutureAt observeCarrier
    resolution.selection.minimizer.1 carrier

/-- Positive theorem: a selected-model exclusion is a universal exclusion
over every tied K/M minimum when context and continuation are coherent. -/
theorem km_context_coherence_excludes_carrier_for_all_tied_models
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (interpretation : KMContextContinuationInterpretation liftSearch)
    (observeCarrier : interpretation.State → EnterpriseCarrier)
    (coherent : KMTiedContextContinuationCoherent resolution interpretation)
    (carrier : EnterpriseCarrier)
    (excluded : ¬ KMDerivedEnterpriseCarrierSupport resolution interpretation
      observeCarrier carrier) :
    ¬ KMPossibleFuture resolution
      (interpretation.carrierFutureAt observeCarrier) carrier := by
  intro possible
  obtain ⟨candidate, tied, future⟩ := possible
  exact excluded ((context_coherence_carrierFuture_iff
    (coherent candidate tied) observeCarrier carrier).mp future)

/-- Positive theorem: a carrier reachable under the selected minimum is
necessary across the tied class under the same coherence contract. -/
theorem km_context_coherence_makes_selected_carrier_necessary
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (interpretation : KMContextContinuationInterpretation liftSearch)
    (observeCarrier : interpretation.State → EnterpriseCarrier)
    (coherent : KMTiedContextContinuationCoherent resolution interpretation)
    (carrier : EnterpriseCarrier)
    (selectedFuture : KMDerivedEnterpriseCarrierSupport resolution interpretation
      observeCarrier carrier) :
    KMNecessaryFuture resolution
      (interpretation.carrierFutureAt observeCarrier) carrier := by
  intro candidate tied
  exact (context_coherence_carrierFuture_iff
    (coherent candidate tied) observeCarrier carrier).mpr selectedFuture

/-- A numerical domain forecast is support-compatible only when every
formally excluded carrier has zero mass. -/
def EnterpriseCarrierMassSupportCompatible
    (allowed : EnterpriseCarrier → Prop)
    (mass : EnterpriseCarrier → Nat) : Prop :=
  ∀ carrier, ¬ allowed carrier → mass carrier = 0

/-- Any positive assigned mass certifies membership in the declared formal
support. -/
theorem positive_mass_requires_allowed_carrier
    (allowed : EnterpriseCarrier → Prop)
    (mass : EnterpriseCarrier → Nat)
    (compatible : EnterpriseCarrierMassSupportCompatible allowed mass)
    (carrier : EnterpriseCarrier)
    (positive : 0 < mass carrier) :
    allowed carrier := by
  by_contra excluded
  exact (Nat.ne_of_gt positive) (compatible carrier excluded)

/-- If formal support is a singleton, normalization and support compatibility
force all numerical mass onto that carrier. -/
theorem singleton_formal_support_forces_point_mass
    (allowed : EnterpriseCarrier → Prop)
    (mass : EnterpriseCarrier → Nat)
    (total : Nat)
    (selected : EnterpriseCarrier)
    (normalized : (∑ carrier, mass carrier) = total)
    (compatible : EnterpriseCarrierMassSupportCompatible allowed mass)
    (singleton : ∀ carrier, allowed carrier ↔ carrier = selected) :
    mass selected = total := by
  calc
    mass selected = ∑ carrier, mass carrier := by
      symm
      apply Finset.sum_eq_single selected
      · intro carrier _ different
        apply compatible carrier
        intro allowedCarrier
        exact different ((singleton carrier).mp allowedCarrier)
      · simp
    _ = total := normalized

/-- Exact integer numerators of the active v2 empirical comparator on common
denominator 56. -/
def enterpriseNextCarrierV2Mass : EnterpriseCarrier → Nat
  | .assetRevision => 1
  | .capabilityRealization => 2
  | .commitmentRisk => 1
  | .controlDecision => 5
  | .deploymentInstance => 1
  | .releaseSurface => 1
  | .scientificClaim => 44
  | .workItemRun => 1

theorem enterpriseNextCarrierV2Mass_normalized :
    (∑ carrier, enterpriseNextCarrierV2Mass carrier) = 56 := by
  decide

theorem enterpriseNextCarrierV2Mass_positive
    (carrier : EnterpriseCarrier) :
    0 < enterpriseNextCarrierV2Mass carrier := by
  cases carrier <;> decide

/-- Numerical consequence: because the active v2 comparator has full support,
it can be compatible with an OC-derived support only if OC excludes nothing.
Any nontrivial formal exclusion therefore forces a preregistered model-family
revision rather than retrospective relabeling of v2 as generative OC. -/
theorem v2_full_support_compatible_only_with_no_exclusions
    (allowed : EnterpriseCarrier → Prop)
    (compatible : EnterpriseCarrierMassSupportCompatible allowed
      enterpriseNextCarrierV2Mass) :
    ∀ carrier, allowed carrier := by
  intro carrier
  exact positive_mass_requires_allowed_carrier allowed
    enterpriseNextCarrierV2Mass compatible carrier
    (enterpriseNextCarrierV2Mass_positive carrier)

/-- No-go: even an exact terminal state does not determine an enterprise
carrier until the domain projection is fixed. -/
theorem exact_state_does_not_determine_enterprise_carrier_without_projection
    {State : Type} (state : State) :
    ∃ left right : State → EnterpriseCarrier, left state ≠ right state := by
  refine ⟨fun _ => .assetRevision, fun _ => .scientificClaim, ?_⟩
  simp

end OCKIndividuationMSpaceComposition
