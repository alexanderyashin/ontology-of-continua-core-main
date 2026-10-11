namespace OCMinimalObligationSpine

universe u v

/-!
Q067/Q027 geodesic closed-orbit density gate.

The frozen AIM target asks for a dense subset of metrics in the source class
`G` for which the tangent vectors to closed geodesics are dense in the unit
tangent bundle `SM`.

This file does not replace that target with a weaker Anosov-slice statement.
It records the exact transfer payload needed for the Anosov/geodesic-flow route
and the separate density-in-`G` payload required to promote that route to the
full target.
-/

/-- Predicate bundle for the Q067/Q027 geodesic-density domain. -/
structure Q067GeodesicDensityDomain where
  Metric : Type u
  UnitTangentVector : Metric → Type v
  inG : Metric → Prop
  anosovGeodesicFlowMetric : Metric → Prop
  periodicGeodesicFlowVector :
    ∀ g : Metric, UnitTangentVector g → Prop
  closedGeodesicTangentVector :
    ∀ g : Metric, UnitTangentVector g → Prop
  denseInUnitTangentBundle :
    ∀ g : Metric, (UnitTangentVector g → Prop) → Prop
  denseMetricSubsetInG : (Metric → Prop) → Prop
  density_respects_pointwise_equivalence :
    ∀ (g : Metric) (A B : UnitTangentVector g → Prop),
      (∀ v : UnitTangentVector g, A v ↔ B v) →
      denseInUnitTangentBundle g A →
      denseInUnitTangentBundle g B

/--
The frozen Q067/Q027 target: there is a dense metric subset of `G` whose
metrics have dense closed-geodesic tangent vectors in their unit tangent
bundles.
-/
def Q067DenseClosedGeodesicTangentMetricsInG
    (D : Q067GeodesicDensityDomain.{u, v}) : Prop :=
  ∃ Good : D.Metric → Prop,
    D.denseMetricSubsetInG Good ∧
    ∀ g : D.Metric,
      Good g →
      D.inG g ∧
      D.denseInUnitTangentBundle g
        (D.closedGeodesicTangentVector g)

/--
For one metric, periodic geodesic-flow vectors and tangent lifts of closed
geodesics describe the same subset of the unit tangent bundle.
-/
def Q067PeriodicClosedTangentEquivalence
    (D : Q067GeodesicDensityDomain.{u, v})
    (g : D.Metric) : Prop :=
  ∀ v : D.UnitTangentVector g,
    D.periodicGeodesicFlowVector g v ↔
    D.closedGeodesicTangentVector g v

/--
The local transfer: dense periodic geodesic-flow vectors become dense
closed-geodesic tangent vectors once the two predicates are proved equivalent
on the same unit tangent bundle.
-/
theorem q067_closed_geodesic_tangents_dense_of_periodic_dense
    {D : Q067GeodesicDensityDomain.{u, v}}
    {g : D.Metric}
    (h_periodic_dense :
      D.denseInUnitTangentBundle g
        (D.periodicGeodesicFlowVector g))
    (h_equiv : Q067PeriodicClosedTangentEquivalence D g) :
    D.denseInUnitTangentBundle g
      (D.closedGeodesicTangentVector g) := by
  exact D.density_respects_pointwise_equivalence g
    (D.periodicGeodesicFlowVector g)
    (D.closedGeodesicTangentVector g)
    h_equiv
    h_periodic_dense

/--
An Anosov/geodesic-flow transfer payload for every admitted Anosov metric.

This is a strong scientific slice.  It becomes a full answer to the frozen AIM
target only after a separate proof that the Anosov-good metrics form a dense
subset of the stated metric class `G`.
-/
structure Q067AnosovClosedOrbitTransferPayload
    (D : Q067GeodesicDensityDomain.{u, v}) where
  periodic_vectors_dense :
    ∀ g : D.Metric,
      D.inG g →
      D.anosovGeodesicFlowMetric g →
      D.denseInUnitTangentBundle g
        (D.periodicGeodesicFlowVector g)
  periodic_closed_tangent_equivalence :
    ∀ g : D.Metric,
      D.inG g →
      D.anosovGeodesicFlowMetric g →
      Q067PeriodicClosedTangentEquivalence D g

/--
The Anosov transfer payload proves the Q067 tangent-vector density property for
each admitted Anosov metric.
-/
theorem q067_closed_geodesic_tangents_dense_of_anosov_payload
    {D : Q067GeodesicDensityDomain.{u, v}}
    (P : Q067AnosovClosedOrbitTransferPayload D)
    {g : D.Metric}
    (h_inG : D.inG g)
    (h_anosov : D.anosovGeodesicFlowMetric g) :
    D.denseInUnitTangentBundle g
      (D.closedGeodesicTangentVector g) := by
  exact q067_closed_geodesic_tangents_dense_of_periodic_dense
    (P.periodic_vectors_dense g h_inG h_anosov)
    (P.periodic_closed_tangent_equivalence g h_inG h_anosov)

/--
The missing promotion payload for the frozen target: the admitted Anosov-good
slice itself is dense in the metric class `G`.
-/
structure Q067AnosovSliceDenseInG
    (D : Q067GeodesicDensityDomain.{u, v}) where
  anosov_slice_dense :
    D.denseMetricSubsetInG
      (fun g : D.Metric =>
        D.inG g ∧ D.anosovGeodesicFlowMetric g)

/--
If the Anosov-good slice is dense in `G`, and the Anosov/geodesic-flow transfer
payload is available on that slice, then the full frozen Q067/Q027 target is
proved.
-/
theorem q067_full_target_of_dense_anosov_slice
    {D : Q067GeodesicDensityDomain.{u, v}}
    (S : Q067AnosovSliceDenseInG D)
    (P : Q067AnosovClosedOrbitTransferPayload D) :
    Q067DenseClosedGeodesicTangentMetricsInG D := by
  refine ⟨
    (fun g : D.Metric =>
      D.inG g ∧ D.anosovGeodesicFlowMetric g),
    S.anosov_slice_dense,
    ?_⟩
  intro g h_good
  exact ⟨h_good.1,
    q067_closed_geodesic_tangents_dense_of_anosov_payload
      P h_good.1 h_good.2⟩

/-- A direct dense-good-metric construction also closes the frozen target. -/
structure Q067DirectDenseGoodMetricPackage
    (D : Q067GeodesicDensityDomain.{u, v}) where
  Good : D.Metric → Prop
  good_dense_in_G : D.denseMetricSubsetInG Good
  good_in_G :
    ∀ g : D.Metric, Good g → D.inG g
  good_closed_tangents_dense :
    ∀ g : D.Metric,
      Good g →
      D.denseInUnitTangentBundle g
        (D.closedGeodesicTangentVector g)

/-- A direct dense-good-metric package proves the frozen Q067/Q027 target. -/
theorem q067_full_target_of_direct_dense_good_metric_package
    {D : Q067GeodesicDensityDomain.{u, v}}
    (P : Q067DirectDenseGoodMetricPackage D) :
    Q067DenseClosedGeodesicTangentMetricsInG D := by
  exact ⟨P.Good, P.good_dense_in_G,
    fun g h_good =>
      ⟨P.good_in_G g h_good,
        P.good_closed_tangents_dense g h_good⟩⟩

/--
The honest terminal positive payload for Q067/Q027: either prove the frozen
dense-good-metric target directly, or prove the dense Anosov slice plus the
periodic-orbit/closed-geodesic transfer payload.
-/
def Q067TerminalPositivePayload
    (D : Q067GeodesicDensityDomain.{u, v}) : Prop :=
  Nonempty (Q067DirectDenseGoodMetricPackage D) ∨
  (Nonempty (Q067AnosovSliceDenseInG D) ∧
   Nonempty (Q067AnosovClosedOrbitTransferPayload D))

end OCMinimalObligationSpine
