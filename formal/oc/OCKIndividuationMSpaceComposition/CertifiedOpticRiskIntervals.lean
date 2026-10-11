import OCKIndividuationMSpaceComposition.FiniteParetoOpticSelector

namespace OCKIndividuationMSpaceComposition

universe uOptic

/-!
# Certified lower/upper risk intervals for optic adjudication

Upper certificates are sufficient to show that one fitted optic works; lower
certificates are necessary to show that another information class cannot do
better.  Keeping the two surfaces separate yields a sound dominance rule:
`upper i < lower j`.  Overlap intentionally produces no strict conclusion.
-/

/-- A coherent scientific risk interval for one registered optic. -/
structure CertifiedRiskInterval where
  lower : ℝ
  upper : ℝ
  coherent : lower ≤ upper

/-- `new` tightens `old` when it raises the certified lower endpoint and
lowers the certified upper endpoint. -/
def CertifiedRiskInterval.Tightens
    (old new : CertifiedRiskInterval) : Prop :=
  old.lower ≤ new.lower ∧ new.upper ≤ old.upper

/-- Strict certified dominance: every risk admitted by `left` is lower than
every risk admitted by `right`. -/
def CertifiedOpticDominates
    {Optic : Type uOptic}
    (interval : Optic → CertifiedRiskInterval)
    (left right : Optic) : Prop :=
  (interval left).upper < (interval right).lower

/-- The certified dominance relation is irreflexive. -/
theorem certifiedOpticDominates_irrefl
    {Optic : Type uOptic}
    (interval : Optic → CertifiedRiskInterval)
    (optic : Optic) :
    ¬ CertifiedOpticDominates interval optic optic := by
  intro dominates
  exact (not_lt_of_ge (interval optic).coherent) dominates

/-- Certified dominance is transitive; hence a multi-step elimination chain
can be compressed to one directly certified comparison. -/
theorem certifiedOpticDominates_trans
    {Optic : Type uOptic}
    (interval : Optic → CertifiedRiskInterval)
    {first second third : Optic}
    (firstSecond : CertifiedOpticDominates interval first second)
    (secondThird : CertifiedOpticDominates interval second third) :
    CertifiedOpticDominates interval first third := by
  unfold CertifiedOpticDominates at *
  exact lt_of_lt_of_le firstSecond
    (le_trans (interval second).coherent (le_of_lt secondThird))

/-- Two opposite certified dominance claims are inconsistent. -/
theorem certifiedOpticDominates_asymm
    {Optic : Type uOptic}
    (interval : Optic → CertifiedRiskInterval)
    {left right : Optic}
    (leftRight : CertifiedOpticDominates interval left right) :
    ¬ CertifiedOpticDominates interval right left := by
  intro rightLeft
  have self := certifiedOpticDominates_trans interval leftRight rightLeft
  exact certifiedOpticDominates_irrefl interval left self

/-- Once certified, a dominance edge persists under endpoint tightening. -/
theorem certified_dominance_persists_under_interval_tightening
    {Optic : Type uOptic}
    (oldInterval newInterval : Optic → CertifiedRiskInterval)
    (tightens : ∀ optic,
      (oldInterval optic).Tightens (newInterval optic))
    {left right : Optic}
    (oldDominance : CertifiedOpticDominates oldInterval left right) :
    CertifiedOpticDominates newInterval left right := by
  unfold CertifiedOpticDominates at *
  exact lt_of_le_of_lt (tightens left).2
    (lt_of_lt_of_le oldDominance (tightens right).1)

/-- A true risk contained in a tighter interval is also contained in its
predecessor interval. -/
theorem trueRisk_membership_transports_to_looser_interval
    (old new : CertifiedRiskInterval)
    (tightens : old.Tightens new)
    (risk : ℝ)
    (insideNew : new.lower ≤ risk ∧ risk ≤ new.upper) :
    old.lower ≤ risk ∧ risk ≤ old.upper :=
  ⟨tightens.1.trans insideNew.1, insideNew.2.trans tightens.2⟩

/-- Soundness against any unknown true-risk assignment lying inside all
registered intervals. -/
theorem certifiedOpticDominance_implies_trueRisk_order
    {Optic : Type uOptic}
    (interval : Optic → CertifiedRiskInterval)
    (trueRisk : Optic → ℝ)
    (inside : ∀ optic,
      (interval optic).lower ≤ trueRisk optic ∧
        trueRisk optic ≤ (interval optic).upper)
    {left right : Optic}
    (dominates : CertifiedOpticDominates interval left right) :
    trueRisk left < trueRisk right := by
  unfold CertifiedOpticDominates at dominates
  exact lt_of_le_of_lt (inside left).2
    (lt_of_lt_of_le dominates (inside right).1)

/-- A candidate whose upper risk is below every competitor's lower risk is
the unique strict optimum for every true-risk assignment compatible with the
registered intervals. -/
theorem dominates_all_is_uniformly_unique_best
    {Optic : Type uOptic}
    (registered : Finset Optic)
    (interval : Optic → CertifiedRiskInterval)
    (trueRisk : Optic → ℝ)
    (inside : ∀ optic,
      (interval optic).lower ≤ trueRisk optic ∧
        trueRisk optic ≤ (interval optic).upper)
    (chosen : Optic)
    (chosenRegistered : chosen ∈ registered)
    (dominatesEveryOther : ∀ other ∈ registered, other ≠ chosen →
      CertifiedOpticDominates interval chosen other) :
    chosen ∈ registered ∧
      ∀ other ∈ registered, other ≠ chosen → trueRisk chosen < trueRisk other := by
  refine ⟨chosenRegistered, ?_⟩
  intro other otherRegistered different
  exact certifiedOpticDominance_implies_trueRisk_order interval trueRisk inside
    (dominatesEveryOther other otherRegistered different)

/-- Overlap witness: if two coherent intervals intersect, the evidence is
compatible with equal true risks.  Therefore strict ranking is not identified
from those intervals alone. -/
theorem overlapping_risk_intervals_admit_equal_trueRisks
    (left right : CertifiedRiskInterval)
    (overlap : max left.lower right.lower ≤ min left.upper right.upper) :
    ∃ leftRisk rightRisk : ℝ,
      left.lower ≤ leftRisk ∧ leftRisk ≤ left.upper ∧
      right.lower ≤ rightRisk ∧ rightRisk ≤ right.upper ∧
      leftRisk = rightRisk := by
  let shared := max left.lower right.lower
  have sharedLeftLower : left.lower ≤ shared := le_max_left _ _
  have sharedRightLower : right.lower ≤ shared := le_max_right _ _
  have sharedLeftUpper : shared ≤ left.upper :=
    overlap.trans (min_le_left _ _)
  have sharedRightUpper : shared ≤ right.upper :=
    overlap.trans (min_le_right _ _)
  exact ⟨shared, shared, sharedLeftLower, sharedLeftUpper,
    sharedRightLower, sharedRightUpper, rfl⟩

/-- Complete two-interval adjudication boundary: disjoint coherent intervals
certify exactly one direction of strict dominance. -/
theorem disjoint_risk_intervals_certify_one_dominance_direction
    (left right : CertifiedRiskInterval)
    (disjoint : min left.upper right.upper < max left.lower right.lower) :
    left.upper < right.lower ∨ right.upper < left.lower := by
  by_cases leftBefore : left.upper < right.lower
  · exact Or.inl leftBefore
  · right
    have rightLowerLeLeftUpper : right.lower ≤ left.upper := le_of_not_gt leftBefore
    by_contra notRightBefore
    have leftLowerLeRightUpper : left.lower ≤ right.upper := le_of_not_gt notRightBefore
    have maxLeLeftUpper :
        max left.lower right.lower ≤ left.upper :=
      max_le left.coherent rightLowerLeLeftUpper
    have maxLeRightUpper :
        max left.lower right.lower ≤ right.upper :=
      max_le leftLowerLeRightUpper right.coherent
    have maxLeMin :
        max left.lower right.lower ≤ min left.upper right.upper :=
      le_min maxLeLeftUpper maxLeRightUpper
    exact (not_le_of_gt disjoint) maxLeMin

/-- Registered candidates not strictly dominated by another registered optic. -/
noncomputable def certifiedNondominatedOptics
    {Optic : Type uOptic}
    (registered : Finset Optic)
    (interval : Optic → CertifiedRiskInterval) : Finset Optic := by
  classical
  exact registered.filter fun optic =>
    ¬ ∃ other ∈ registered, CertifiedOpticDominates interval other optic

/-- Every emitted optic is registered and has no registered certified
dominator. -/
theorem certifiedNondominatedOptics_member
    {Optic : Type uOptic}
    (registered : Finset Optic)
    (interval : Optic → CertifiedRiskInterval)
    {optic : Optic}
    (member : optic ∈ certifiedNondominatedOptics registered interval) :
    optic ∈ registered ∧
      ¬ ∃ other ∈ registered, CertifiedOpticDominates interval other optic := by
  classical
  change optic ∈ registered.filter (fun candidate =>
    ¬ ∃ other ∈ registered,
      CertifiedOpticDominates interval other candidate) at member
  exact Finset.mem_filter.mp member

/-- A certified dominated candidate is absent from the nondominated set. -/
theorem certified_dominated_optic_is_pruned
    {Optic : Type uOptic}
    (registered : Finset Optic)
    (interval : Optic → CertifiedRiskInterval)
    {dominator candidate : Optic}
    (dominatorRegistered : dominator ∈ registered)
    (dominates : CertifiedOpticDominates interval dominator candidate) :
    candidate ∉ certifiedNondominatedOptics registered interval := by
  intro member
  exact (certifiedNondominatedOptics_member registered interval member).2
    ⟨dominator, dominatorRegistered, dominates⟩

/-- As valid intervals tighten, the nondominated candidate set can only
shrink.  Old scientific eliminations are not silently reopened. -/
theorem certifiedNondominatedOptics_antitone_under_tightening
    {Optic : Type uOptic}
    (registered : Finset Optic)
    (oldInterval newInterval : Optic → CertifiedRiskInterval)
    (tightens : ∀ optic,
      (oldInterval optic).Tightens (newInterval optic)) :
    certifiedNondominatedOptics registered newInterval ⊆
      certifiedNondominatedOptics registered oldInterval := by
  intro optic newMember
  have newCertificate :=
    certifiedNondominatedOptics_member registered newInterval newMember
  classical
  change optic ∈ registered.filter (fun candidate =>
    ¬ ∃ other ∈ registered,
      CertifiedOpticDominates oldInterval other candidate)
  apply Finset.mem_filter.mpr
  refine ⟨newCertificate.1, ?_⟩
  rintro ⟨other, otherRegistered, oldDominance⟩
  have newDominance := certified_dominance_persists_under_interval_tightening
    oldInterval newInterval tightens oldDominance
  exact newCertificate.2 ⟨other, otherRegistered, newDominance⟩

/-- A candidate that dominated every registered competitor remains the unique
interval-certified winner after valid tightening. -/
theorem dominates_all_persists_under_interval_tightening
    {Optic : Type uOptic}
    (registered : Finset Optic)
    (oldInterval newInterval : Optic → CertifiedRiskInterval)
    (tightens : ∀ optic,
      (oldInterval optic).Tightens (newInterval optic))
    (chosen : Optic)
    (oldDominatesEveryOther : ∀ other ∈ registered, other ≠ chosen →
      CertifiedOpticDominates oldInterval chosen other) :
    ∀ other ∈ registered, other ≠ chosen →
      CertifiedOpticDominates newInterval chosen other := by
  intro other otherRegistered different
  exact certified_dominance_persists_under_interval_tightening
    oldInterval newInterval tightens
    (oldDominatesEveryOther other otherRegistered different)

end OCKIndividuationMSpaceComposition
