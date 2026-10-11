import OCKIndividuationMSpaceComposition.GovernanceBarrierHazard

namespace OCKIndividuationMSpaceComposition

/-! A typed bridge from persistent threshold dynamics to governance hazard. -/

/-- First crossing for an arbitrary rational-valued order parameter. -/
def ThresholdCrossesAt (state : ℕ → ℚ) (threshold : ℚ) (crossing : ℕ) : Prop :=
  threshold ≤ state crossing ∧
    ∀ earlier, earlier < crossing → state earlier < threshold

/-- A first crossing that remains in the crossed regime thereafter. -/
structure PersistentThresholdCrossingAt
    (state : ℕ → ℚ) (threshold : ℚ) (crossing : ℕ) : Prop where
  crosses : ThresholdCrossesAt state threshold crossing
  persists : ∀ later, crossing ≤ later → threshold ≤ state later

/-- Hazard is activated exactly when the declared order parameter is crossed. -/
def thresholdActivatedHazard
    (state : ℕ → ℚ) (threshold rate : ℚ) (t : ℕ) : ℚ :=
  if threshold ≤ state t then rate else 0

theorem thresholdActivatedHazard_before_crossing
    {state : ℕ → ℚ} {threshold rate : ℚ} {crossing t : ℕ}
    (persistent : PersistentThresholdCrossingAt state threshold crossing)
    (before : t < crossing) :
    thresholdActivatedHazard state threshold rate t = 0 := by
  have below := persistent.crosses.2 t before
  simp [thresholdActivatedHazard, not_le.mpr below]

theorem thresholdActivatedHazard_at_or_after_crossing
    {state : ℕ → ℚ} {threshold rate : ℚ} {crossing t : ℕ}
    (persistent : PersistentThresholdCrossingAt state threshold crossing)
    (atOrAfter : crossing ≤ t) :
    thresholdActivatedHazard state threshold rate t = rate := by
  simp [thresholdActivatedHazard, persistent.persists t atOrAfter]

/-- Before activation, survival is exactly one. -/
theorem thresholdActivated_survival_at_crossing
    {state : ℕ → ℚ} {threshold rate : ℚ} {crossing : ℕ}
    (persistent : PersistentThresholdCrossingAt state threshold crossing) :
    barrierSurvival (thresholdActivatedHazard state threshold rate) crossing = 1 := by
  unfold barrierSurvival
  apply Finset.prod_eq_one
  intro t member
  have before : t < crossing := Finset.mem_range.mp member
  rw [thresholdActivatedHazard_before_crossing persistent before]
  ring

/-- After a persistent crossing, survival has the exact shifted geometric law. -/
theorem thresholdActivated_survival_after_crossing
    {state : ℕ → ℚ} {threshold rate : ℚ} {crossing : ℕ}
    (persistent : PersistentThresholdCrossingAt state threshold crossing)
    (post : ℕ) :
    barrierSurvival (thresholdActivatedHazard state threshold rate) (crossing + post) =
      (1 - rate) ^ post := by
  induction post with
  | zero => simpa using thresholdActivated_survival_at_crossing persistent
  | succ post ih =>
      rw [Nat.add_succ, barrierSurvival_succ, ih]
      rw [thresholdActivatedHazard_at_or_after_crossing persistent (Nat.le_add_right crossing post)]
      ring

theorem thresholdActivated_cdf_after_crossing
    {state : ℕ → ℚ} {threshold rate : ℚ} {crossing : ℕ}
    (persistent : PersistentThresholdCrossingAt state threshold crossing)
    (post : ℕ) :
    barrierCdf (thresholdActivatedHazard state threshold rate) (crossing + post) =
      1 - (1 - rate) ^ post := by
  rw [barrierCdf, thresholdActivated_survival_after_crossing persistent post]

theorem thresholdActivated_first_mass_after_crossing
    {state : ℕ → ℚ} {threshold rate : ℚ} {crossing : ℕ}
    (persistent : PersistentThresholdCrossingAt state threshold crossing)
    (post : ℕ) :
    firstBarrierMass (thresholdActivatedHazard state threshold rate) (crossing + post) =
      (1 - rate) ^ post * rate := by
  rw [firstBarrierMass, thresholdActivated_survival_after_crossing persistent post]
  rw [thresholdActivatedHazard_at_or_after_crossing persistent (Nat.le_add_right crossing post)]

/-- A transient one-step crossing countermodel. -/
def transientThresholdState (t : ℕ) : ℚ := if t = 1 then 1 else 0

/-- A crossing with the same first event but persistent post-crossing regime. -/
def persistentThresholdState (t : ℕ) : ℚ := if 1 ≤ t then 1 else 0

theorem transientThresholdState_crosses_at_one :
    ThresholdCrossesAt transientThresholdState 1 1 := by
  constructor
  · simp [transientThresholdState]
  · intro earlier before
    have zero : earlier = 0 :=
      Nat.eq_zero_of_le_zero (Nat.le_of_lt_succ before)
    subst earlier
    simp [transientThresholdState]

theorem persistentThresholdState_crosses_at_one :
    ThresholdCrossesAt persistentThresholdState 1 1 := by
  constructor
  · simp [persistentThresholdState]
  · intro earlier before
    have zero : earlier = 0 :=
      Nat.eq_zero_of_le_zero (Nat.le_of_lt_succ before)
    subst earlier
    simp [persistentThresholdState]

theorem persistentThresholdState_persists :
    PersistentThresholdCrossingAt persistentThresholdState 1 1 where
  crosses := persistentThresholdState_crosses_at_one
  persists := by
    intro later atOrAfter
    simp [persistentThresholdState, atOrAfter]

/--
No-go: equal first-crossing time does not determine future hazard unless
persistence (or a replacement post-crossing law) is supplied.
-/
theorem first_crossing_alone_does_not_determine_future_hazard
    (rate : ℚ) (nonzero : rate ≠ 0) :
    ThresholdCrossesAt transientThresholdState 1 1 ∧
    ThresholdCrossesAt persistentThresholdState 1 1 ∧
    thresholdActivatedHazard transientThresholdState 1 rate 2 ≠
      thresholdActivatedHazard persistentThresholdState 1 rate 2 := by
  refine ⟨transientThresholdState_crosses_at_one,
    persistentThresholdState_crosses_at_one, ?_⟩
  simpa [thresholdActivatedHazard, transientThresholdState,
    persistentThresholdState] using (Ne.symm nonzero)

/-! A finite-dwell extension: activation lasts for exactly `dwell` steps. -/

def finiteDwellHazard (crossing dwell : ℕ) (rate : ℚ) (t : ℕ) : ℚ :=
  if t < crossing then 0 else if t < crossing + dwell then rate else 0

theorem finiteDwellHazard_before
    {crossing dwell t : ℕ} {rate : ℚ} (before : t < crossing) :
    finiteDwellHazard crossing dwell rate t = 0 := by
  simp [finiteDwellHazard, before]

theorem finiteDwellHazard_during
    {crossing dwell t : ℕ} {rate : ℚ}
    (atOrAfter : crossing ≤ t) (beforeEnd : t < crossing + dwell) :
    finiteDwellHazard crossing dwell rate t = rate := by
  simp [finiteDwellHazard, Nat.not_lt.mpr atOrAfter, beforeEnd]

theorem finiteDwellHazard_after
    {crossing dwell t : ℕ} {rate : ℚ}
    (atOrAfterEnd : crossing + dwell ≤ t) :
    finiteDwellHazard crossing dwell rate t = 0 := by
  have atOrAfter : crossing ≤ t :=
    le_trans (Nat.le_add_right crossing dwell) atOrAfterEnd
  simp [finiteDwellHazard, Nat.not_lt.mpr atOrAfter,
    Nat.not_lt.mpr atOrAfterEnd]

theorem finiteDwell_survival_at_crossing
    {crossing dwell : ℕ} {rate : ℚ} :
    barrierSurvival (finiteDwellHazard crossing dwell rate) crossing = 1 := by
  unfold barrierSurvival
  apply Finset.prod_eq_one
  intro t member
  have before : t < crossing := Finset.mem_range.mp member
  rw [finiteDwellHazard_before before]
  ring

theorem finiteDwell_survival_during
    {crossing dwell : ℕ} {rate : ℚ} (post : ℕ) (within : post ≤ dwell) :
    barrierSurvival (finiteDwellHazard crossing dwell rate) (crossing + post) =
      (1 - rate) ^ post := by
  induction post with
  | zero => simpa using
      (finiteDwell_survival_at_crossing (crossing := crossing)
        (dwell := dwell) (rate := rate))
  | succ post ih =>
      have postWithin : post ≤ dwell :=
        le_trans (Nat.le_succ post) within
      have postBefore : post < dwell := Nat.lt_of_succ_le within
      rw [Nat.add_succ, barrierSurvival_succ, ih postWithin]
      rw [finiteDwellHazard_during (Nat.le_add_right crossing post)
        (Nat.add_lt_add_left postBefore crossing)]
      ring

theorem finiteDwell_survival_plateau
    {crossing dwell : ℕ} {rate : ℚ} (post : ℕ) :
    barrierSurvival (finiteDwellHazard crossing dwell rate)
        (crossing + dwell + post) =
      (1 - rate) ^ dwell := by
  induction post with
  | zero => simpa using
      (finiteDwell_survival_during (crossing := crossing) (dwell := dwell)
        (rate := rate) dwell (le_refl dwell))
  | succ post ih =>
      rw [Nat.add_succ, barrierSurvival_succ, ih]
      rw [finiteDwellHazard_after (Nat.le_add_right (crossing + dwell) post)]
      ring

theorem finiteDwell_cdf_plateau
    {crossing dwell : ℕ} {rate : ℚ} (post : ℕ) :
    barrierCdf (finiteDwellHazard crossing dwell rate)
        (crossing + dwell + post) =
      1 - (1 - rate) ^ dwell := by
  rw [barrierCdf, finiteDwell_survival_plateau]

/-! General post-crossing rates and their finite-window truncation. -/

def postCrossingHazard (crossing : ℕ) (rates : ℕ → ℚ) (t : ℕ) : ℚ :=
  if t < crossing then 0 else rates (t - crossing)

theorem postCrossingHazard_before
    {crossing t : ℕ} {rates : ℕ → ℚ} (before : t < crossing) :
    postCrossingHazard crossing rates t = 0 := by
  simp [postCrossingHazard, before]

theorem postCrossingHazard_at
    {crossing post : ℕ} {rates : ℕ → ℚ} :
    postCrossingHazard crossing rates (crossing + post) = rates post := by
  simp [postCrossingHazard, Nat.not_lt.mpr (Nat.le_add_right crossing post)]

theorem postCrossing_survival_at_crossing
    {crossing : ℕ} {rates : ℕ → ℚ} :
    barrierSurvival (postCrossingHazard crossing rates) crossing = 1 := by
  unfold barrierSurvival
  apply Finset.prod_eq_one
  intro t member
  have before : t < crossing := Finset.mem_range.mp member
  rw [postCrossingHazard_before before]
  ring

theorem postCrossing_survival_product
    {crossing : ℕ} {rates : ℕ → ℚ} (post : ℕ) :
    barrierSurvival (postCrossingHazard crossing rates) (crossing + post) =
      ∏ k ∈ Finset.range post, (1 - rates k) := by
  induction post with
  | zero => simpa using
      (postCrossing_survival_at_crossing (crossing := crossing) (rates := rates))
  | succ post ih =>
      rw [Nat.add_succ, barrierSurvival_succ, ih, postCrossingHazard_at]
      rw [Finset.prod_range_succ]

theorem postCrossing_cdf_product
    {crossing : ℕ} {rates : ℕ → ℚ} (post : ℕ) :
    barrierCdf (postCrossingHazard crossing rates) (crossing + post) =
      1 - ∏ k ∈ Finset.range post, (1 - rates k) := by
  rw [barrierCdf, postCrossing_survival_product]

def finiteWindowHazard
    (crossing dwell : ℕ) (rates : ℕ → ℚ) (t : ℕ) : ℚ :=
  if t < crossing then 0
  else if t < crossing + dwell then rates (t - crossing)
  else 0

theorem finiteWindowHazard_before
    {crossing dwell t : ℕ} {rates : ℕ → ℚ} (before : t < crossing) :
    finiteWindowHazard crossing dwell rates t = 0 := by
  simp [finiteWindowHazard, before]

theorem finiteWindowHazard_during
    {crossing dwell post : ℕ} {rates : ℕ → ℚ} (within : post < dwell) :
    finiteWindowHazard crossing dwell rates (crossing + post) = rates post := by
  have atOrAfter : ¬ crossing + post < crossing :=
    Nat.not_lt.mpr (Nat.le_add_right crossing post)
  have beforeEnd : crossing + post < crossing + dwell :=
    Nat.add_lt_add_left within crossing
  simp [finiteWindowHazard, atOrAfter, beforeEnd]

theorem finiteWindowHazard_after
    {crossing dwell t : ℕ} {rates : ℕ → ℚ}
    (atOrAfterEnd : crossing + dwell ≤ t) :
    finiteWindowHazard crossing dwell rates t = 0 := by
  have atOrAfter : crossing ≤ t :=
    le_trans (Nat.le_add_right crossing dwell) atOrAfterEnd
  simp [finiteWindowHazard, Nat.not_lt.mpr atOrAfter,
    Nat.not_lt.mpr atOrAfterEnd]

theorem finiteWindow_survival_during
    {crossing dwell : ℕ} {rates : ℕ → ℚ} (post : ℕ) (within : post ≤ dwell) :
    barrierSurvival (finiteWindowHazard crossing dwell rates) (crossing + post) =
      ∏ k ∈ Finset.range post, (1 - rates k) := by
  induction post with
  | zero =>
      unfold barrierSurvival
      simp only [Nat.add_zero, Finset.range_zero, Finset.prod_empty]
      apply Finset.prod_eq_one
      intro t member
      have before : t < crossing := Finset.mem_range.mp member
      rw [finiteWindowHazard_before before]
      ring
  | succ post ih =>
      have postWithin : post ≤ dwell := le_trans (Nat.le_succ post) within
      have postBefore : post < dwell := Nat.lt_of_succ_le within
      rw [Nat.add_succ, barrierSurvival_succ, ih postWithin]
      rw [finiteWindowHazard_during postBefore, Finset.prod_range_succ]

theorem finiteWindow_survival_plateau
    {crossing dwell : ℕ} {rates : ℕ → ℚ} (post : ℕ) :
    barrierSurvival (finiteWindowHazard crossing dwell rates)
        (crossing + dwell + post) =
      ∏ k ∈ Finset.range dwell, (1 - rates k) := by
  induction post with
  | zero => simpa using
      (finiteWindow_survival_during (crossing := crossing) (dwell := dwell)
        (rates := rates) dwell (le_refl dwell))
  | succ post ih =>
      rw [Nat.add_succ, barrierSurvival_succ, ih]
      rw [finiteWindowHazard_after (Nat.le_add_right (crossing + dwell) post)]
      ring

theorem finiteWindow_cdf_plateau
    {crossing dwell : ℕ} {rates : ℕ → ℚ} (post : ℕ) :
    barrierCdf (finiteWindowHazard crossing dwell rates)
        (crossing + dwell + post) =
      1 - ∏ k ∈ Finset.range dwell, (1 - rates k) := by
  rw [barrierCdf, finiteWindow_survival_plateau]

def earlyHalfHazard (t : ℕ) : ℚ := if t = 0 then 1 / 2 else 0

def lateHalfHazard (t : ℕ) : ℚ := if t = 1 then 1 / 2 else 0

/-- Endpoint survival does not identify when within the interval the risk occurred. -/
theorem endpoint_survival_does_not_identify_hazard_schedule :
    barrierSurvival earlyHalfHazard 2 = barrierSurvival lateHalfHazard 2 ∧
    earlyHalfHazard 0 ≠ lateHalfHazard 0 := by
  norm_num [barrierSurvival, earlyHalfHazard, lateHalfHazard,
    Finset.prod_range_succ]

end OCKIndividuationMSpaceComposition
