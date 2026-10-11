import OCKIndividuationMSpaceComposition.LikelihoodRecoverySandwich
import Mathlib.Topology.MetricSpace.Pseudo.Defs

namespace OCKIndividuationMSpaceComposition

section MetricCode

variable {Hypothesis Observation : Type*} [PseudoMetricSpace Observation]

/-- Strict pairwise separation of all distinct registered hypotheses. -/
def RadiusSeparated
    (code : Hypothesis → Observation) (radius : ℝ) : Prop :=
  ∀ ⦃first second : Hypothesis⦄, first ≠ second →
    2 * radius < dist (code first) (code second)

/-- Positive theorem: two distinct codewords cannot both explain one observation
within the certified noise radius. -/
theorem bounded_radius_candidates_unique
    (code : Hypothesis → Observation) (radius : ℝ)
    (separated : RadiusSeparated code radius)
    (observed : Observation) (truth candidate : Hypothesis)
    (truthClose : dist observed (code truth) ≤ radius)
    (candidateClose : dist observed (code candidate) ≤ radius) :
    candidate = truth := by
  by_contra distinct
  have strict := separated distinct
  have upper : dist (code candidate) (code truth) ≤ 2 * radius := by
    calc
      dist (code candidate) (code truth) ≤
          dist (code candidate) observed + dist observed (code truth) :=
        dist_triangle _ _ _
      _ ≤ radius + radius :=
        add_le_add (by simpa [dist_comm] using candidateClose) truthClose
      _ = 2 * radius := by ring
  exact (not_le_of_gt strict) upper

/-- Every decoder that returns a radius-consistent candidate is exact on every
observation generated within that radius. -/
theorem radiusConsistentDecoder_exact
    (code : Hypothesis → Observation) (radius : ℝ)
    (separated : RadiusSeparated code radius)
    (decoder : Observation → Hypothesis)
    (observed : Observation) (truth : Hypothesis)
    (truthClose : dist observed (code truth) ≤ radius)
    (decoderConsistent : dist observed (code (decoder observed)) ≤ radius) :
    decoder observed = truth :=
  bounded_radius_candidates_unique code radius separated observed truth
    (decoder observed) truthClose decoderConsistent

/-- No-go: an observation collision prevents every decoder from being exact on
all registered hypotheses. -/
theorem observation_collision_blocks_uniform_exact_decoder
    (code : Hypothesis → Observation)
    (first second : Hypothesis) (distinct : first ≠ second)
    (collision : code first = code second) :
    ¬ ∃ decoder : Observation → Hypothesis,
        ∀ hypothesis, decoder (code hypothesis) = hypothesis := by
  rintro ⟨decoder, exactOnCode⟩
  apply distinct
  calc
    first = decoder (code first) := (exactOnCode first).symm
    _ = decoder (code second) := by rw [collision]
    _ = second := exactOnCode second

end MetricCode

section RestrictedGeometry

variable {Parameter Observation : Type*}
  [PseudoMetricSpace Parameter] [PseudoMetricSpace Observation]

/-- A design preserves at least an `alpha` fraction of parameter distance on a
declared admissible (for example sparse and beta-min) family. -/
def RestrictedSeparationLowerBound
    (design : Parameter → Observation)
    (admissible : Parameter → Prop) (alpha : ℝ) : Prop :=
  ∀ ⦃first second : Parameter⦄,
    admissible first → admissible second →
    alpha * dist first second ≤ dist (design first) (design second)

/-- A restricted lower-Lipschitz design plus a beta-min margin gives the exact
pairwise observation separation needed for bounded-noise recovery. -/
theorem restrictedLowerBound_yields_radiusSeparation
    (design : Parameter → Observation)
    (admissible : Parameter → Prop) (alpha radius : ℝ)
    (lowerBound : RestrictedSeparationLowerBound design admissible alpha)
    (parameterMargin :
      ∀ ⦃first second : Parameter⦄,
        admissible first → admissible second → first ≠ second →
        2 * radius < alpha * dist first second) :
    ∀ ⦃first second : Parameter⦄,
      admissible first → admissible second → first ≠ second →
      2 * radius < dist (design first) (design second) := by
  intro first second firstAdmissible secondAdmissible distinct
  exact (parameterMargin firstAdmissible secondAdmissible distinct).trans_le
    (lowerBound firstAdmissible secondAdmissible)

/-- Concrete sparse-design recovery theorem.  `admissible` may encode support
size, beta-min, sign, governance scope, or any conjunction required by the
domain projection. -/
theorem bounded_noise_sparse_decoder_exact
    (design : Parameter → Observation)
    (admissible : Parameter → Prop) (alpha radius : ℝ)
    (lowerBound : RestrictedSeparationLowerBound design admissible alpha)
    (parameterMargin :
      ∀ ⦃first second : Parameter⦄,
        admissible first → admissible second → first ≠ second →
        2 * radius < alpha * dist first second)
    (decoder : Observation → Parameter)
    (observed : Observation) (truth : Parameter)
    (truthAdmissible : admissible truth)
    (decodedAdmissible : admissible (decoder observed))
    (truthClose : dist observed (design truth) ≤ radius)
    (decoderConsistent : dist observed (design (decoder observed)) ≤ radius) :
    decoder observed = truth := by
  by_contra distinct
  have strict :
      2 * radius < alpha * dist (decoder observed) truth :=
    parameterMargin decodedAdmissible truthAdmissible distinct
  have restricted :
      alpha * dist (decoder observed) truth ≤
        dist (design (decoder observed)) (design truth) :=
    lowerBound decodedAdmissible truthAdmissible
  have upper :
      dist (design (decoder observed)) (design truth) ≤ 2 * radius := by
    calc
      dist (design (decoder observed)) (design truth) ≤
          dist (design (decoder observed)) observed +
            dist observed (design truth) := dist_triangle _ _ _
      _ ≤ radius + radius :=
        add_le_add (by simpa [dist_comm] using decoderConsistent) truthClose
      _ = 2 * radius := by ring
  exact (not_le_of_gt (strict.trans_le restricted)) upper

end RestrictedGeometry

end OCKIndividuationMSpaceComposition
