import Mathlib.Data.Set.Basic

namespace OCMinimalObligationSpine

universe u

/-!
Q023 principal two-torus positive-curvature closure gate.

The AIM target is the full statement:

  There exists a principal `T^2`-bundle whose total space admits `sec > 0`.

This file intentionally keeps that target intact.  A nonnegative-curvature
successor, an almost-positive/quasi-positive metric, or a positive quotient
shadow is not a renamed closure.  Such evidence is useful only after the
missing total-space positive-curvature payload is supplied, or after a genuine
obstruction proves that no such total space exists.
-/

/--
Predicate bundle for an encoded Q023 candidate.

`Candidate` is an abstract total-space candidate.  The geometry is represented
by predicates so the release machine can enforce the exact AIM boundary without
pretending that a Riemannian metric construction has already been formalized in
mathlib.
-/
structure Q023PrincipalTorusBundleDomain where
  Candidate : Type u
  principalT2BundleTotalSpace : Candidate → Prop
  admitsPositiveSectionalCurvatureMetric : Candidate → Prop
  admitsNonnegativeSectionalCurvatureMetric : Candidate → Prop
  hasFlatTwoPlane : Candidate → Prop
  quotientOrBiquotientShadow : Candidate → Prop
  shadowTransferredToPrincipalTotalSpace : Candidate → Prop
  flatPlaneBlocksPositive :
    ∀ E : Candidate,
      hasFlatTwoPlane E →
      ¬ admitsPositiveSectionalCurvatureMetric E

/-- The full AIM Q023 positive target, not a successor or downgraded claim. -/
def Q023FullPositiveTarget (D : Q023PrincipalTorusBundleDomain.{u}) : Prop :=
  ∃ E : D.Candidate,
    D.principalT2BundleTotalSpace E ∧
    D.admitsPositiveSectionalCurvatureMetric E

/-- Direct positive construction payload for the full frozen target. -/
structure Q023DirectPositiveConstruction (D : Q023PrincipalTorusBundleDomain.{u}) where
  E : D.Candidate
  principal_total_space : D.principalT2BundleTotalSpace E
  sec_positive_metric : D.admitsPositiveSectionalCurvatureMetric E

/-- A direct total-space `sec > 0` construction closes the full Q023 target. -/
theorem q023_full_target_of_direct_positive_construction
    {D : Q023PrincipalTorusBundleDomain.{u}}
    (C : Q023DirectPositiveConstruction D) :
    Q023FullPositiveTarget D := by
  exact ⟨C.E, C.principal_total_space, C.sec_positive_metric⟩

/-- Direct obstruction payload for a negative answer to the full frozen target. -/
structure Q023DirectObstruction (D : Q023PrincipalTorusBundleDomain.{u}) where
  no_positive_principal_total_space :
    ∀ E : D.Candidate,
      D.principalT2BundleTotalSpace E →
      ¬ D.admitsPositiveSectionalCurvatureMetric E

/-- A direct obstruction refutes the full positive target. -/
theorem q023_no_full_target_of_direct_obstruction
    {D : Q023PrincipalTorusBundleDomain.{u}}
    (O : Q023DirectObstruction D) :
    ¬ Q023FullPositiveTarget D := by
  intro h
  rcases h with ⟨E, h_principal, h_positive⟩
  exact O.no_positive_principal_total_space E h_principal h_positive

/--
Nonnegative successor data, e.g. a product-Hopf-type boundary example.

This is valuable evidence, but it is deliberately not the full positive target
when a flat two-plane remains.
-/
structure Q023NonnegativeBoundaryExample (D : Q023PrincipalTorusBundleDomain.{u}) where
  E : D.Candidate
  principal_total_space : D.principalT2BundleTotalSpace E
  sec_nonnegative_metric : D.admitsNonnegativeSectionalCurvatureMetric E
  flat_two_plane : D.hasFlatTwoPlane E

/--
A nonnegative principal `T^2` total space with a flat two-plane is not a
positive-curvature closure for that candidate.
-/
theorem q023_nonnegative_boundary_example_blocks_candidate_positive
    {D : Q023PrincipalTorusBundleDomain.{u}}
    (B : Q023NonnegativeBoundaryExample D) :
    ¬ D.admitsPositiveSectionalCurvatureMetric B.E := by
  exact D.flatPlaneBlocksPositive B.E B.flat_two_plane

/--
Positive quotient/biquotient shadow data.

The shadow can become a Q023 closure only after it is transferred back to a
principal `T^2`-bundle total space with positive sectional curvature.
-/
structure Q023QuotientShadowData (D : Q023PrincipalTorusBundleDomain.{u}) where
  E : D.Candidate
  quotient_shadow : D.quotientOrBiquotientShadow E

/-- The exact promotion obligation for a quotient/biquotient shadow. -/
def Q023ShadowPromotionObligation
    (D : Q023PrincipalTorusBundleDomain.{u})
    (S : Q023QuotientShadowData D) : Prop :=
  D.shadowTransferredToPrincipalTotalSpace S.E ∧
  D.principalT2BundleTotalSpace S.E ∧
  D.admitsPositiveSectionalCurvatureMetric S.E

/--
A quotient/biquotient shadow closes Q023 only after the total-space transfer
and strict positive-curvature metric are supplied.
-/
theorem q023_full_target_of_promoted_shadow
    {D : Q023PrincipalTorusBundleDomain.{u}}
    (S : Q023QuotientShadowData D)
    (H : Q023ShadowPromotionObligation D S) :
    Q023FullPositiveTarget D := by
  rcases H with ⟨_h_transfer, h_principal, h_positive⟩
  exact ⟨S.E, h_principal, h_positive⟩

/--
Four-dimensional Euler-characteristic obstruction data.

This is a bounded but genuine no-go slice for Q023: if a candidate is a compact
four-dimensional principal `T^2` total space, the torus-bundle/fibration lane
forces Euler characteristic zero, while positive sectional curvature in the
four-dimensional Chern-Gauss-Bonnet lane forces positive Euler characteristic.
Those two certificates are incompatible.

The obstruction deliberately prunes only the four-dimensional candidate lane;
it is not a refutation of the unrestricted AIM target.
-/
structure Q023FourDimensionalEulerObstructionData
    (D : Q023PrincipalTorusBundleDomain.{u}) where
  compactFourDimensionalCandidate : D.Candidate → Prop
  zeroEulerCharacteristic : D.Candidate → Prop
  positiveEulerCharacteristic : D.Candidate → Prop
  principal_torus_four_dimensional_forces_zero_euler :
    ∀ E : D.Candidate,
      D.principalT2BundleTotalSpace E →
      compactFourDimensionalCandidate E →
      zeroEulerCharacteristic E
  positive_curvature_four_dimensional_forces_positive_euler :
    ∀ E : D.Candidate,
      compactFourDimensionalCandidate E →
      D.admitsPositiveSectionalCurvatureMetric E →
      positiveEulerCharacteristic E
  zero_euler_contradicts_positive_euler :
    ∀ E : D.Candidate,
      zeroEulerCharacteristic E →
      positiveEulerCharacteristic E →
      False

/--
The compact four-dimensional principal `T^2` total-space lane cannot supply the
Q023 positive construction.
-/
theorem q023_four_dimensional_principal_torus_total_space_no_positive
    {D : Q023PrincipalTorusBundleDomain.{u}}
    (O : Q023FourDimensionalEulerObstructionData D) :
    ∀ E : D.Candidate,
      D.principalT2BundleTotalSpace E →
      O.compactFourDimensionalCandidate E →
      ¬ D.admitsPositiveSectionalCurvatureMetric E := by
  intro E h_principal h_four h_positive
  exact O.zero_euler_contradicts_positive_euler E
    (O.principal_torus_four_dimensional_forces_zero_euler E h_principal h_four)
    (O.positive_curvature_four_dimensional_forces_positive_euler E h_four h_positive)

/--
If every admitted Q023 candidate is forced into the compact four-dimensional
lane, the four-dimensional Euler obstruction becomes a direct obstruction for
that restricted domain.
-/
theorem q023_direct_obstruction_of_all_candidates_four_dimensional
    {D : Q023PrincipalTorusBundleDomain.{u}}
    (O : Q023FourDimensionalEulerObstructionData D)
    (all_principal_candidates_four_dimensional :
      ∀ E : D.Candidate,
        D.principalT2BundleTotalSpace E →
        O.compactFourDimensionalCandidate E) :
    Q023DirectObstruction D := by
  refine ⟨?_⟩
  intro E h_principal
  exact q023_four_dimensional_principal_torus_total_space_no_positive O E
    h_principal
    (all_principal_candidates_four_dimensional E h_principal)

/--
Even-dimensional invariant-metric obstruction data.

This is the next honest Q023 pruning lane.  If the positive metric is required
to be invariant under the free principal `T^2` action, then an infinitesimal
circle subgroup supplies a nowhere-zero Killing field.  Berger's fixed-point
theorem for compact even-dimensional positive-curvature manifolds says that
such a Killing field must have a zero.  Hence an invariant positive metric
cannot close the even-dimensional principal `T^2` lane.

The obstruction is deliberately scoped to invariant metrics.  The unrestricted
AIM target asks only that the total space admit some positive metric, so a
non-invariant higher-dimensional construction is not ruled out by this theorem.
-/
structure Q023EvenDimensionalInvariantMetricObstructionData
    (D : Q023PrincipalTorusBundleDomain.{u}) where
  compactEvenDimensionalCandidate : D.Candidate → Prop
  principalT2InvariantPositiveMetric : D.Candidate → Prop
  nowhereZeroPrincipalKillingField : D.Candidate → Prop
  everyKillingFieldHasZero : D.Candidate → Prop
  invariant_metric_is_positive :
    ∀ E : D.Candidate,
      principalT2InvariantPositiveMetric E →
      D.admitsPositiveSectionalCurvatureMetric E
  principal_invariant_metric_gives_nowhere_zero_killing :
    ∀ E : D.Candidate,
      D.principalT2BundleTotalSpace E →
      compactEvenDimensionalCandidate E →
      principalT2InvariantPositiveMetric E →
      nowhereZeroPrincipalKillingField E
  berger_positive_even_forces_killing_zero :
    ∀ E : D.Candidate,
      compactEvenDimensionalCandidate E →
      D.admitsPositiveSectionalCurvatureMetric E →
      everyKillingFieldHasZero E
  nowhere_zero_contradicts_every_zero :
    ∀ E : D.Candidate,
      nowhereZeroPrincipalKillingField E →
      everyKillingFieldHasZero E →
      False

/-- The even-dimensional invariant-positive-metric target slice. -/
def Q023EvenDimensionalInvariantPositiveTarget
    (D : Q023PrincipalTorusBundleDomain.{u})
    (I : Q023EvenDimensionalInvariantMetricObstructionData D) : Prop :=
  ∃ E : D.Candidate,
    D.principalT2BundleTotalSpace E ∧
    I.compactEvenDimensionalCandidate E ∧
    I.principalT2InvariantPositiveMetric E

/--
No compact even-dimensional principal `T^2` total space can close Q023 through a
positive metric invariant under the principal torus action.
-/
theorem q023_no_even_dimensional_principal_torus_invariant_positive_target
    {D : Q023PrincipalTorusBundleDomain.{u}}
    (I : Q023EvenDimensionalInvariantMetricObstructionData D) :
    ¬ Q023EvenDimensionalInvariantPositiveTarget D I := by
  intro h
  rcases h with ⟨E, h_principal, h_even, h_invariant_positive⟩
  exact I.nowhere_zero_contradicts_every_zero E
    (I.principal_invariant_metric_gives_nowhere_zero_killing E
      h_principal h_even h_invariant_positive)
    (I.berger_positive_even_forces_killing_zero E h_even
      (I.invariant_metric_is_positive E h_invariant_positive))

/--
If a restricted admitted domain proves both that every principal candidate is
compact even-dimensional and that every positive metric can be promoted to a
principal-invariant positive metric, then the invariant-metric obstruction
becomes a direct obstruction for that restricted domain.
-/
theorem q023_direct_obstruction_of_even_dimensional_invariant_metric_reduction
    {D : Q023PrincipalTorusBundleDomain.{u}}
    (I : Q023EvenDimensionalInvariantMetricObstructionData D)
    (all_principal_candidates_even :
      ∀ E : D.Candidate,
        D.principalT2BundleTotalSpace E →
        I.compactEvenDimensionalCandidate E)
    (all_positive_metrics_principal_invariant :
      ∀ E : D.Candidate,
        D.principalT2BundleTotalSpace E →
        D.admitsPositiveSectionalCurvatureMetric E →
        I.principalT2InvariantPositiveMetric E) :
    Q023DirectObstruction D := by
  refine ⟨?_⟩
  intro E h_principal h_positive
  exact I.nowhere_zero_contradicts_every_zero E
    (I.principal_invariant_metric_gives_nowhere_zero_killing E
      h_principal
      (all_principal_candidates_even E h_principal)
      (all_positive_metrics_principal_invariant E h_principal h_positive))
    (I.berger_positive_even_forces_killing_zero E
      (all_principal_candidates_even E h_principal)
      h_positive)

/--
General principal-invariant metric obstruction data.

Sugahara's commuting-Killing-field strengthening removes the even-dimensional
restriction from the invariant metric lane: on a closed positive sectional
curvature manifold, any two commuting Killing fields become linearly dependent
somewhere.  A free principal `T^2` action whose metric is invariant supplies two
fundamental commuting Killing fields that must remain independent everywhere.

Therefore a principal-torus-invariant positive metric is not a lawful Q023
construction route in any dimension.  The unrestricted Q023 target is still not
lowered, because it asks for some positive metric on the total space, not
necessarily one invariant under the principal torus action.
-/
structure Q023InvariantTorusActionObstructionData
    (D : Q023PrincipalTorusBundleDomain.{u}) where
  closedCandidate : D.Candidate → Prop
  principalT2InvariantPositiveMetric : D.Candidate → Prop
  principalFundamentalFieldsEverywhereIndependent : D.Candidate → Prop
  commutingKillingFieldsDependentSomewhere : D.Candidate → Prop
  invariant_metric_is_positive :
    ∀ E : D.Candidate,
      principalT2InvariantPositiveMetric E →
      D.admitsPositiveSectionalCurvatureMetric E
  free_principal_invariant_metric_gives_everywhere_independent_fields :
    ∀ E : D.Candidate,
      D.principalT2BundleTotalSpace E →
      closedCandidate E →
      principalT2InvariantPositiveMetric E →
      principalFundamentalFieldsEverywhereIndependent E
  sugahara_positive_curvature_forces_commuting_dependence :
    ∀ E : D.Candidate,
      closedCandidate E →
      D.admitsPositiveSectionalCurvatureMetric E →
      commutingKillingFieldsDependentSomewhere E
  everywhere_independent_contradicts_dependent_somewhere :
    ∀ E : D.Candidate,
      principalFundamentalFieldsEverywhereIndependent E →
      commutingKillingFieldsDependentSomewhere E →
      False

/-- The principal-invariant positive metric target slice in any dimension. -/
def Q023InvariantPositiveTarget
    (D : Q023PrincipalTorusBundleDomain.{u})
    (I : Q023InvariantTorusActionObstructionData D) : Prop :=
  ∃ E : D.Candidate,
    D.principalT2BundleTotalSpace E ∧
    I.closedCandidate E ∧
    I.principalT2InvariantPositiveMetric E

/--
No closed principal `T^2` total space can close Q023 by a positive metric
invariant under the principal torus action.
-/
theorem q023_no_principal_torus_invariant_positive_target
    {D : Q023PrincipalTorusBundleDomain.{u}}
    (I : Q023InvariantTorusActionObstructionData D) :
    ¬ Q023InvariantPositiveTarget D I := by
  intro h
  rcases h with ⟨E, h_principal, h_closed, h_invariant_positive⟩
  exact I.everywhere_independent_contradicts_dependent_somewhere E
    (I.free_principal_invariant_metric_gives_everywhere_independent_fields E
      h_principal h_closed h_invariant_positive)
    (I.sugahara_positive_curvature_forces_commuting_dependence E h_closed
      (I.invariant_metric_is_positive E h_invariant_positive))

/--
If a restricted admitted domain proves that every positive metric can be
promoted to a principal-invariant positive metric on a closed candidate, then
the invariant-torus-action obstruction becomes a direct obstruction for that
restricted domain.
-/
theorem q023_direct_obstruction_of_principal_invariant_metric_reduction
    {D : Q023PrincipalTorusBundleDomain.{u}}
    (I : Q023InvariantTorusActionObstructionData D)
    (all_principal_candidates_closed :
      ∀ E : D.Candidate,
        D.principalT2BundleTotalSpace E →
        I.closedCandidate E)
    (all_positive_metrics_principal_invariant :
      ∀ E : D.Candidate,
        D.principalT2BundleTotalSpace E →
        D.admitsPositiveSectionalCurvatureMetric E →
        I.principalT2InvariantPositiveMetric E) :
    Q023DirectObstruction D := by
  refine ⟨?_⟩
  intro E h_principal h_positive
  exact I.everywhere_independent_contradicts_dependent_somewhere E
    (I.free_principal_invariant_metric_gives_everywhere_independent_fields E
      h_principal
      (all_principal_candidates_closed E h_principal)
      (all_positive_metrics_principal_invariant E h_principal h_positive))
    (I.sugahara_positive_curvature_forces_commuting_dependence E
      (all_principal_candidates_closed E h_principal)
      h_positive)

/--
Fundamental-group obstruction data.

This is a topology-first Q023 pruning lane.  A strict sectional-curvature
positive metric gives a positive Ricci lower bound; by Bonnet--Myers, a closed
complete positive-curvature candidate must have finite fundamental group.  Thus
any principal `T^2` total-space candidate whose homotopy exact sequence leaves
an infinite fundamental group cannot be the requested Q023 positive example.

This does not lower the Q023 target.  It tells the constructive search that a
lawful positive candidate must pass the finite-`π₁` screen; in the common
simply connected base case, the boundary/transgression data must kill both
torus generators rather than leaving a rank-deficient infinite quotient.
-/
structure Q023FundamentalGroupObstructionData
    (D : Q023PrincipalTorusBundleDomain.{u}) where
  closedCompleteCandidate : D.Candidate → Prop
  finiteFundamentalGroup : D.Candidate → Prop
  infiniteFundamentalGroup : D.Candidate → Prop
  positive_sectional_curvature_forces_finite_pi1 :
    ∀ E : D.Candidate,
      closedCompleteCandidate E →
      D.admitsPositiveSectionalCurvatureMetric E →
      finiteFundamentalGroup E
  infinite_pi1_contradicts_finite_pi1 :
    ∀ E : D.Candidate,
      infiniteFundamentalGroup E →
      finiteFundamentalGroup E →
      False

/-- The infinite-`π₁` positive target slice blocked by Bonnet--Myers. -/
def Q023InfinitePi1PositiveTarget
    (D : Q023PrincipalTorusBundleDomain.{u})
    (P : Q023FundamentalGroupObstructionData D) : Prop :=
  ∃ E : D.Candidate,
    D.principalT2BundleTotalSpace E ∧
    P.closedCompleteCandidate E ∧
    P.infiniteFundamentalGroup E ∧
    D.admitsPositiveSectionalCurvatureMetric E

/--
No closed complete principal `T^2` total space with infinite fundamental group
can be the strict positive-curvature Q023 example.
-/
theorem q023_no_infinite_pi1_positive_target
    {D : Q023PrincipalTorusBundleDomain.{u}}
    (P : Q023FundamentalGroupObstructionData D) :
    ¬ Q023InfinitePi1PositiveTarget D P := by
  intro h
  rcases h with ⟨E, _h_principal, h_closed_complete, h_infinite_pi1, h_positive⟩
  exact P.infinite_pi1_contradicts_finite_pi1 E h_infinite_pi1
    (P.positive_sectional_curvature_forces_finite_pi1 E h_closed_complete h_positive)

/--
If every admitted principal candidate in a restricted domain is closed complete
and has infinite fundamental group, Bonnet--Myers promotes the finite-`π₁`
screen to a direct obstruction for that restricted domain.
-/
theorem q023_direct_obstruction_of_infinite_pi1_domain
    {D : Q023PrincipalTorusBundleDomain.{u}}
    (P : Q023FundamentalGroupObstructionData D)
    (all_principal_candidates_closed_complete :
      ∀ E : D.Candidate,
        D.principalT2BundleTotalSpace E →
        P.closedCompleteCandidate E)
    (all_principal_candidates_infinite_pi1 :
      ∀ E : D.Candidate,
        D.principalT2BundleTotalSpace E →
        P.infiniteFundamentalGroup E) :
    Q023DirectObstruction D := by
  refine ⟨?_⟩
  intro E h_principal h_positive
  exact P.infinite_pi1_contradicts_finite_pi1 E
    (all_principal_candidates_infinite_pi1 E h_principal)
    (P.positive_sectional_curvature_forces_finite_pi1 E
      (all_principal_candidates_closed_complete E h_principal)
      h_positive)

/--
Homotopy exact-sequence rank-deficiency data for principal `T^2` candidates.

For a principal `T^2 -> E -> B` lane with simply connected base, the low-degree
homotopy exact sequence has the form
`π₂(B) -> π₁(T²) -> π₁(E) -> 0`.
If the boundary/transgression image fails to have full rank in `π₁(T²) ≅ Z²`,
then an infinite quotient survives in `π₁(E)`.  That candidate is then blocked
by the Bonnet--Myers finite-`π₁` screen above.
-/
structure Q023TorusLESRankDeficiencyData
    (D : Q023PrincipalTorusBundleDomain.{u})
    (P : Q023FundamentalGroupObstructionData D) where
  simplyConnectedBaseCandidate : D.Candidate → Prop
  rankDeficientBoundaryMap : D.Candidate → Prop
  rank_deficient_boundary_map_gives_infinite_pi1 :
    ∀ E : D.Candidate,
      D.principalT2BundleTotalSpace E →
      simplyConnectedBaseCandidate E →
      rankDeficientBoundaryMap E →
      P.infiniteFundamentalGroup E

/-- The rank-deficient low-degree homotopy sequence target slice. -/
def Q023RankDeficientBoundaryPositiveTarget
    (D : Q023PrincipalTorusBundleDomain.{u})
    (P : Q023FundamentalGroupObstructionData D)
    (L : Q023TorusLESRankDeficiencyData D P) : Prop :=
  ∃ E : D.Candidate,
    D.principalT2BundleTotalSpace E ∧
    P.closedCompleteCandidate E ∧
    L.simplyConnectedBaseCandidate E ∧
    L.rankDeficientBoundaryMap E ∧
    D.admitsPositiveSectionalCurvatureMetric E

/--
In the simply connected base lane, a rank-deficient `π₂(B) -> π₁(T²)` boundary
map leaves infinite `π₁(E)`, so Bonnet--Myers blocks strict positive curvature.
-/
theorem q023_no_rank_deficient_boundary_positive_target
    {D : Q023PrincipalTorusBundleDomain.{u}}
    {P : Q023FundamentalGroupObstructionData D}
    (L : Q023TorusLESRankDeficiencyData D P) :
    ¬ Q023RankDeficientBoundaryPositiveTarget D P L := by
  intro h
  rcases h with
    ⟨E, h_principal, h_closed_complete, h_base_simply_connected,
      h_rank_deficient, h_positive⟩
  exact P.infinite_pi1_contradicts_finite_pi1 E
    (L.rank_deficient_boundary_map_gives_infinite_pi1 E
      h_principal h_base_simply_connected h_rank_deficient)
    (P.positive_sectional_curvature_forces_finite_pi1 E
      h_closed_complete h_positive)

/--
If a restricted domain consists only of closed complete principal `T^2` total
spaces over simply connected bases with rank-deficient boundary map, the
homotopy exact-sequence screen promotes to a direct obstruction for that domain.
-/
theorem q023_direct_obstruction_of_rank_deficient_boundary_domain
    {D : Q023PrincipalTorusBundleDomain.{u}}
    {P : Q023FundamentalGroupObstructionData D}
    (L : Q023TorusLESRankDeficiencyData D P)
    (all_principal_candidates_closed_complete :
      ∀ E : D.Candidate,
        D.principalT2BundleTotalSpace E →
        P.closedCompleteCandidate E)
    (all_principal_candidates_simply_connected_base :
      ∀ E : D.Candidate,
        D.principalT2BundleTotalSpace E →
        L.simplyConnectedBaseCandidate E)
    (all_principal_candidates_rank_deficient :
      ∀ E : D.Candidate,
        D.principalT2BundleTotalSpace E →
        L.rankDeficientBoundaryMap E) :
    Q023DirectObstruction D := by
  refine ⟨?_⟩
  intro E h_principal h_positive
  exact P.infinite_pi1_contradicts_finite_pi1 E
    (L.rank_deficient_boundary_map_gives_infinite_pi1 E
      h_principal
      (all_principal_candidates_simply_connected_base E h_principal)
      (all_principal_candidates_rank_deficient E h_principal))
    (P.positive_sectional_curvature_forces_finite_pi1 E
      (all_principal_candidates_closed_complete E h_principal)
      h_positive)

/--
Synge fundamental-group obstruction data.

Bonnet--Myers cuts away infinite fundamental groups.  Synge sharpens the screen
in the compact even-dimensional orientable lane: positive sectional curvature
forces the manifold to be simply connected.  Thus a compact even-dimensional
orientable principal `T^2` total-space candidate with any nontrivial fundamental
group cannot be the Q023 positive example.
-/
structure Q023SyngeFundamentalGroupObstructionData
    (D : Q023PrincipalTorusBundleDomain.{u}) where
  compactEvenDimensionalOrientableCandidate : D.Candidate → Prop
  trivialFundamentalGroup : D.Candidate → Prop
  nontrivialFundamentalGroup : D.Candidate → Prop
  positive_sectional_curvature_forces_trivial_pi1 :
    ∀ E : D.Candidate,
      compactEvenDimensionalOrientableCandidate E →
      D.admitsPositiveSectionalCurvatureMetric E →
      trivialFundamentalGroup E
  nontrivial_pi1_contradicts_trivial_pi1 :
    ∀ E : D.Candidate,
      nontrivialFundamentalGroup E →
      trivialFundamentalGroup E →
      False

/-- The compact even-dimensional orientable nontrivial-`π₁` target slice. -/
def Q023SyngeNontrivialPi1PositiveTarget
    (D : Q023PrincipalTorusBundleDomain.{u})
    (S : Q023SyngeFundamentalGroupObstructionData D) : Prop :=
  ∃ E : D.Candidate,
    D.principalT2BundleTotalSpace E ∧
    S.compactEvenDimensionalOrientableCandidate E ∧
    S.nontrivialFundamentalGroup E ∧
    D.admitsPositiveSectionalCurvatureMetric E

/--
No compact even-dimensional orientable principal `T^2` total space with
nontrivial fundamental group can be the strict positive-curvature Q023 example.
-/
theorem q023_no_even_orientable_nontrivial_pi1_positive_target
    {D : Q023PrincipalTorusBundleDomain.{u}}
    (S : Q023SyngeFundamentalGroupObstructionData D) :
    ¬ Q023SyngeNontrivialPi1PositiveTarget D S := by
  intro h
  rcases h with ⟨E, _h_principal, h_even_orientable, h_nontrivial_pi1, h_positive⟩
  exact S.nontrivial_pi1_contradicts_trivial_pi1 E h_nontrivial_pi1
    (S.positive_sectional_curvature_forces_trivial_pi1 E
      h_even_orientable h_positive)

/--
If every candidate in a restricted domain is compact even-dimensional orientable
and has nontrivial fundamental group, Synge promotes to a direct obstruction for
that domain.
-/
theorem q023_direct_obstruction_of_even_orientable_nontrivial_pi1_domain
    {D : Q023PrincipalTorusBundleDomain.{u}}
    (S : Q023SyngeFundamentalGroupObstructionData D)
    (all_principal_candidates_even_orientable :
      ∀ E : D.Candidate,
        D.principalT2BundleTotalSpace E →
        S.compactEvenDimensionalOrientableCandidate E)
    (all_principal_candidates_nontrivial_pi1 :
      ∀ E : D.Candidate,
        D.principalT2BundleTotalSpace E →
        S.nontrivialFundamentalGroup E) :
    Q023DirectObstruction D := by
  refine ⟨?_⟩
  intro E h_principal h_positive
  exact S.nontrivial_pi1_contradicts_trivial_pi1 E
    (all_principal_candidates_nontrivial_pi1 E h_principal)
    (S.positive_sectional_curvature_forces_trivial_pi1 E
      (all_principal_candidates_even_orientable E h_principal)
      h_positive)

/--
Low-degree homotopy exact-sequence non-unimodular data.

For a principal `T^2 -> E -> B` over a simply connected base, full rank of
`π₂(B) -> π₁(T²)` is only the Bonnet--Myers finite-`π₁` screen.  In an even
orientable positive-curvature lane, Synge requires the quotient to be trivial.
So if the boundary image is full rank but non-unimodular, a finite nontrivial
`π₁(E)` survives and the candidate is blocked.
-/
structure Q023TorusLESNonUnimodularBoundaryData
    (D : Q023PrincipalTorusBundleDomain.{u})
    (S : Q023SyngeFundamentalGroupObstructionData D) where
  simplyConnectedBaseCandidate : D.Candidate → Prop
  nonUnimodularBoundaryMap : D.Candidate → Prop
  non_unimodular_boundary_map_gives_nontrivial_pi1 :
    ∀ E : D.Candidate,
      D.principalT2BundleTotalSpace E →
      simplyConnectedBaseCandidate E →
      nonUnimodularBoundaryMap E →
      S.nontrivialFundamentalGroup E

/-- The even-orientable simply connected base non-unimodular LES target slice. -/
def Q023NonUnimodularBoundaryPositiveTarget
    (D : Q023PrincipalTorusBundleDomain.{u})
    (S : Q023SyngeFundamentalGroupObstructionData D)
    (U : Q023TorusLESNonUnimodularBoundaryData D S) : Prop :=
  ∃ E : D.Candidate,
    D.principalT2BundleTotalSpace E ∧
    S.compactEvenDimensionalOrientableCandidate E ∧
    U.simplyConnectedBaseCandidate E ∧
    U.nonUnimodularBoundaryMap E ∧
    D.admitsPositiveSectionalCurvatureMetric E

/--
In the even-dimensional orientable simply connected base lane, a non-unimodular
boundary image leaves finite nontrivial `π₁(E)`, so Synge blocks strict positive
curvature.
-/
theorem q023_no_nonunimodular_boundary_positive_target
    {D : Q023PrincipalTorusBundleDomain.{u}}
    {S : Q023SyngeFundamentalGroupObstructionData D}
    (U : Q023TorusLESNonUnimodularBoundaryData D S) :
    ¬ Q023NonUnimodularBoundaryPositiveTarget D S U := by
  intro h
  rcases h with
    ⟨E, h_principal, h_even_orientable, h_base_simply_connected,
      h_nonunimodular, h_positive⟩
  exact S.nontrivial_pi1_contradicts_trivial_pi1 E
    (U.non_unimodular_boundary_map_gives_nontrivial_pi1 E
      h_principal h_base_simply_connected h_nonunimodular)
    (S.positive_sectional_curvature_forces_trivial_pi1 E
      h_even_orientable h_positive)

/--
If a restricted domain consists only of even orientable candidates over simply
connected bases with non-unimodular boundary image, Synge promotes the LES
screen to a direct obstruction for that domain.
-/
theorem q023_direct_obstruction_of_nonunimodular_boundary_domain
    {D : Q023PrincipalTorusBundleDomain.{u}}
    {S : Q023SyngeFundamentalGroupObstructionData D}
    (U : Q023TorusLESNonUnimodularBoundaryData D S)
    (all_principal_candidates_even_orientable :
      ∀ E : D.Candidate,
        D.principalT2BundleTotalSpace E →
        S.compactEvenDimensionalOrientableCandidate E)
    (all_principal_candidates_simply_connected_base :
      ∀ E : D.Candidate,
        D.principalT2BundleTotalSpace E →
        U.simplyConnectedBaseCandidate E)
    (all_principal_candidates_nonunimodular :
      ∀ E : D.Candidate,
        D.principalT2BundleTotalSpace E →
        U.nonUnimodularBoundaryMap E) :
    Q023DirectObstruction D := by
  refine ⟨?_⟩
  intro E h_principal h_positive
  exact S.nontrivial_pi1_contradicts_trivial_pi1 E
    (U.non_unimodular_boundary_map_gives_nontrivial_pi1 E
      h_principal
      (all_principal_candidates_simply_connected_base E h_principal)
      (all_principal_candidates_nonunimodular E h_principal))
    (S.positive_sectional_curvature_forces_trivial_pi1 E
      (all_principal_candidates_even_orientable E h_principal)
      h_positive)

/--
Connection-metric/fatness route data for Q023.

This is not a new answer to the AIM problem.  It is the source-bound contract
for one serious constructive route: a connection-metric ansatz may be promoted
to the full Q023 positive target only when the relevant Chaves--Derdzinski--
Rigas / fatness payload is supplied for the exact principal `T^2` total space.

Conversely, a failed fatness certificate prunes only the connection-metric
route.  It does not lower or rename the unrestricted Q023 claim, because an
arbitrary non-invariant positive metric could still exist until a full-domain
obstruction is proved.
-/
structure Q023ConnectionMetricFatnessData
    (D : Q023PrincipalTorusBundleDomain.{u}) where
  connectionMetricAnsatz : D.Candidate → Prop
  fatnessCertificate : D.Candidate → Prop
  fat_connection_metric_gives_positive :
    ∀ E : D.Candidate,
      D.principalT2BundleTotalSpace E →
      connectionMetricAnsatz E →
      fatnessCertificate E →
      D.admitsPositiveSectionalCurvatureMetric E
  positive_connection_metric_requires_fatness :
    ∀ E : D.Candidate,
      D.principalT2BundleTotalSpace E →
      connectionMetricAnsatz E →
      D.admitsPositiveSectionalCurvatureMetric E →
      fatnessCertificate E

/-- A fat connection-metric candidate is a direct Q023 positive construction. -/
def q023_direct_positive_construction_of_fat_connection_metric_candidate
    {D : Q023PrincipalTorusBundleDomain.{u}}
    (F : Q023ConnectionMetricFatnessData D)
    (E : D.Candidate)
    (h_principal : D.principalT2BundleTotalSpace E)
    (h_connection : F.connectionMetricAnsatz E)
    (h_fat : F.fatnessCertificate E) :
    Q023DirectPositiveConstruction D := by
  exact
    { E := E
      principal_total_space := h_principal
      sec_positive_metric :=
        F.fat_connection_metric_gives_positive E
          h_principal h_connection h_fat }

/-- The connection-metric target slice for Q023. -/
def Q023ConnectionMetricPositiveTarget
    (D : Q023PrincipalTorusBundleDomain.{u})
    (F : Q023ConnectionMetricFatnessData D) : Prop :=
  ∃ E : D.Candidate,
    D.principalT2BundleTotalSpace E ∧
    F.connectionMetricAnsatz E ∧
    D.admitsPositiveSectionalCurvatureMetric E

/--
If every exact principal `T^2` connection-metric candidate in a restricted
search lane lacks the fatness certificate, that lane is rejected.  The theorem
does not refute the unrestricted AIM target; it prevents a non-fat connection
metric from being counted as the terminal payload.
-/
theorem q023_no_connection_metric_positive_target_without_fatness
    {D : Q023PrincipalTorusBundleDomain.{u}}
    (F : Q023ConnectionMetricFatnessData D)
    (no_fat_principal_connection_candidates :
      ∀ E : D.Candidate,
        D.principalT2BundleTotalSpace E →
        F.connectionMetricAnsatz E →
        ¬ F.fatnessCertificate E) :
    ¬ Q023ConnectionMetricPositiveTarget D F := by
  intro h
  rcases h with ⟨E, h_principal, h_connection, h_positive⟩
  exact no_fat_principal_connection_candidates E h_principal h_connection
    (F.positive_connection_metric_requires_fatness E
      h_principal h_connection h_positive)

/--
The next research payload is a disjunction of the two honest terminal routes:
construct a strict total-space metric, or prove a direct obstruction.
-/
def Q023TerminalPayload (D : Q023PrincipalTorusBundleDomain.{u}) : Prop :=
  Nonempty (Q023DirectPositiveConstruction D) ∨
  Nonempty (Q023DirectObstruction D)

/--
The terminal payload decides the full frozen Q023 target without lowering it.

A positive branch supplies the exact principal `T^2` total-space strict
positive-curvature construction.  A negative branch supplies a direct
full-domain obstruction.  Boundary examples, quotient shadows, invariant-metric
no-go slices and failed fatness lanes do not enter this theorem unless they have
already been promoted to one of those terminal payloads.
-/
theorem q023_full_target_decided_by_terminal_payload
    {D : Q023PrincipalTorusBundleDomain.{u}}
    (P : Q023TerminalPayload D) :
    Q023FullPositiveTarget D ∨ ¬ Q023FullPositiveTarget D := by
  rcases P with h_positive | h_negative
  · rcases h_positive with ⟨C⟩
    exact Or.inl (q023_full_target_of_direct_positive_construction C)
  · rcases h_negative with ⟨O⟩
    exact Or.inr (q023_no_full_target_of_direct_obstruction O)

end OCMinimalObligationSpine
