namespace OCMinimalObligationSpine

universe u

/-!
Q014_Q040 Alexandrov Gauss-formula transfer skeleton.

The AIM target is not the Riemannian source theorem itself.  The target says:
for an Alexandrov ambient space `X`, a convex hypersurface `Y` with its induced
intrinsic metric should inherit the same lower curvature bound.

This file formalizes the two honest positive routes:

* a direct synthetic Alexandrov transfer proof;
* a controlled reduction to a proved Riemannian source slice, plus stability of
  the hypersurface lower-curvature bound under the induced-metric limit.

The point is constructive governance for the research machine: the full claim
is obtained by proving one of these routes, not by renaming a source-slice
theorem.
-/

/--
Predicate bundle for one encoded Q014 ambient/hypersurface instance.

An element of `Instance` should be read as a candidate pair `(X,Y)` with all
metadata needed by the Q014 proof lane: source category, convexity,
intrinsic-metric admissibility, ambient lower bound and hypersurface lower
bound.
-/
structure Q014GaussDomain where
  Instance : Type u
  admittedAlexandrovAmbient : Instance → Prop
  convexHypersurface : Instance → Prop
  inducedIntrinsicMetric : Instance → Prop
  ambientLowerCurvatureBound : Instance → Prop
  hypersurfaceLowerCurvatureBound : Instance → Prop

/-- The full AIM Q014 positive target, in predicate form. -/
def Q014FullPositiveTarget (D : Q014GaussDomain.{u}) : Prop :=
  ∀ x : D.Instance,
    D.admittedAlexandrovAmbient x →
    D.convexHypersurface x →
    D.inducedIntrinsicMetric x →
    D.ambientLowerCurvatureBound x →
    D.hypersurfaceLowerCurvatureBound x

/--
Direct synthetic route: prove the lower-bound transfer inside the Alexandrov
category itself.
-/
structure Q014SyntheticTransfer (D : Q014GaussDomain.{u}) where
  transfer :
    ∀ x : D.Instance,
      D.admittedAlexandrovAmbient x →
      D.convexHypersurface x →
      D.inducedIntrinsicMetric x →
      D.ambientLowerCurvatureBound x →
      D.hypersurfaceLowerCurvatureBound x

/-- A direct synthetic transfer proof closes the full positive target. -/
theorem q014_full_target_of_synthetic_transfer
    {D : Q014GaussDomain.{u}}
    (T : Q014SyntheticTransfer D) :
    Q014FullPositiveTarget D := by
  intro x h_ambient h_convex h_metric h_lower
  exact T.transfer x h_ambient h_convex h_metric h_lower

/--
Controlled reduction route.

`riemannianSourceSlice` marks the source class where the AKP-type theorem is
already proved.  `limitRel y x` says that source-slice instance `y` is an
admissible approximation/resolution/limit witness for Alexandrov instance `x`.
The reduction must preserve the source hypotheses, and stability must transfer
the hypersurface lower-curvature bound from the source witness back to `x`.
-/
structure Q014ControlledReduction (D : Q014GaussDomain.{u}) where
  riemannianSourceSlice : D.Instance → Prop
  limitRel : D.Instance → D.Instance → Prop
  source_theorem :
    ∀ y : D.Instance,
      riemannianSourceSlice y →
      D.convexHypersurface y →
      D.inducedIntrinsicMetric y →
      D.ambientLowerCurvatureBound y →
      D.hypersurfaceLowerCurvatureBound y
  reduction :
    ∀ x : D.Instance,
      D.admittedAlexandrovAmbient x →
      D.convexHypersurface x →
      D.inducedIntrinsicMetric x →
      D.ambientLowerCurvatureBound x →
      ∃ y : D.Instance,
        riemannianSourceSlice y ∧
        D.convexHypersurface y ∧
        D.inducedIntrinsicMetric y ∧
        D.ambientLowerCurvatureBound y ∧
        limitRel y x
  stability :
    ∀ y x : D.Instance,
      limitRel y x →
      D.hypersurfaceLowerCurvatureBound y →
      D.hypersurfaceLowerCurvatureBound x

/--
A controlled Riemannian-source reduction plus lower-curvature stability closes
the full Alexandrov-ambient target.
-/
theorem q014_full_target_of_controlled_reduction
    {D : Q014GaussDomain.{u}}
    (R : Q014ControlledReduction D) :
    Q014FullPositiveTarget D := by
  intro x h_ambient h_convex h_metric h_lower
  rcases R.reduction x h_ambient h_convex h_metric h_lower with
    ⟨y, h_source, h_y_convex, h_y_metric, h_y_lower, h_limit⟩
  exact R.stability y x h_limit
    (R.source_theorem y h_source h_y_convex h_y_metric h_y_lower)

/--
Controlled approximation certificate for the Riemannian-source route.

This is the explicit payload shape needed before a smooth/Riemannian
approximation argument may be counted for the full Alexandrov Q014 target.
It separates the mathematical obligations that are easy to lose in prose:

* existence of a source-slice approximation for every admitted Alexandrov
  convex-hypersurface instance;
* preservation of convexity, induced intrinsic metric and ambient lower
  curvature on the source witness;
* the source lower-bound theorem;
* stability of the hypersurface lower-curvature bound back to the Alexandrov
  limit instance.

Without this certificate, an approximation/doubling/smoothing argument is only
context evidence; with it, the existing controlled-reduction theorem becomes a
full positive proof route.
-/
structure Q014ControlledApproximationCertificate (D : Q014GaussDomain.{u}) where
  riemannianSourceSlice : D.Instance → Prop
  approximationRel : D.Instance → D.Instance → Prop
  approximation_exists :
    ∀ x : D.Instance,
      D.admittedAlexandrovAmbient x →
      D.convexHypersurface x →
      D.inducedIntrinsicMetric x →
      D.ambientLowerCurvatureBound x →
      ∃ y : D.Instance,
        riemannianSourceSlice y ∧
        approximationRel y x
  approximation_preserves_convexity :
    ∀ y x : D.Instance,
      approximationRel y x →
      D.convexHypersurface x →
      D.convexHypersurface y
  approximation_preserves_induced_metric :
    ∀ y x : D.Instance,
      approximationRel y x →
      D.inducedIntrinsicMetric x →
      D.inducedIntrinsicMetric y
  approximation_preserves_ambient_lower_bound :
    ∀ y x : D.Instance,
      approximationRel y x →
      D.ambientLowerCurvatureBound x →
      D.ambientLowerCurvatureBound y
  source_theorem :
    ∀ y : D.Instance,
      riemannianSourceSlice y →
      D.convexHypersurface y →
      D.inducedIntrinsicMetric y →
      D.ambientLowerCurvatureBound y →
      D.hypersurfaceLowerCurvatureBound y
  lower_bound_stability :
    ∀ y x : D.Instance,
      approximationRel y x →
      D.hypersurfaceLowerCurvatureBound y →
      D.hypersurfaceLowerCurvatureBound x

/--
An explicit controlled approximation certificate assembles the abstract
controlled-reduction payload.
-/
def q014_controlled_reduction_of_approximation_certificate
    {D : Q014GaussDomain.{u}}
    (A : Q014ControlledApproximationCertificate D) :
    Q014ControlledReduction D where
  riemannianSourceSlice := A.riemannianSourceSlice
  limitRel := A.approximationRel
  source_theorem := A.source_theorem
  reduction := by
    intro x h_ambient h_convex h_metric h_lower
    rcases A.approximation_exists x h_ambient h_convex h_metric h_lower with
      ⟨y, h_source, h_approx⟩
    exact
      ⟨y,
        h_source,
        A.approximation_preserves_convexity y x h_approx h_convex,
        A.approximation_preserves_induced_metric y x h_approx h_metric,
        A.approximation_preserves_ambient_lower_bound y x h_approx h_lower,
        h_approx⟩
  stability := A.lower_bound_stability

/--
An explicit controlled approximation certificate closes Q014 by routing through
the compiled controlled-reduction theorem.
-/
theorem q014_full_target_of_controlled_approximation_certificate
    {D : Q014GaussDomain.{u}}
    (A : Q014ControlledApproximationCertificate D) :
    Q014FullPositiveTarget D := by
  exact q014_full_target_of_controlled_reduction
    (q014_controlled_reduction_of_approximation_certificate A)

/-- A verified counterexample is exactly the negation witness for the target. -/
def Q014Counterexample (D : Q014GaussDomain.{u}) : Prop :=
  ∃ x : D.Instance,
    D.admittedAlexandrovAmbient x ∧
    D.convexHypersurface x ∧
    D.inducedIntrinsicMetric x ∧
    D.ambientLowerCurvatureBound x ∧
    ¬ D.hypersurfaceLowerCurvatureBound x

/-- Any Q014 counterexample refutes the full positive target. -/
theorem q014_counterexample_refutes_full_target
    {D : Q014GaussDomain.{u}}
    (h_counterexample : Q014Counterexample D) :
    ¬ Q014FullPositiveTarget D := by
  intro h_full
  rcases h_counterexample with
    ⟨x, h_ambient, h_convex, h_metric, h_lower, h_not_hypersurface_lower⟩
  exact h_not_hypersurface_lower
    (h_full x h_ambient h_convex h_metric h_lower)

/--
Boundary-conjecture bridge for Q014.

Petrunin's formulation identifies the Q014-type convex-hypersurface problem
with the boundary-conjecture route: boundary/convex-hypersurface intrinsic
metrics in Alexandrov geometry should inherit the same lower curvature bound.

The field `every_q014_instance_is_boundary_case` is intentionally explicit:
the proof machine may use this bridge only after it has shown that the frozen
Q014 instance is genuinely represented by the boundary/convex-hypersurface
case governed by the conjecture, with the induced intrinsic metric preserved.
-/
structure Q014BoundaryConjectureBridge (D : Q014GaussDomain.{u}) where
  boundaryCase : D.Instance → Prop
  every_q014_instance_is_boundary_case :
    ∀ x : D.Instance,
      D.admittedAlexandrovAmbient x →
      D.convexHypersurface x →
      D.inducedIntrinsicMetric x →
      D.ambientLowerCurvatureBound x →
      boundaryCase x
  boundary_conjecture_transfer :
    ∀ x : D.Instance,
      boundaryCase x →
      D.ambientLowerCurvatureBound x →
      D.hypersurfaceLowerCurvatureBound x

/--
If the boundary-conjecture bridge is proved for the admitted Q014 instances,
then the full positive Q014 target follows.
-/
theorem q014_full_target_of_boundary_conjecture_bridge
    {D : Q014GaussDomain.{u}}
    (B : Q014BoundaryConjectureBridge D) :
    Q014FullPositiveTarget D := by
  intro x h_ambient h_convex h_metric h_lower
  exact B.boundary_conjecture_transfer x
    (B.every_q014_instance_is_boundary_case x h_ambient h_convex h_metric h_lower)
    h_lower

/--
Realization data saying that a boundary-conjecture instance is an admitted
Q014 convex-hypersurface instance.

This is the reverse bookkeeping direction: if a boundary instance has already
been encoded as an admitted convex hypersurface with induced intrinsic metric,
then a proof of the full Q014 target gives the boundary-conjecture conclusion
for that realized class.
-/
structure Q014BoundaryAsConvexHypersurface (D : Q014GaussDomain.{u}) where
  boundaryCase : D.Instance → Prop
  boundary_admitted_ambient :
    ∀ x : D.Instance, boundaryCase x → D.admittedAlexandrovAmbient x
  boundary_convex_hypersurface :
    ∀ x : D.Instance, boundaryCase x → D.convexHypersurface x
  boundary_induced_intrinsic_metric :
    ∀ x : D.Instance, boundaryCase x → D.inducedIntrinsicMetric x

/--
The full Q014 target implies the boundary-conjecture lower-curvature conclusion
for every boundary instance that has been realized as an admitted Q014
convex-hypersurface instance.
-/
theorem q014_full_target_implies_realized_boundary_conjecture
    {D : Q014GaussDomain.{u}}
    (R : Q014BoundaryAsConvexHypersurface D)
    (h_full : Q014FullPositiveTarget D) :
    ∀ x : D.Instance,
      R.boundaryCase x →
      D.ambientLowerCurvatureBound x →
      D.hypersurfaceLowerCurvatureBound x := by
  intro x h_boundary h_lower
  exact h_full x
    (R.boundary_admitted_ambient x h_boundary)
    (R.boundary_convex_hypersurface x h_boundary)
    (R.boundary_induced_intrinsic_metric x h_boundary)
    h_lower

/--
The honest terminal positive payload for Q014.

The full frozen Alexandrov-ambient claim is closed positively only by one of:

* a direct synthetic Alexandrov transfer;
* a controlled approximation certificate with lower-curvature stability;
* a boundary-conjecture bridge that has been proved for the admitted instances.
-/
def Q014TerminalPositivePayload (D : Q014GaussDomain.{u}) : Prop :=
  Nonempty (Q014SyntheticTransfer D) ∨
  Nonempty (Q014ControlledApproximationCertificate D) ∨
  Nonempty (Q014BoundaryConjectureBridge D)

/-- Any terminal positive payload proves the full frozen Q014 target. -/
theorem q014_full_target_of_terminal_positive_payload
    {D : Q014GaussDomain.{u}}
    (P : Q014TerminalPositivePayload D) :
    Q014FullPositiveTarget D := by
  rcases P with h_synthetic | h_approx | h_boundary
  · rcases h_synthetic with ⟨T⟩
    exact q014_full_target_of_synthetic_transfer T
  · rcases h_approx with ⟨A⟩
    exact q014_full_target_of_controlled_approximation_certificate A
  · rcases h_boundary with ⟨B⟩
    exact q014_full_target_of_boundary_conjecture_bridge B

/-- The honest terminal negative payload for Q014 is a verified counterexample. -/
def Q014TerminalNegativePayload (D : Q014GaussDomain.{u}) : Prop :=
  Q014Counterexample D

/-- Any terminal negative payload refutes the full frozen Q014 target. -/
theorem q014_not_full_target_of_terminal_negative_payload
    {D : Q014GaussDomain.{u}}
    (N : Q014TerminalNegativePayload D) :
    ¬ Q014FullPositiveTarget D := by
  exact q014_counterexample_refutes_full_target N

end OCMinimalObligationSpine
