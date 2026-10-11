/-!
Q040 topological-denominator arithmetic kernel.

This file intentionally formalizes only the small algebraic consequence used by
the topology package:

* if the Euler class of `TS^6` is `2u`, and
* a degree-one map pulls `u` back to the top generator,

then the pulled Euler-class coefficient is non-zero.

It is not a Lean formalization of the full bundle construction, and it is not a
curvature metric construction for AIM Problem 40.
-/

namespace OCMinimalObligationSpine

universe u

/-- Coefficient of the pulled-back top Euler class in the chosen generator. -/
def q040PulledEulerCoefficient (degree sphereEulerCoefficient : Int) : Int :=
  sphereEulerCoefficient * degree

/-- For `degree = 1` and `e(TS^6)=2u`, the pulled-back Euler coefficient is `2`. -/
theorem q040_degree_one_sphere_six_euler_coeff :
    q040PulledEulerCoefficient 1 2 = 2 := by
  rfl

/-- Therefore the denominator bundle has non-zero Euler coefficient. -/
theorem q040_degree_one_sphere_six_euler_nonzero :
    q040PulledEulerCoefficient 1 2 ≠ 0 := by
  decide

/--
Predicate bundle for the full Q040 target.

`Candidate` is an encoded total space / bundle candidate for an oriented real
rank-six vector bundle over `S^3 × S^3`.  The topology denominator proves that
non-trivial Euler-class candidates exist, but Q040 is a curvature question:
closure requires either a complete `sec ≥ 0` metric on such a non-trivial
candidate or a source-exact obstruction for all admitted candidates.
-/
structure Q040RankSixBundleDomain where
  Candidate : Type u
  rankSixBundleOverS3xS3 : Candidate → Prop
  nontrivialEulerClass : Candidate → Prop
  admitsCompleteNonnegativeSectionalCurvatureMetric : Candidate → Prop
  productSoulMetric : Candidate → Prop
  wilking_product_soul_no_go :
    ∀ E : Candidate,
      rankSixBundleOverS3xS3 E →
      nontrivialEulerClass E →
      productSoulMetric E →
      ¬ admitsCompleteNonnegativeSectionalCurvatureMetric E

/-- The full AIM Q040 positive target, not a topology-only denominator. -/
def Q040FullPositiveTarget (D : Q040RankSixBundleDomain.{u}) : Prop :=
  ∃ E : D.Candidate,
    D.rankSixBundleOverS3xS3 E ∧
    D.nontrivialEulerClass E ∧
    D.admitsCompleteNonnegativeSectionalCurvatureMetric E

/-- Direct positive construction payload for the frozen Q040 target. -/
structure Q040DirectPositiveConstruction (D : Q040RankSixBundleDomain.{u}) where
  E : D.Candidate
  rank_six_bundle : D.rankSixBundleOverS3xS3 E
  nontrivial_euler : D.nontrivialEulerClass E
  complete_sec_nonnegative_metric :
    D.admitsCompleteNonnegativeSectionalCurvatureMetric E

/-- A direct metric construction closes the full positive Q040 target. -/
theorem q040_full_target_of_direct_positive_construction
    {D : Q040RankSixBundleDomain.{u}}
    (C : Q040DirectPositiveConstruction D) :
    Q040FullPositiveTarget D := by
  exact
    ⟨C.E,
      C.rank_six_bundle,
      C.nontrivial_euler,
      C.complete_sec_nonnegative_metric⟩

/-- Direct obstruction payload for a negative answer to the frozen Q040 target. -/
structure Q040DirectObstruction (D : Q040RankSixBundleDomain.{u}) where
  no_complete_sec_nonnegative_metric :
    ∀ E : D.Candidate,
      D.rankSixBundleOverS3xS3 E →
      D.nontrivialEulerClass E →
      ¬ D.admitsCompleteNonnegativeSectionalCurvatureMetric E

/-- A direct obstruction refutes the full positive Q040 target. -/
theorem q040_no_full_target_of_direct_obstruction
    {D : Q040RankSixBundleDomain.{u}}
    (O : Q040DirectObstruction D) :
    ¬ Q040FullPositiveTarget D := by
  intro h
  rcases h with ⟨E, h_rank, h_euler, h_metric⟩
  exact O.no_complete_sec_nonnegative_metric E h_rank h_euler h_metric

/-- Topological denominator: a non-trivial Euler rank-six bundle candidate exists. -/
structure Q040TopologicalDenominator (D : Q040RankSixBundleDomain.{u}) where
  E : D.Candidate
  rank_six_bundle : D.rankSixBundleOverS3xS3 E
  nontrivial_euler : D.nontrivialEulerClass E

/--
A topology denominator becomes a positive Q040 construction only after the
complete nonnegative-curvature metric payload is supplied on that same bundle.
-/
structure Q040MetricPayloadForTopologicalDenominator
    (D : Q040RankSixBundleDomain.{u}) where
  denominator : Q040TopologicalDenominator D
  complete_sec_nonnegative_metric :
    D.admitsCompleteNonnegativeSectionalCurvatureMetric denominator.E

/-- A metric payload for the denominator is exactly a direct positive construction. -/
def q040_direct_positive_construction_of_metric_payload
    {D : Q040RankSixBundleDomain.{u}}
    (P : Q040MetricPayloadForTopologicalDenominator D) :
    Q040DirectPositiveConstruction D where
  E := P.denominator.E
  rank_six_bundle := P.denominator.rank_six_bundle
  nontrivial_euler := P.denominator.nontrivial_euler
  complete_sec_nonnegative_metric := P.complete_sec_nonnegative_metric

/-- The product-soul positive target slice governed by Wilking's source boundary. -/
def Q040ProductSoulPositiveTarget (D : Q040RankSixBundleDomain.{u}) : Prop :=
  ∃ E : D.Candidate,
    D.rankSixBundleOverS3xS3 E ∧
    D.nontrivialEulerClass E ∧
    D.productSoulMetric E ∧
    D.admitsCompleteNonnegativeSectionalCurvatureMetric E

/--
Wilking's product-soul no-go blocks the product-soul slice.  It does not refute
the full frozen Q040 target unless every admitted candidate is proved to lie in
that product-soul slice.
-/
theorem q040_no_product_soul_positive_target
    {D : Q040RankSixBundleDomain.{u}} :
    ¬ Q040ProductSoulPositiveTarget D := by
  intro h
  rcases h with ⟨E, h_rank, h_euler, h_product_soul, h_metric⟩
  exact D.wilking_product_soul_no_go E h_rank h_euler h_product_soul h_metric

/--
If a direct positive construction exists, Wilking's product-soul no-go forces
that construction to be outside the product-soul-metric subclass.
-/
theorem q040_direct_positive_construction_not_product_soul_metric
    {D : Q040RankSixBundleDomain.{u}}
    (C : Q040DirectPositiveConstruction D) :
    ¬ D.productSoulMetric C.E := by
  intro h_product_soul
  exact D.wilking_product_soul_no_go C.E
    C.rank_six_bundle C.nontrivial_euler h_product_soul
    C.complete_sec_nonnegative_metric

/--
If all admitted rank-six non-trivial Euler candidates in a restricted domain
are product-soul-metric candidates, Wilking's boundary theorem promotes to a
direct obstruction for that restricted domain.
-/
theorem q040_direct_obstruction_of_product_soul_reduction
    {D : Q040RankSixBundleDomain.{u}}
    (all_admitted_candidates_product_soul :
      ∀ E : D.Candidate,
        D.rankSixBundleOverS3xS3 E →
        D.nontrivialEulerClass E →
        D.productSoulMetric E) :
    Q040DirectObstruction D := by
  refine ⟨?_⟩
  intro E h_rank h_euler h_metric
  exact D.wilking_product_soul_no_go E h_rank h_euler
    (all_admitted_candidates_product_soul E h_rank h_euler)
    h_metric

/--
The next research payload is a disjunction of the two honest terminal routes:
construct a complete nonnegative-curvature metric on a non-trivial Euler
rank-six bundle, or prove a direct obstruction for all admitted candidates.
-/
def Q040TerminalPayload (D : Q040RankSixBundleDomain.{u}) : Prop :=
  Nonempty (Q040DirectPositiveConstruction D) ∨
  Nonempty (Q040DirectObstruction D)

/--
Any terminal Q040 payload decides the frozen full target: a direct construction
proves the target, while a direct obstruction refutes it.
-/
theorem q040_full_target_decided_by_terminal_payload
    {D : Q040RankSixBundleDomain.{u}}
    (P : Q040TerminalPayload D) :
    Q040FullPositiveTarget D ∨ ¬ Q040FullPositiveTarget D := by
  rcases P with h_positive | h_negative
  · rcases h_positive with ⟨C⟩
    exact Or.inl (q040_full_target_of_direct_positive_construction C)
  · rcases h_negative with ⟨O⟩
    exact Or.inr (q040_no_full_target_of_direct_obstruction O)

end OCMinimalObligationSpine
