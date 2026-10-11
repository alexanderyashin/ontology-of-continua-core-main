import OCMinimalObligationSpine.Q073PortmanteauMomentBridge

/-!
# Q073 Lorentz displacement-law adapter

This module closes the mathematical adapter between a two-dimensional
displacement process and the already mechanized Q073 Portmanteau bridge.

The time argument is dimensionless.  A physical application must first choose
positive length and time scales and pass `t / timeScale` to this layer; taking
the logarithm of a unit-bearing time is not authorized here.

The module does not construct a Lorentz billiard flow and does not internalize
the Chernov--Dolgopyat weak limit theorem.  Those remain exact external inputs.
In particular, bibliographic metadata, replay hashes, and Boolean status fields
cannot inhabit any mathematical premise below.
-/

namespace OCMinimalObligationSpine

open Filter MeasureTheory
open scoped Topology

/-- The two-dimensional real displacement space used by Q073. -/
abbrev Q073Plane := EuclideanSpace ℝ (Fin 2)

local instance q073PlaneMeasurableSpace : MeasurableSpace Q073Plane :=
  borel Q073Plane

local instance q073PlaneBorelSpace : BorelSpace Q073Plane :=
  ⟨rfl⟩

/--
The minimal observable content of a displacement process.

`initialLaw` is the initial probability law and `displacement t ω` is the
unwrapped displacement at dimensionless time `t`.  No billiard equation,
ergodicity, weak limit, or asymptotic moment statement is hidden in this data
type.
-/
structure Q073DisplacementProcess
    (Ω : Type*) [MeasurableSpace Ω] where
  initialLaw : ProbabilityMeasure Ω
  displacement : ℝ → Ω → Q073Plane
  measurable_displacement : ∀ t, Measurable (displacement t)

/-- The dimensionless `sqrt (t log t)` normalization from the source theorem. -/
noncomputable def q073_lorentz_normalization (t : ℝ) : ℝ :=
  Real.sqrt (t * Real.log t)

/-- The normalized displacement random variable. -/
noncomputable def q073_normalizedDisplacement
    {Ω : Type*} [MeasurableSpace Ω]
    (process : Q073DisplacementProcess Ω)
    (t : ℝ) (ω : Ω) : Q073Plane :=
  (q073_lorentz_normalization t)⁻¹ • process.displacement t ω

theorem q073_normalizedDisplacement_measurable
    {Ω : Type*} [MeasurableSpace Ω]
    (process : Q073DisplacementProcess Ω)
    (t : ℝ) :
    Measurable (q073_normalizedDisplacement process t) := by
  exact
    (continuous_const_smul
      (q073_lorentz_normalization t)⁻¹).measurable.comp
      (process.measurable_displacement t)

/-- The push-forward law of the normalized displacement. -/
noncomputable def q073_normalizedDisplacementLaw
    {Ω : Type*} [MeasurableSpace Ω]
    (process : Q073DisplacementProcess Ω)
    (t : ℝ) : ProbabilityMeasure Q073Plane :=
  process.initialLaw.map
    (q073_normalizedDisplacement_measurable process t).aemeasurable

/-- Mean-square displacement in the initial law. -/
noncomputable def q073_meanSquareDisplacement
    {Ω : Type*} [MeasurableSpace Ω]
    (process : Q073DisplacementProcess Ω)
    (t : ℝ) : ℝ :=
  ∫ ω, ‖process.displacement t ω‖ ^ 2
    ∂(process.initialLaw : Measure Ω)

/-- The ordinary two-dimensional finite-time convention `MSD / (4t)`. -/
noncomputable def q073_effectiveDiffusion
    {Ω : Type*} [MeasurableSpace Ω]
    (process : Q073DisplacementProcess Ω)
    (t : ℝ) : ℝ :=
  q073_meanSquareDisplacement process t / (4 * t)

/-- The second moment of the normalized displacement law. -/
noncomputable def q073_normalizedSecondMoment
    {Ω : Type*} [MeasurableSpace Ω]
    (process : Q073DisplacementProcess Ω)
    (t : ℝ) : ℝ :=
  ∫ x, ‖x‖ ^ 2
    ∂(q073_normalizedDisplacementLaw process t : Measure Q073Plane)

@[simp]
theorem q073_effectiveDiffusion_eq_msd_div_four_time
    {Ω : Type*} [MeasurableSpace Ω]
    (process : Q073DisplacementProcess Ω)
    (t : ℝ) :
    q073_effectiveDiffusion process t =
      q073_meanSquareDisplacement process t / (4 * t) := by
  rfl

theorem q073_lorentz_normalization_pos
    {t : ℝ} (ht : 1 < t) :
    0 < q073_lorentz_normalization t := by
  unfold q073_lorentz_normalization
  exact Real.sqrt_pos.2
    (mul_pos (zero_lt_one.trans ht) (Real.log_pos ht))

theorem q073_lorentz_normalization_sq
    {t : ℝ} (ht : 1 < t) :
    q073_lorentz_normalization t ^ 2 = t * Real.log t := by
  unfold q073_lorentz_normalization
  exact Real.sq_sqrt
    (mul_nonneg
      (zero_le_one.trans ht.le)
      (Real.log_nonneg ht.le))

/--
The bounded truncation used by the Portmanteau bridge is dominated by the
actual second moment of every normalized law with a finite second moment.
-/
theorem q073_truncation_integral_le_normalizedSecondMoment
    {Ω : Type*} [MeasurableSpace Ω]
    (process : Q073DisplacementProcess Ω)
    (t : ℝ)
    (hMomentFinite :
      Integrable
        (fun x : Q073Plane => ‖x‖ ^ 2)
        (q073_normalizedDisplacementLaw process t : Measure Q073Plane)) :
    ∫ x, q073_squared_norm_truncation Q073Plane x
        ∂(q073_normalizedDisplacementLaw process t : Measure Q073Plane) ≤
      q073_normalizedSecondMoment process t := by
  unfold q073_normalizedSecondMoment q073_normalizedDisplacementLaw
  exact integral_mono
    ((q073_squared_norm_truncation Q073Plane).integrable _)
    hMomentFinite
    (fun x => min_le_left (‖x‖ ^ 2) 1)

/--
For `t > 1`, the second moment of `q(t) / sqrt (t log t)` is exactly
`MSD(t) / (t log t)`.  This is the previously missing algebraic binding
between the source normalization and the physical observable.
-/
theorem q073_normalizedSecondMoment_eq_msd_div_time_log
    {Ω : Type*} [MeasurableSpace Ω]
    (process : Q073DisplacementProcess Ω)
    (t : ℝ)
    (ht : 1 < t) :
    q073_normalizedSecondMoment process t =
      q073_meanSquareDisplacement process t / (t * Real.log t) := by
  let scale : ℝ := (q073_lorentz_normalization t)⁻¹
  have hMeasurable :
      Measurable (q073_normalizedDisplacement process t) :=
    q073_normalizedDisplacement_measurable process t
  have hScalePos : 0 < scale := by
    exact inv_pos.mpr (q073_lorentz_normalization_pos ht)
  have hScaleSq :
      scale ^ 2 = (t * Real.log t)⁻¹ := by
    dsimp [scale]
    rw [inv_pow, q073_lorentz_normalization_sq ht]
  unfold q073_normalizedSecondMoment q073_normalizedDisplacementLaw
  rw [ProbabilityMeasure.toMeasure_map]
  rw [integral_map_of_stronglyMeasurable
    hMeasurable
    (continuous_norm.pow 2).stronglyMeasurable]
  change
    (∫ ω, ‖scale • process.displacement t ω‖ ^ 2
      ∂(process.initialLaw : Measure Ω)) =
      q073_meanSquareDisplacement process t / (t * Real.log t)
  have hPointwise :
      (fun ω => ‖scale • process.displacement t ω‖ ^ 2) =
        fun ω => scale ^ 2 * ‖process.displacement t ω‖ ^ 2 := by
    funext ω
    rw [norm_smul, Real.norm_eq_abs, abs_of_pos hScalePos]
    ring
  rw [hPointwise, integral_const_mul, hScaleSq]
  unfold q073_meanSquareDisplacement
  rw [div_eq_mul_inv, mul_comm]

/--
The physical finite-time coefficient is eventually the normalized second
moment times `log t / 4`.  The equality is intentionally eventual rather than
asserted at the nonphysical points `t ≤ 1`.
-/
theorem q073_effectiveDiffusion_eventually_eq_scaled_normalizedSecondMoment
    {Ω : Type*} [MeasurableSpace Ω]
    (process : Q073DisplacementProcess Ω) :
    q073_effectiveDiffusion process =ᶠ[atTop]
      (fun t =>
        q073_normalizedSecondMoment process t * Real.log t / 4) := by
  filter_upwards [eventually_gt_atTop (1 : ℝ)] with t ht
  rw [q073_effectiveDiffusion_eq_msd_div_four_time,
    q073_normalizedSecondMoment_eq_msd_div_time_log process t ht]
  have ht0 : t ≠ 0 := ne_of_gt (zero_lt_one.trans ht)
  have hlog0 : Real.log t ≠ 0 := ne_of_gt (Real.log_pos ht)
  field_simp

/--
The honest physical Q073 consequence.

The external source theorem must supply `hWeak` and the nondegenerate-limit
premise; the process instantiation must separately discharge
`hMomentFinite`.  Conditional on those explicit premises, every algebraic and
measure-theoretic step from the actual displacement law to
`D_eff = MSD/(4t)` and then to nonexistence of a finite ordinary coefficient is
mechanized here or in `Q073PortmanteauMomentBridge`.
-/
theorem q073_lorentz_no_finite_ordinary_coefficient
    {Ω : Type*} [MeasurableSpace Ω]
    (process : Q073DisplacementProcess Ω)
    {μLimit : ProbabilityMeasure Q073Plane}
    (hWeak :
      Tendsto
        (q073_normalizedDisplacementLaw process)
        atTop
        (𝓝 μLimit))
    (hNondegenerate :
      0 < (μLimit : Measure Q073Plane) ({0}ᶜ))
    (hMomentFinite :
      ∀ t,
        Integrable
          (fun x : Q073Plane => ‖x‖ ^ 2)
          (q073_normalizedDisplacementLaw process t :
            Measure Q073Plane)) :
    ¬ ∃ finiteCoefficient : ℝ,
      Tendsto
        (q073_effectiveDiffusion process)
        atTop
        (𝓝 finiteCoefficient) := by
  let normalizedMoment : ℝ → ℝ :=
    q073_normalizedSecondMoment process
  let lawCoefficient : ℝ → ℝ :=
    fun t => normalizedMoment t * Real.log t / 4
  have hTruncationDominated :
      ∀ t,
        ∫ x, q073_squared_norm_truncation Q073Plane x
            ∂(q073_normalizedDisplacementLaw process t :
              Measure Q073Plane) ≤
          normalizedMoment t := by
    intro t
    exact q073_truncation_integral_le_normalizedSecondMoment
      process t (hMomentFinite t)
  have hLawRejectsFinite :
      ¬ ∃ finiteCoefficient : ℝ,
        Tendsto lawCoefficient atTop (𝓝 finiteCoefficient) := by
    exact
      q073_weak_nondegenerate_limit_rejects_finite_ordinary_diffusion_coefficient
        hWeak hNondegenerate normalizedMoment lawCoefficient
        hTruncationDominated (fun _ => rfl)
  intro hFinite
  obtain ⟨finiteCoefficient, hEffectiveFinite⟩ := hFinite
  apply hLawRejectsFinite
  refine ⟨finiteCoefficient, ?_⟩
  apply hEffectiveFinite.congr'
  exact
    q073_effectiveDiffusion_eventually_eq_scaled_normalizedSecondMoment
      process

end OCMinimalObligationSpine
