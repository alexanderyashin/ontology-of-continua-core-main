import OCKIndividuationMSpaceComposition.SequentialEvidenceInheritance
import Mathlib.Topology.MetricSpace.Defs

namespace OCKIndividuationMSpaceComposition

universe
  uState uInput uEvidence uTask uProjection uBoundary uConstraint uScope uFrame
  uFamily

/-!
# Quantitative evidence-transport defect

Sequential evidence is ordered: moving forward may add looks, alpha spend or
calibration debt, but an admitted continuation may not erase them.  The
directed defect below turns violation of that order into a number.  It is a
Lawvere-style (asymmetric) distance: zero is exact admissibility and the
triangle inequality is the universal composition law.

This layer is domain independent.  Repository paths, SHAs, deployments and
governance statuses are possible projections of a state, not constituents of
the definition.
-/

/-- Real-valued coordinates of a sequential evidence state. -/
structure EvidencePotential (Family : Type uFamily) where
  family : Family
  look : ℝ
  cumulativeAlphaSpend : ℝ
  calibrationDebt : ℝ

/-- The amount by which an irreversible coordinate illegally decreases. -/
def directedDrop (source target : ℝ) : ℝ :=
  max 0 (source - target)

theorem directedDrop_nonnegative (source target : ℝ) :
    0 ≤ directedDrop source target :=
  le_max_left _ _

theorem directedDrop_eq_zero_iff (source target : ℝ) :
    directedDrop source target = 0 ↔ source ≤ target := by
  constructor
  · intro zero
    have upper : source - target ≤ directedDrop source target :=
      le_max_right _ _
    rw [zero] at upper
    linarith
  · intro monotone
    simp [directedDrop, sub_nonpos.mpr monotone]

theorem directedDrop_triangle (first middle last : ℝ) :
    directedDrop first last ≤
      directedDrop first middle + directedDrop middle last := by
  apply max_le
  · exact add_nonneg
      (directedDrop_nonnegative first middle)
      (directedDrop_nonnegative middle last)
  · calc
      first - last = (first - middle) + (middle - last) := by ring
      _ ≤ max 0 (first - middle) + max 0 (middle - last) :=
        add_le_add (le_max_right _ _) (le_max_right _ _)

theorem directedDrop_eq_sub_of_le
    {source target : ℝ} (monotone : target ≤ source) :
    directedDrop source target = source - target := by
  exact max_eq_right (sub_nonneg.mpr monotone)

/--
Numerical defect of transporting one evidence potential into another.

The family coordinate uses an ordinary metric.  The irreversible coordinates
use a directed positive-part distance, so increases cost zero while decreases
are charged by their exact magnitude.
-/
def evidenceTransportDefect
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (source target : EvidencePotential Family) : ℝ :=
  dist source.family target.family +
    directedDrop source.look target.look +
    directedDrop source.cumulativeAlphaSpend target.cumulativeAlphaSpend +
    directedDrop source.calibrationDebt target.calibrationDebt

theorem evidenceTransportDefect_nonnegative
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (source target : EvidencePotential Family) :
    0 ≤ evidenceTransportDefect source target := by
  exact add_nonneg
    (add_nonneg
      (add_nonneg dist_nonneg
        (directedDrop_nonnegative source.look target.look))
      (directedDrop_nonnegative
        source.cumulativeAlphaSpend target.cumulativeAlphaSpend))
    (directedDrop_nonnegative source.calibrationDebt target.calibrationDebt)

/-- Exact characterization of a zero transport defect. -/
theorem evidenceTransportDefect_eq_zero_iff
    {Family : Type uFamily} [MetricSpace Family]
    (source target : EvidencePotential Family) :
    evidenceTransportDefect source target = 0 ↔
      source.family = target.family ∧
      source.look ≤ target.look ∧
      source.cumulativeAlphaSpend ≤ target.cumulativeAlphaSpend ∧
      source.calibrationDebt ≤ target.calibrationDebt := by
  constructor
  · intro zero
    have familyNonnegative : 0 ≤ dist source.family target.family := dist_nonneg
    have lookNonnegative :
        0 ≤ directedDrop source.look target.look :=
      directedDrop_nonnegative _ _
    have spendNonnegative :
        0 ≤ directedDrop
          source.cumulativeAlphaSpend target.cumulativeAlphaSpend :=
      directedDrop_nonnegative _ _
    have debtNonnegative :
        0 ≤ directedDrop source.calibrationDebt target.calibrationDebt :=
      directedDrop_nonnegative _ _
    have familyZero : dist source.family target.family = 0 := by
      unfold evidenceTransportDefect at zero
      linarith
    have lookZero : directedDrop source.look target.look = 0 := by
      unfold evidenceTransportDefect at zero
      linarith
    have spendZero : directedDrop
        source.cumulativeAlphaSpend target.cumulativeAlphaSpend = 0 := by
      unfold evidenceTransportDefect at zero
      linarith
    have debtZero : directedDrop
        source.calibrationDebt target.calibrationDebt = 0 := by
      unfold evidenceTransportDefect at zero
      linarith
    exact ⟨
      dist_eq_zero.mp familyZero,
      (directedDrop_eq_zero_iff _ _).mp lookZero,
      (directedDrop_eq_zero_iff _ _).mp spendZero,
      (directedDrop_eq_zero_iff _ _).mp debtZero⟩
  · rintro ⟨family, look, spend, debt⟩
    simp [evidenceTransportDefect, family,
      (directedDrop_eq_zero_iff _ _).mpr look,
      (directedDrop_eq_zero_iff _ _).mpr spend,
      (directedDrop_eq_zero_iff _ _).mpr debt]

theorem evidenceTransportDefect_self
    {Family : Type uFamily} [MetricSpace Family]
    (state : EvidencePotential Family) :
    evidenceTransportDefect state state = 0 := by
  exact (evidenceTransportDefect_eq_zero_iff state state).mpr
    ⟨rfl, le_rfl, le_rfl, le_rfl⟩

/-- Universal composition law for quantitative evidence transport. -/
theorem evidenceTransportDefect_triangle
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (first middle last : EvidencePotential Family) :
    evidenceTransportDefect first last ≤
      evidenceTransportDefect first middle +
        evidenceTransportDefect middle last := by
  have familyTriangle :
      dist first.family last.family ≤
        dist first.family middle.family + dist middle.family last.family :=
    dist_triangle _ _ _
  have lookTriangle := directedDrop_triangle first.look middle.look last.look
  have spendTriangle := directedDrop_triangle
    first.cumulativeAlphaSpend middle.cumulativeAlphaSpend
    last.cumulativeAlphaSpend
  have debtTriangle := directedDrop_triangle
    first.calibrationDebt middle.calibrationDebt last.calibrationDebt
  unfold evidenceTransportDefect
  linarith

/-- Exact additivity in the reverse direction along a monotone evidence path. -/
theorem evidenceTransportDefect_reverse_additive
    {Family : Type uFamily} [MetricSpace Family]
    (first middle last : EvidencePotential Family)
    (firstMiddleFamily : first.family = middle.family)
    (middleLastFamily : middle.family = last.family)
    (lookFirstMiddle : first.look ≤ middle.look)
    (lookMiddleLast : middle.look ≤ last.look)
    (spendFirstMiddle :
      first.cumulativeAlphaSpend ≤ middle.cumulativeAlphaSpend)
    (spendMiddleLast :
      middle.cumulativeAlphaSpend ≤ last.cumulativeAlphaSpend)
    (debtFirstMiddle : first.calibrationDebt ≤ middle.calibrationDebt)
    (debtMiddleLast : middle.calibrationDebt ≤ last.calibrationDebt) :
    evidenceTransportDefect last first =
      evidenceTransportDefect last middle +
        evidenceTransportDefect middle first := by
  have lookFirstLast : first.look ≤ last.look :=
    lookFirstMiddle.trans lookMiddleLast
  have spendFirstLast :
      first.cumulativeAlphaSpend ≤ last.cumulativeAlphaSpend :=
    spendFirstMiddle.trans spendMiddleLast
  have debtFirstLast : first.calibrationDebt ≤ last.calibrationDebt :=
    debtFirstMiddle.trans debtMiddleLast
  simp only [evidenceTransportDefect]
  rw [firstMiddleFamily, middleLastFamily]
  simp only [dist_self, zero_add]
  rw [directedDrop_eq_sub_of_le lookFirstLast,
    directedDrop_eq_sub_of_le lookMiddleLast,
    directedDrop_eq_sub_of_le lookFirstMiddle,
    directedDrop_eq_sub_of_le spendFirstLast,
    directedDrop_eq_sub_of_le spendMiddleLast,
    directedDrop_eq_sub_of_le spendFirstMiddle,
    directedDrop_eq_sub_of_le debtFirstLast,
    directedDrop_eq_sub_of_le debtMiddleLast,
    directedDrop_eq_sub_of_le debtFirstMiddle]
  ring

/-- Coordinatewise candidate for the least no-laundering branch merge. -/
def EvidencePotential.join
    {Family : Type uFamily}
    (left right : EvidencePotential Family) : EvidencePotential Family where
  family := left.family
  look := max left.look right.look
  cumulativeAlphaSpend :=
    max left.cumulativeAlphaSpend right.cumulativeAlphaSpend
  calibrationDebt := max left.calibrationDebt right.calibrationDebt

/-- Sum of the two directed transport defects into a proposed branch merge. -/
def branchMergeObstruction
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (left right merge : EvidencePotential Family) : ℝ :=
  evidenceTransportDefect left merge +
    evidenceTransportDefect right merge

theorem branchMergeObstruction_nonnegative
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (left right merge : EvidencePotential Family) :
    0 ≤ branchMergeObstruction left right merge := by
  exact add_nonneg
    (evidenceTransportDefect_nonnegative _ _)
    (evidenceTransportDefect_nonnegative _ _)

/--
Branch-family divergence is a numerical lower bound on every possible merge.
No choice of merge coordinates can hide it.
-/
theorem familyDistance_le_branchMergeObstruction
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (left right merge : EvidencePotential Family) :
    dist left.family right.family ≤
      branchMergeObstruction left right merge := by
  have leftBound :
      dist left.family merge.family ≤
        evidenceTransportDefect left merge := by
    unfold evidenceTransportDefect
    have look := directedDrop_nonnegative left.look merge.look
    have spend := directedDrop_nonnegative
      left.cumulativeAlphaSpend merge.cumulativeAlphaSpend
    have debt := directedDrop_nonnegative
      left.calibrationDebt merge.calibrationDebt
    linarith
  have rightBound :
      dist right.family merge.family ≤
        evidenceTransportDefect right merge := by
    unfold evidenceTransportDefect
    have look := directedDrop_nonnegative right.look merge.look
    have spend := directedDrop_nonnegative
      right.cumulativeAlphaSpend merge.cumulativeAlphaSpend
    have debt := directedDrop_nonnegative
      right.calibrationDebt merge.calibrationDebt
    linarith
  calc
    dist left.family right.family ≤
        dist left.family merge.family + dist merge.family right.family :=
      dist_triangle _ _ _
    _ = dist left.family merge.family + dist right.family merge.family := by
      rw [dist_comm merge.family right.family]
    _ ≤ evidenceTransportDefect left merge +
        evidenceTransportDefect right merge :=
      add_le_add leftBound rightBound
    _ = branchMergeObstruction left right merge := rfl

theorem branchMergeObstruction_eq_zero_iff
    {Family : Type uFamily} [MetricSpace Family]
    (left right merge : EvidencePotential Family) :
    branchMergeObstruction left right merge = 0 ↔
      evidenceTransportDefect left merge = 0 ∧
      evidenceTransportDefect right merge = 0 := by
  constructor
  · intro zero
    have leftNonnegative := evidenceTransportDefect_nonnegative left merge
    have rightNonnegative := evidenceTransportDefect_nonnegative right merge
    unfold branchMergeObstruction at zero
    exact ⟨by linarith, by linarith⟩
  · rintro ⟨leftZero, rightZero⟩
    simp [branchMergeObstruction, leftZero, rightZero]

/--
Closed-form optimum: the coordinatewise join removes every avoidable loss, so
its residual obstruction is exactly the distance between evidence families.
-/
theorem branchJoin_obstruction_eq_familyDistance
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (left right : EvidencePotential Family) :
    branchMergeObstruction left right (left.join right) =
      dist left.family right.family := by
  have leftLook : directedDrop left.look (max left.look right.look) = 0 :=
    (directedDrop_eq_zero_iff _ _).mpr (le_max_left _ _)
  have rightLook : directedDrop right.look (max left.look right.look) = 0 :=
    (directedDrop_eq_zero_iff _ _).mpr (le_max_right _ _)
  have leftSpend : directedDrop left.cumulativeAlphaSpend
      (max left.cumulativeAlphaSpend right.cumulativeAlphaSpend) = 0 :=
    (directedDrop_eq_zero_iff _ _).mpr (le_max_left _ _)
  have rightSpend : directedDrop right.cumulativeAlphaSpend
      (max left.cumulativeAlphaSpend right.cumulativeAlphaSpend) = 0 :=
    (directedDrop_eq_zero_iff _ _).mpr (le_max_right _ _)
  have leftDebt : directedDrop left.calibrationDebt
      (max left.calibrationDebt right.calibrationDebt) = 0 :=
    (directedDrop_eq_zero_iff _ _).mpr (le_max_left _ _)
  have rightDebt : directedDrop right.calibrationDebt
      (max left.calibrationDebt right.calibrationDebt) = 0 :=
    (directedDrop_eq_zero_iff _ _).mpr (le_max_right _ _)
  simp [branchMergeObstruction, evidenceTransportDefect,
    EvidencePotential.join, leftLook, rightLook, leftSpend, rightSpend,
    leftDebt, rightDebt, dist_comm]

/-- The closed-form join globally minimizes obstruction over every merge. -/
theorem branchJoin_minimizes_obstruction
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (left right merge : EvidencePotential Family) :
    branchMergeObstruction left right (left.join right) ≤
      branchMergeObstruction left right merge := by
  rw [branchJoin_obstruction_eq_familyDistance]
  exact familyDistance_le_branchMergeObstruction left right merge

/-- Same-family branches admit a canonical zero-obstruction merge. -/
theorem compatibleBranches_join_has_zero_obstruction
    {Family : Type uFamily} [MetricSpace Family]
    (left right : EvidencePotential Family)
    (sameFamily : left.family = right.family) :
    branchMergeObstruction left right (left.join right) = 0 := by
  apply (branchMergeObstruction_eq_zero_iff _ _ _).mpr
  constructor
  · apply (evidenceTransportDefect_eq_zero_iff _ _).mpr
    exact ⟨rfl, le_max_left _ _, le_max_left _ _, le_max_left _ _⟩
  · apply (evidenceTransportDefect_eq_zero_iff _ _).mpr
    exact ⟨sameFamily.symm, le_max_right _ _, le_max_right _ _,
      le_max_right _ _⟩

/-- The canonical join is least among every zero-defect merge candidate. -/
theorem compatibleBranches_join_is_least
    {Family : Type uFamily} [MetricSpace Family]
    (left right merge : EvidencePotential Family)
    (leftAdmitted : evidenceTransportDefect left merge = 0)
    (rightAdmitted : evidenceTransportDefect right merge = 0) :
    evidenceTransportDefect (left.join right) merge = 0 := by
  have leftOrder :=
    (evidenceTransportDefect_eq_zero_iff left merge).mp leftAdmitted
  have rightOrder :=
    (evidenceTransportDefect_eq_zero_iff right merge).mp rightAdmitted
  apply (evidenceTransportDefect_eq_zero_iff _ _).mpr
  exact ⟨
    leftOrder.1,
    max_le leftOrder.2.1 rightOrder.2.1,
    max_le leftOrder.2.2.1 rightOrder.2.2.1,
    max_le leftOrder.2.2.2 rightOrder.2.2.2⟩

/-- No-go: genuinely different evidence families cannot have a zero-obstruction merge. -/
theorem familyDivergence_obstructs_zero_merge
    {Family : Type uFamily} [MetricSpace Family]
    (left right merge : EvidencePotential Family)
    (differentFamily : left.family ≠ right.family) :
    branchMergeObstruction left right merge ≠ 0 := by
  intro zero
  have lower := familyDistance_le_branchMergeObstruction left right merge
  have positive : 0 < dist left.family right.family :=
    dist_pos.mpr differentFamily
  rw [zero] at lower
  linarith

/-!
## Registered calibration

The unweighted defect is meaningful only after its coordinates have been
normalized to common units.  The calibrated form makes that scientific choice
explicit.  Nonnegative weights preserve composition; strictly positive weights
also preserve the exact zero-defect characterization.
-/

structure EvidenceTransportWeights where
  lookWeight : ℝ
  spendWeight : ℝ
  debtWeight : ℝ

def EvidenceTransportWeights.Nonnegative
    (weights : EvidenceTransportWeights) : Prop :=
  0 ≤ weights.lookWeight ∧
    0 ≤ weights.spendWeight ∧
    0 ≤ weights.debtWeight

def EvidenceTransportWeights.StrictlyPositive
    (weights : EvidenceTransportWeights) : Prop :=
  0 < weights.lookWeight ∧
    0 < weights.spendWeight ∧
    0 < weights.debtWeight

def weightedEvidenceTransportDefect
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (weights : EvidenceTransportWeights)
    (source target : EvidencePotential Family) : ℝ :=
  dist source.family target.family +
    weights.lookWeight * directedDrop source.look target.look +
    weights.spendWeight *
      directedDrop source.cumulativeAlphaSpend target.cumulativeAlphaSpend +
    weights.debtWeight *
      directedDrop source.calibrationDebt target.calibrationDebt

theorem weightedEvidenceTransportDefect_nonnegative
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (weights : EvidenceTransportWeights)
    (weightsNonnegative : weights.Nonnegative)
    (source target : EvidencePotential Family) :
    0 ≤ weightedEvidenceTransportDefect weights source target := by
  unfold weightedEvidenceTransportDefect
  exact add_nonneg
    (add_nonneg
      (add_nonneg dist_nonneg
        (mul_nonneg weightsNonnegative.1
          (directedDrop_nonnegative source.look target.look)))
      (mul_nonneg weightsNonnegative.2.1
        (directedDrop_nonnegative
          source.cumulativeAlphaSpend target.cumulativeAlphaSpend)))
    (mul_nonneg weightsNonnegative.2.2
      (directedDrop_nonnegative source.calibrationDebt target.calibrationDebt))

theorem weightedEvidenceTransportDefect_eq_zero_iff
    {Family : Type uFamily} [MetricSpace Family]
    (weights : EvidenceTransportWeights)
    (weightsPositive : weights.StrictlyPositive)
    (source target : EvidencePotential Family) :
    weightedEvidenceTransportDefect weights source target = 0 ↔
      source.family = target.family ∧
      source.look ≤ target.look ∧
      source.cumulativeAlphaSpend ≤ target.cumulativeAlphaSpend ∧
      source.calibrationDebt ≤ target.calibrationDebt := by
  have weightsNonnegative : weights.Nonnegative :=
    ⟨weightsPositive.1.le, weightsPositive.2.1.le,
      weightsPositive.2.2.le⟩
  constructor
  · intro zero
    have familyNonnegative : 0 ≤ dist source.family target.family := dist_nonneg
    have lookDropNonnegative := directedDrop_nonnegative source.look target.look
    have spendDropNonnegative := directedDrop_nonnegative
      source.cumulativeAlphaSpend target.cumulativeAlphaSpend
    have debtDropNonnegative := directedDrop_nonnegative
      source.calibrationDebt target.calibrationDebt
    have lookTermNonnegative : 0 ≤ weights.lookWeight *
        directedDrop source.look target.look :=
      mul_nonneg weightsNonnegative.1 lookDropNonnegative
    have spendTermNonnegative : 0 ≤ weights.spendWeight *
        directedDrop source.cumulativeAlphaSpend target.cumulativeAlphaSpend :=
      mul_nonneg weightsNonnegative.2.1 spendDropNonnegative
    have debtTermNonnegative : 0 ≤ weights.debtWeight *
        directedDrop source.calibrationDebt target.calibrationDebt :=
      mul_nonneg weightsNonnegative.2.2 debtDropNonnegative
    have familyZero : dist source.family target.family = 0 := by
      unfold weightedEvidenceTransportDefect at zero
      linarith
    have lookTermZero : weights.lookWeight *
        directedDrop source.look target.look = 0 := by
      unfold weightedEvidenceTransportDefect at zero
      linarith
    have spendTermZero : weights.spendWeight *
        directedDrop source.cumulativeAlphaSpend target.cumulativeAlphaSpend = 0 := by
      unfold weightedEvidenceTransportDefect at zero
      linarith
    have debtTermZero : weights.debtWeight *
        directedDrop source.calibrationDebt target.calibrationDebt = 0 := by
      unfold weightedEvidenceTransportDefect at zero
      linarith
    have lookZero : directedDrop source.look target.look = 0 :=
      (mul_eq_zero.mp lookTermZero).resolve_left (ne_of_gt weightsPositive.1)
    have spendZero : directedDrop
        source.cumulativeAlphaSpend target.cumulativeAlphaSpend = 0 :=
      (mul_eq_zero.mp spendTermZero).resolve_left
        (ne_of_gt weightsPositive.2.1)
    have debtZero : directedDrop
        source.calibrationDebt target.calibrationDebt = 0 :=
      (mul_eq_zero.mp debtTermZero).resolve_left
        (ne_of_gt weightsPositive.2.2)
    exact ⟨
      dist_eq_zero.mp familyZero,
      (directedDrop_eq_zero_iff _ _).mp lookZero,
      (directedDrop_eq_zero_iff _ _).mp spendZero,
      (directedDrop_eq_zero_iff _ _).mp debtZero⟩
  · rintro ⟨family, look, spend, debt⟩
    simp [weightedEvidenceTransportDefect, family,
      (directedDrop_eq_zero_iff _ _).mpr look,
      (directedDrop_eq_zero_iff _ _).mpr spend,
      (directedDrop_eq_zero_iff _ _).mpr debt]

theorem weightedEvidenceTransportDefect_triangle
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (weights : EvidenceTransportWeights)
    (weightsNonnegative : weights.Nonnegative)
    (first middle last : EvidencePotential Family) :
    weightedEvidenceTransportDefect weights first last ≤
      weightedEvidenceTransportDefect weights first middle +
        weightedEvidenceTransportDefect weights middle last := by
  have familyTriangle :
      dist first.family last.family ≤
        dist first.family middle.family + dist middle.family last.family :=
    dist_triangle _ _ _
  have lookTriangle := mul_le_mul_of_nonneg_left
    (directedDrop_triangle first.look middle.look last.look)
    weightsNonnegative.1
  have spendTriangle := mul_le_mul_of_nonneg_left
    (directedDrop_triangle first.cumulativeAlphaSpend
      middle.cumulativeAlphaSpend last.cumulativeAlphaSpend)
    weightsNonnegative.2.1
  have debtTriangle := mul_le_mul_of_nonneg_left
    (directedDrop_triangle first.calibrationDebt
      middle.calibrationDebt last.calibrationDebt)
    weightsNonnegative.2.2
  unfold weightedEvidenceTransportDefect
  linarith

def weightedBranchMergeObstruction
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (weights : EvidenceTransportWeights)
    (left right merge : EvidencePotential Family) : ℝ :=
  weightedEvidenceTransportDefect weights left merge +
    weightedEvidenceTransportDefect weights right merge

theorem familyDistance_le_weightedBranchMergeObstruction
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (weights : EvidenceTransportWeights)
    (weightsNonnegative : weights.Nonnegative)
    (left right merge : EvidencePotential Family) :
    dist left.family right.family ≤
      weightedBranchMergeObstruction weights left right merge := by
  have leftBound : dist left.family merge.family ≤
      weightedEvidenceTransportDefect weights left merge := by
    unfold weightedEvidenceTransportDefect
    have look := mul_nonneg weightsNonnegative.1
      (directedDrop_nonnegative left.look merge.look)
    have spend := mul_nonneg weightsNonnegative.2.1
      (directedDrop_nonnegative
        left.cumulativeAlphaSpend merge.cumulativeAlphaSpend)
    have debt := mul_nonneg weightsNonnegative.2.2
      (directedDrop_nonnegative left.calibrationDebt merge.calibrationDebt)
    linarith
  have rightBound : dist right.family merge.family ≤
      weightedEvidenceTransportDefect weights right merge := by
    unfold weightedEvidenceTransportDefect
    have look := mul_nonneg weightsNonnegative.1
      (directedDrop_nonnegative right.look merge.look)
    have spend := mul_nonneg weightsNonnegative.2.1
      (directedDrop_nonnegative
        right.cumulativeAlphaSpend merge.cumulativeAlphaSpend)
    have debt := mul_nonneg weightsNonnegative.2.2
      (directedDrop_nonnegative right.calibrationDebt merge.calibrationDebt)
    linarith
  calc
    dist left.family right.family ≤
        dist left.family merge.family + dist merge.family right.family :=
      dist_triangle _ _ _
    _ = dist left.family merge.family + dist right.family merge.family := by
      rw [dist_comm merge.family right.family]
    _ ≤ weightedEvidenceTransportDefect weights left merge +
        weightedEvidenceTransportDefect weights right merge :=
      add_le_add leftBound rightBound
    _ = weightedBranchMergeObstruction weights left right merge := rfl

theorem weightedBranchJoin_obstruction_eq_familyDistance
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (weights : EvidenceTransportWeights)
    (left right : EvidencePotential Family) :
    weightedBranchMergeObstruction weights left right (left.join right) =
      dist left.family right.family := by
  have leftLook : directedDrop left.look (max left.look right.look) = 0 :=
    (directedDrop_eq_zero_iff _ _).mpr (le_max_left _ _)
  have rightLook : directedDrop right.look (max left.look right.look) = 0 :=
    (directedDrop_eq_zero_iff _ _).mpr (le_max_right _ _)
  have leftSpend : directedDrop left.cumulativeAlphaSpend
      (max left.cumulativeAlphaSpend right.cumulativeAlphaSpend) = 0 :=
    (directedDrop_eq_zero_iff _ _).mpr (le_max_left _ _)
  have rightSpend : directedDrop right.cumulativeAlphaSpend
      (max left.cumulativeAlphaSpend right.cumulativeAlphaSpend) = 0 :=
    (directedDrop_eq_zero_iff _ _).mpr (le_max_right _ _)
  have leftDebt : directedDrop left.calibrationDebt
      (max left.calibrationDebt right.calibrationDebt) = 0 :=
    (directedDrop_eq_zero_iff _ _).mpr (le_max_left _ _)
  have rightDebt : directedDrop right.calibrationDebt
      (max left.calibrationDebt right.calibrationDebt) = 0 :=
    (directedDrop_eq_zero_iff _ _).mpr (le_max_right _ _)
  simp [weightedBranchMergeObstruction, weightedEvidenceTransportDefect,
    EvidencePotential.join, leftLook, rightLook, leftSpend, rightSpend,
    leftDebt, rightDebt, dist_comm]

theorem weightedBranchJoin_minimizes_obstruction
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (weights : EvidenceTransportWeights)
    (weightsNonnegative : weights.Nonnegative)
    (left right merge : EvidencePotential Family) :
    weightedBranchMergeObstruction weights left right (left.join right) ≤
      weightedBranchMergeObstruction weights left right merge := by
  rw [weightedBranchJoin_obstruction_eq_familyDistance]
  exact familyDistance_le_weightedBranchMergeObstruction
    weights weightsNonnegative left right merge

/-- Embed the operational account into the universal real-valued potential. -/
def SequentialEvidenceAccount.toPotential
    {Family : Type uFamily}
    (account : SequentialEvidenceAccount Family) : EvidencePotential Family where
  family := account.family
  look := account.lookIndex
  cumulativeAlphaSpend := account.cumulativeAlphaSpend
  calibrationDebt := account.calibrationDebt

theorem accountInheritance_has_zero_transportDefect
    {Family : Type uFamily} [MetricSpace Family]
    (source target : SequentialEvidenceAccount Family)
    (family : source.family = target.family)
    (look : source.lookIndex ≤ target.lookIndex)
    (spend : source.cumulativeAlphaSpend ≤ target.cumulativeAlphaSpend)
    (debt : source.calibrationDebt ≤ target.calibrationDebt) :
    evidenceTransportDefect source.toPotential target.toPotential = 0 := by
  apply (evidenceTransportDefect_eq_zero_iff _ _).mpr
  refine ⟨family, ?_, spend, debt⟩
  change (source.lookIndex : ℝ) ≤ (target.lookIndex : ℝ)
  exact_mod_cast look

namespace ContinuationWitness

/-- Every admitted continuation has zero forward evidence-transport defect. -/
theorem sequentialEvidence_zero_transportDefect
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {Family : Type uFamily} [MetricSpace Family]
    {context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {account : State → SequentialEvidenceAccount Family}
    {revisionOnly : Evidence → Prop}
    (contract : EvidenceInheritanceContract context account revisionOnly)
    {initial endpoint : State}
    (witness : ContinuationWitness context initial endpoint) :
    evidenceTransportDefect
      (account initial).toPotential (account endpoint).toPotential = 0 := by
  have inheritance := witness.sequentialEvidence_inherits contract
  exact accountInheritance_has_zero_transportDefect
    (account initial) (account endpoint)
    inheritance.1 inheritance.2.1 inheritance.2.2.1 inheritance.2.2.2

/-- Registered coordinate calibration preserves the zero-defect path theorem. -/
theorem sequentialEvidence_zero_weightedTransportDefect
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {Family : Type uFamily} [MetricSpace Family]
    {context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {account : State → SequentialEvidenceAccount Family}
    {revisionOnly : Evidence → Prop}
    (weights : EvidenceTransportWeights)
    (contract : EvidenceInheritanceContract context account revisionOnly)
    {initial endpoint : State}
    (witness : ContinuationWitness context initial endpoint) :
    weightedEvidenceTransportDefect weights
      (account initial).toPotential (account endpoint).toPotential = 0 := by
  have inheritance := witness.sequentialEvidence_inherits contract
  have family := inheritance.1
  change (account initial).toPotential.family =
    (account endpoint).toPotential.family at family
  have look : (account initial).toPotential.look ≤
      (account endpoint).toPotential.look := by
    change ((account initial).lookIndex : ℝ) ≤
      ((account endpoint).lookIndex : ℝ)
    exact_mod_cast inheritance.2.1
  have spend := inheritance.2.2.1
  change (account initial).toPotential.cumulativeAlphaSpend ≤
    (account endpoint).toPotential.cumulativeAlphaSpend at spend
  have debt := inheritance.2.2.2
  change (account initial).toPotential.calibrationDebt ≤
    (account endpoint).toPotential.calibrationDebt at debt
  simp [weightedEvidenceTransportDefect, family,
    (directedDrop_eq_zero_iff _ _).mpr look,
    (directedDrop_eq_zero_iff _ _).mpr spend,
    (directedDrop_eq_zero_iff _ _).mpr debt]

/-- Revision-only transport is zero in both directions, not merely forward. -/
theorem revisionOnly_zero_bidirectional_transportDefect
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {Family : Type uFamily} [MetricSpace Family]
    {context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {account : State → SequentialEvidenceAccount Family}
    {revisionOnly : Evidence → Prop}
    (contract : EvidenceInheritanceContract context account revisionOnly)
    {initial endpoint : State}
    (witness : ContinuationWitness context initial endpoint)
    (onlyRevisions : ∀ evidence,
      evidence ∈ witness.evidence.evidenceTrace → revisionOnly evidence) :
    evidenceTransportDefect
        (account initial).toPotential (account endpoint).toPotential = 0 ∧
      evidenceTransportDefect
        (account endpoint).toPotential (account initial).toPotential = 0 := by
  have accountEquality :=
    witness.revisionOnly_preserves_sequentialEvidence contract onlyRevisions
  rw [accountEquality]
  exact ⟨evidenceTransportDefect_self _, evidenceTransportDefect_self _⟩

end ContinuationWitness

end OCKIndividuationMSpaceComposition
