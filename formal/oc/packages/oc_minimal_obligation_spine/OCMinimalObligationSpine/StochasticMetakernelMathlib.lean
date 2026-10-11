import Mathlib.Probability.Kernel.Basic
import Mathlib.Probability.Kernel.Composition.Comp
import Mathlib.Probability.Kernel.Disintegration.StandardBorel

/-!
Mathlib-backed surface for the stochastic metakernel research line.

This file deliberately proves only the measurable-interface layer needed by
the next theorem obligations.  It proves the quotient-kernel Markov closure
available under an explicit measurable representative/section assumption.  It
does not prove the general stochastic metakernel or stochastic refinement
theorem.
-/

namespace OCMinimalObligationSpine
namespace StochasticMetakernelMathlib

open MeasureTheory
open ProbabilityTheory
open scoped ProbabilityTheory

universe uX uQ uC uE uSig

/--
A measurable quotient or sufficient statistic used to turn a state space `X`
into an explicitly measurable candidate quotient space `Q`.
-/
structure MeasurableQuotientSurface
    (X : Type uX) (Q : Type uQ)
    [MeasurableSpace X] [MeasurableSpace Q] where
  q : X → Q
  measurable_q : Measurable q

/--
An event in the original state space is quotient-saturated when it is the
pullback of a measurable event on the quotient/sufficient-statistic space.
-/
def QuotientSaturated
    {X : Type uX} {Q : Type uQ}
    [MeasurableSpace X] [MeasurableSpace Q]
    (surface : MeasurableQuotientSurface X Q) (s : Set X) : Prop :=
  ∃ t : Set Q, MeasurableSet t ∧ s = surface.q ⁻¹' t

theorem measurableSet_of_quotientSaturated
    {X : Type uX} {Q : Type uQ}
    [MeasurableSpace X] [MeasurableSpace Q]
    {surface : MeasurableQuotientSurface X Q} {s : Set X}
    (hs : QuotientSaturated surface s) : MeasurableSet s := by
  rcases hs with ⟨t, ht, rfl⟩
  exact surface.measurable_q ht

theorem preimage_quotientSaturated
    {X : Type uX} {Q : Type uQ}
    [MeasurableSpace X] [MeasurableSpace Q]
    (surface : MeasurableQuotientSurface X Q)
    {t : Set Q} (ht : MeasurableSet t) :
    QuotientSaturated surface (surface.q ⁻¹' t) := by
  exact ⟨t, ht, rfl⟩

/--
Receiver-law signatures are measurable sufficient statistics whose equality
forces equality of all declared one-step receiver event probabilities.

This is the typed interface needed before stating representative-independent
quotient kernels.  It is not yet a Markov-closure theorem.
-/
structure ReceiverLawSignatureSurface
    (X : Type uX) (C : Type uC) (E : Type uE) (Sig : Type uSig)
    [MeasurableSpace X] [MeasurableSpace E] [MeasurableSpace Sig] where
  receiver : C → Kernel X E
  signature : X → Sig
  measurable_signature : Measurable signature
  same_signature_implies_same_receiver_law :
    ∀ ⦃x y : X⦄,
      signature x = signature y →
        ∀ (c : C) {event : Set E},
          MeasurableSet event →
            receiver c x event = receiver c y event

/--
The receiver-law signature factors through the quotient/sufficient statistic
when a measurable map from quotient states to signatures reconstructs it.
-/
structure ReceiverSignatureFactorization
    (X : Type uX) (Q : Type uQ) (Sig : Type uSig)
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace Sig] where
  quotient_surface : MeasurableQuotientSurface X Q
  signature_on_quotient : Q → Sig
  measurable_signature_on_quotient : Measurable signature_on_quotient
  signature : X → Sig
  signature_eq_comp : signature = signature_on_quotient ∘ quotient_surface.q

theorem measurable_signature_of_factorization
    {X : Type uX} {Q : Type uQ} {Sig : Type uSig}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace Sig]
    (factorization : ReceiverSignatureFactorization X Q Sig) :
    Measurable factorization.signature := by
  rw [factorization.signature_eq_comp]
  exact factorization.measurable_signature_on_quotient.comp
    factorization.quotient_surface.measurable_q

/--
Minimal assumption package for the next stochastic bridge step: the state,
quotient, event, and signature spaces have measurable structures; the quotient
map and signature maps are measurable; and the receiver kernels are mathlib
kernels.
-/
structure StochasticBridgeMeasurableSurface
    (X : Type uX) (Q : Type uQ) (C : Type uC) (E : Type uE) (Sig : Type uSig)
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace E] [MeasurableSpace Sig] where
  quotient_surface : MeasurableQuotientSurface X Q
  receiver_surface : ReceiverLawSignatureSurface X C E Sig
  factorization : ReceiverSignatureFactorization X Q Sig

theorem bridge_signature_measurable
    {X : Type uX} {Q : Type uQ} {C : Type uC} {E : Type uE} {Sig : Type uSig}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace E] [MeasurableSpace Sig]
    (bridge : StochasticBridgeMeasurableSurface X Q C E Sig) :
    Measurable bridge.factorization.signature :=
  measurable_signature_of_factorization bridge.factorization

/--
`transition` is lumpable through `surface.q` when every measurable quotient
event has representative-independent transition probability after pullback.
-/
def QuotientTransitionLumpable
    {X : Type uX} {Q : Type uQ}
    [MeasurableSpace X] [MeasurableSpace Q]
    (surface : MeasurableQuotientSurface X Q)
    (transition : Kernel X X) : Prop :=
  ∀ ⦃x y : X⦄,
    surface.q x = surface.q y →
      ∀ {event : Set Q},
        MeasurableSet event →
          transition x (surface.q ⁻¹' event) =
            transition y (surface.q ⁻¹' event)

theorem quotient_transition_value_representative_independent
    {X : Type uX} {Q : Type uQ}
    [MeasurableSpace X] [MeasurableSpace Q]
    {surface : MeasurableQuotientSurface X Q}
    {transition : Kernel X X}
    (h_lumpable : QuotientTransitionLumpable surface transition)
    {x y : X} (hxy : surface.q x = surface.q y)
    {event : Set Q} (h_event : MeasurableSet event) :
    transition x (surface.q ⁻¹' event) =
      transition y (surface.q ⁻¹' event) :=
  h_lumpable hxy h_event

/--
The next construction target is a quotient kernel whose event law agrees with
the source transition law on every pulled-back measurable quotient event.

This structure records a typechecked construction contract.  Supplying an
inhabitant is stronger than the representative-independence theorem above and
is intentionally left as the next open obligation for Markov closure.
-/
structure QuotientKernelConstructionSurface
    (X : Type uX) (Q : Type uQ)
    [MeasurableSpace X] [MeasurableSpace Q] where
  quotient_surface : MeasurableQuotientSurface X Q
  source_transition : Kernel X X
  quotient_transition : Kernel Q Q
  source_transition_lumpable :
    QuotientTransitionLumpable quotient_surface source_transition
  quotient_transition_law :
    ∀ (x : X) {event : Set Q},
      MeasurableSet event →
        quotient_transition (quotient_surface.q x) event =
          source_transition x (quotient_surface.q ⁻¹' event)

theorem quotient_kernel_law_representative_independent
    {X : Type uX} {Q : Type uQ}
    [MeasurableSpace X] [MeasurableSpace Q]
    (construction : QuotientKernelConstructionSurface X Q)
    {x y : X} (hxy : construction.quotient_surface.q x =
      construction.quotient_surface.q y)
    {event : Set Q} (h_event : MeasurableSet event) :
    construction.source_transition x
        (construction.quotient_surface.q ⁻¹' event) =
      construction.source_transition y
        (construction.quotient_surface.q ⁻¹' event) :=
  construction.source_transition_lumpable hxy h_event

/--
Given a measurable representative/section for quotient states, a source kernel
on `X` pushes forward to a concrete quotient kernel on `Q`.

The construction is intentionally parameterized by the measurable
representative map; existence of such a representative in the desired generality
is a separate standard-Borel/regular-conditional obligation.
-/
noncomputable def quotientKernelFromRepresentative
    {X : Type uX} {Q : Type uQ}
    [MeasurableSpace X] [MeasurableSpace Q]
    (surface : MeasurableQuotientSurface X Q)
    (transition : Kernel X X)
    (repr : Q → X) (h_repr : Measurable repr) : Kernel Q Q where
  toFun q_state := Measure.map surface.q (transition (repr q_state))
  measurable' := by
    exact (Measure.measurable_map surface.q surface.measurable_q).comp
      (transition.measurable.comp h_repr)

theorem quotientKernelFromRepresentative_apply
    {X : Type uX} {Q : Type uQ}
    [MeasurableSpace X] [MeasurableSpace Q]
    (surface : MeasurableQuotientSurface X Q)
    (transition : Kernel X X)
    (repr : Q → X) (h_repr : Measurable repr)
    (q_state : Q) {event : Set Q} (h_event : MeasurableSet event) :
    quotientKernelFromRepresentative surface transition repr h_repr q_state event =
      transition (repr q_state) (surface.q ⁻¹' event) := by
  rw [quotientKernelFromRepresentative]
  exact Measure.map_apply surface.measurable_q h_event

theorem quotientKernelFromRepresentative_law_independent_of_section_value
    {X : Type uX} {Q : Type uQ}
    [MeasurableSpace X] [MeasurableSpace Q]
    {surface : MeasurableQuotientSurface X Q}
    {transition : Kernel X X}
    (h_lumpable : QuotientTransitionLumpable surface transition)
    {repr₁ repr₂ : Q → X} {h_repr₁ : Measurable repr₁} {h_repr₂ : Measurable repr₂}
    {q_state : Q}
    (h_repr₁_hits : surface.q (repr₁ q_state) = q_state)
    (h_repr₂_hits : surface.q (repr₂ q_state) = q_state)
    {event : Set Q} (h_event : MeasurableSet event) :
    quotientKernelFromRepresentative surface transition repr₁ h_repr₁ q_state event =
      quotientKernelFromRepresentative surface transition repr₂ h_repr₂ q_state event := by
  rw [quotientKernelFromRepresentative_apply surface transition repr₁ h_repr₁ q_state h_event]
  rw [quotientKernelFromRepresentative_apply surface transition repr₂ h_repr₂ q_state h_event]
  exact h_lumpable (h_repr₁_hits.trans h_repr₂_hits.symm) h_event

/--
One-step source-to-quotient bridge: under transition lumpability, the explicit
representative quotient kernel started at `q x` agrees with the pushforward of
the source transition from `x` on every measurable quotient event, provided the
representative chosen for `q x` lies in the same quotient fibre as `x`.

This is the first source-process preservation bridge needed for the finite
horizon theorem; iterating it over source paths remains a separate obligation.
-/
theorem quotientKernelFromRepresentative_apply_of_source_state
    {X : Type uX} {Q : Type uQ}
    [MeasurableSpace X] [MeasurableSpace Q]
    {surface : MeasurableQuotientSurface X Q}
    {transition : Kernel X X}
    (h_lumpable : QuotientTransitionLumpable surface transition)
    {repr : Q → X} {h_repr : Measurable repr}
    (x : X)
    (h_repr_hits : surface.q (repr (surface.q x)) = surface.q x)
    {event : Set Q} (h_event : MeasurableSet event) :
    quotientKernelFromRepresentative surface transition repr h_repr (surface.q x) event =
      transition x (surface.q ⁻¹' event) := by
  rw [quotientKernelFromRepresentative_apply surface transition repr h_repr (surface.q x) h_event]
  exact h_lumpable h_repr_hits h_event

/--
If the source transition is a Markov kernel, then the representative-pushforward
quotient transition is also a Markov kernel.

This closes the Markov-probability part of the quotient construction under the
same explicit measurable representative assumption used by
`quotientKernelFromRepresentative`; it does not assert existence of a canonical
representative in full generality.
-/
theorem quotientKernelFromRepresentative_isMarkovKernel
    {X : Type uX} {Q : Type uQ}
    [MeasurableSpace X] [MeasurableSpace Q]
    (surface : MeasurableQuotientSurface X Q)
    (transition : Kernel X X) [IsMarkovKernel transition]
    (repr : Q → X) (h_repr : Measurable repr) :
    IsMarkovKernel (quotientKernelFromRepresentative surface transition repr h_repr) := by
  refine ⟨fun q_state => ?_⟩
  dsimp [quotientKernelFromRepresentative]
  exact (transition (repr q_state)).isProbabilityMeasure_map
    surface.measurable_q.aemeasurable

/--
Receiver kernels are lumpable through the quotient when every measurable
receiver event has representative-independent probability on quotient fibres.
-/
def QuotientReceiverLumpable
    {X : Type uX} {Q : Type uQ} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace E]
    (surface : MeasurableQuotientSurface X Q)
    (receiver : C → Kernel X E) : Prop :=
  ∀ (c : C) ⦃x y : X⦄,
    surface.q x = surface.q y →
      ∀ {event : Set E},
        MeasurableSet event →
          receiver c x event = receiver c y event

/--
The quotient is complete for the declared receiver laws when equality of every
declared receiver event law forces equality of quotient states.

Together with `QuotientReceiverLumpable`, this states that the quotient fibres
are exactly the receiver-law equivalence classes, not merely a sufficient
coarsening.
-/
def ReceiverLawCompleteQuotient
    {X : Type uX} {Q : Type uQ} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace E]
    (surface : MeasurableQuotientSurface X Q)
    (receiver : C → Kernel X E) : Prop :=
  ∀ ⦃x y : X⦄,
    (∀ (c : C) {event : Set E},
      MeasurableSet event →
        receiver c x event = receiver c y event) →
      surface.q x = surface.q y

/--
An external encoder is exact for the declared receiver laws when two source
states mapped to the same encoder state have identical declared receiver event
laws.
-/
def EncoderReceiverLawPreserving
    {X : Type uX} {R : Type*} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace E]
    (encoder : X → R)
    (receiver : C → Kernel X E) : Prop :=
  ∀ ⦃x y : X⦄,
    encoder x = encoder y →
      ∀ (c : C) {event : Set E},
        MeasurableSet event →
          receiver c x event = receiver c y event

/--
Relation-level refinement: the encoder may be finer than the quotient, but it
may not merge two states that the quotient keeps distinct.
-/
def EncoderRefinesQuotient
    {X : Type uX} {Q : Type uQ} {R : Type*}
    [MeasurableSpace X] [MeasurableSpace Q]
    (surface : MeasurableQuotientSurface X Q)
    (encoder : X → R) : Prop :=
  ∀ ⦃x y : X⦄, encoder x = encoder y → surface.q x = surface.q y

theorem encoder_refines_quotient_of_receiver_law_complete
    {X : Type uX} {Q : Type uQ} {R : Type*} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace E]
    {surface : MeasurableQuotientSurface X Q}
    {receiver : C → Kernel X E}
    {encoder : X → R}
    (h_complete : ReceiverLawCompleteQuotient surface receiver)
    (h_encoder_exact : EncoderReceiverLawPreserving encoder receiver) :
    EncoderRefinesQuotient surface encoder := by
  intro x y hxy
  exact h_complete (h_encoder_exact hxy)

/--
Scoped stochastic refinement/no-go theorem.

If the quotient is complete for the declared receiver-law family, then an exact
receiver-law-preserving encoder cannot identify two states that land in
different quotient fibres.  This is the Lean-level no-go core of `SGM-STEP-05`:
any exact closed encoder preserving the declared receiver laws must refine the
quotient relation.  It does not yet prove measurable factor existence or
isomorphism of arbitrary quotient realizations.
-/
theorem exact_encoder_quotient_collision_noGo
    {X : Type uX} {Q : Type uQ} {R : Type*} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace E]
    {surface : MeasurableQuotientSurface X Q}
    {receiver : C → Kernel X E}
    {encoder : X → R}
    (h_complete : ReceiverLawCompleteQuotient surface receiver)
    (h_encoder_exact : EncoderReceiverLawPreserving encoder receiver)
    {x y : X}
    (h_encoder_collision : encoder x = encoder y)
    (h_quotient_distinct : surface.q x ≠ surface.q y) :
    False := by
  exact h_quotient_distinct
    (encoder_refines_quotient_of_receiver_law_complete
      h_complete h_encoder_exact h_encoder_collision)

/--
Set-theoretic decoder induced by an encoder that refines the quotient relation.

For encoder states outside the image of `encoder`, the decoder returns
`default`; on the image, the refinement proof makes the quotient value
well-defined.  No measurability is claimed here.
-/
noncomputable def quotientDecoderOfEncoderRefinement
    {X : Type uX} {Q : Type uQ} {R : Type*}
    [MeasurableSpace X] [MeasurableSpace Q] [Inhabited Q]
    (surface : MeasurableQuotientSurface X Q)
    (encoder : X → R)
    (_h_refines : EncoderRefinesQuotient surface encoder) : R → Q := by
  classical
  exact fun r =>
    if h : ∃ x : X, encoder x = r then
      surface.q (Classical.choose h)
    else
      default

theorem quotientDecoderOfEncoderRefinement_apply
    {X : Type uX} {Q : Type uQ} {R : Type*}
    [MeasurableSpace X] [MeasurableSpace Q] [Inhabited Q]
    {surface : MeasurableQuotientSurface X Q}
    {encoder : X → R}
    (h_refines : EncoderRefinesQuotient surface encoder)
    (x : X) :
    quotientDecoderOfEncoderRefinement surface encoder h_refines
        (encoder x) =
      surface.q x := by
  classical
  unfold quotientDecoderOfEncoderRefinement
  let h_exists : ∃ y : X, encoder y = encoder x := ⟨x, rfl⟩
  rw [dif_pos h_exists]
  exact h_refines (Classical.choose_spec h_exists)

/--
An exact receiver-law-preserving encoder over a receiver-law-complete quotient
admits a set-theoretic quotient decoder on its image.

This is a scoped factorization result for `SGM-STEP-05`.  It deliberately stops
before the measurable factor/isomorphism claim: constructing a measurable
decoder requires additional measurable-selection or standard-Borel assumptions.
-/
theorem quotient_factors_through_exact_encoder_set_theoretically
    {X : Type uX} {Q : Type uQ} {R : Type*} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace E] [Inhabited Q]
    {surface : MeasurableQuotientSurface X Q}
    {receiver : C → Kernel X E}
    {encoder : X → R}
    (h_complete : ReceiverLawCompleteQuotient surface receiver)
    (h_encoder_exact : EncoderReceiverLawPreserving encoder receiver)
    (x : X) :
    quotientDecoderOfEncoderRefinement surface encoder
        (encoder_refines_quotient_of_receiver_law_complete
          h_complete h_encoder_exact)
        (encoder x) =
      surface.q x := by
  exact quotientDecoderOfEncoderRefinement_apply
    (encoder_refines_quotient_of_receiver_law_complete
      h_complete h_encoder_exact) x

/--
Measurable factorization contract for an encoder through the quotient.

This is the precise measurable upgrade of the set-theoretic decoder above:
the quotient map is recovered as a measurable decoder after the encoder.  The
contract is intentionally a structure, not an existence theorem; existence of a
measurable decoder for arbitrary exact encoders remains the separate measurable-
selection/isomorphism obligation of `SGM-STEP-05`.
-/
structure MeasurableQuotientFactorizationThroughEncoder
    {X : Type uX} {Q : Type uQ} {R : Type*}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace R]
    (surface : MeasurableQuotientSurface X Q)
    (encoder : X → R) where
  decoder : R → Q
  measurable_decoder : Measurable decoder
  quotient_eq_decoder_comp_encoder :
    ∀ x : X, decoder (encoder x) = surface.q x

/--
Any measurable quotient factorization through an encoder proves the
relation-level refinement: the encoder cannot merge quotient-distinct states.
-/
theorem measurable_factorization_refines_quotient
    {X : Type uX} {Q : Type uQ} {R : Type*}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace R]
    {surface : MeasurableQuotientSurface X Q}
    {encoder : X → R}
    (factorization :
      MeasurableQuotientFactorizationThroughEncoder surface encoder) :
    EncoderRefinesQuotient surface encoder := by
  intro x y hxy
  calc
    surface.q x = factorization.decoder (encoder x) := by
      exact (factorization.quotient_eq_decoder_comp_encoder x).symm
    _ = factorization.decoder (encoder y) := by
      rw [hxy]
    _ = surface.q y := by
      exact factorization.quotient_eq_decoder_comp_encoder y

/--
An exact receiver-law-preserving encoder over a receiver-law-complete quotient
has a measurable quotient factorization whenever the induced set-theoretic
decoder is itself measurable.

The theorem deliberately exposes the remaining burden as
`h_decoder_measurable`; it does not smuggle in measurable selection or a
standard-Borel isomorphism theorem.
-/
noncomputable def exact_encoder_has_measurable_factorization_of_measurable_decoder
    {X : Type uX} {Q : Type uQ} {R : Type*} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace R]
    [MeasurableSpace E] [Inhabited Q]
    {surface : MeasurableQuotientSurface X Q}
    {receiver : C → Kernel X E}
    {encoder : X → R}
    (h_complete : ReceiverLawCompleteQuotient surface receiver)
    (h_encoder_exact : EncoderReceiverLawPreserving encoder receiver)
    (h_decoder_measurable :
      Measurable
        (quotientDecoderOfEncoderRefinement surface encoder
          (encoder_refines_quotient_of_receiver_law_complete
            h_complete h_encoder_exact))) :
    MeasurableQuotientFactorizationThroughEncoder surface encoder where
  decoder :=
    quotientDecoderOfEncoderRefinement surface encoder
      (encoder_refines_quotient_of_receiver_law_complete
        h_complete h_encoder_exact)
  measurable_decoder := h_decoder_measurable
  quotient_eq_decoder_comp_encoder :=
    quotient_factors_through_exact_encoder_set_theoretically
      h_complete h_encoder_exact

/--
The quotient refines an encoder when the encoder carries no distinctions
beyond the quotient fibres.  Together with `EncoderRefinesQuotient`, this is
the relation-level "same scientific information" condition.
-/
def QuotientRefinesEncoder
    {X : Type uX} {Q : Type uQ} {R : Type*}
    [MeasurableSpace X] [MeasurableSpace Q]
    (surface : MeasurableQuotientSurface X Q)
    (encoder : X → R) : Prop :=
  ∀ ⦃x y : X⦄, surface.q x = surface.q y → encoder x = encoder y

/--
Bimeasurable source-level realization between a quotient and an encoder.

The two maps are required to agree on the actually observed source states:
`decoder ∘ encoder = q` and `encoder_on_quotient ∘ q = encoder`.  This is the
honest scoped replacement for an overbroad "arbitrary exact encoders are
measurably isomorphic" claim: it records exactly which measurable witnesses
must exist before the isomorphism language is justified.
-/
structure BimeasurableQuotientEncoderRealizationOnSource
    {X : Type uX} {Q : Type uQ} {R : Type*}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace R]
    (surface : MeasurableQuotientSurface X Q)
    (encoder : X → R) where
  decoder : R → Q
  measurable_decoder : Measurable decoder
  encoder_on_quotient : Q → R
  measurable_encoder_on_quotient : Measurable encoder_on_quotient
  quotient_eq_decoder_comp_encoder :
    ∀ x : X, decoder (encoder x) = surface.q x
  encoder_eq_encoder_on_quotient_comp_quotient :
    ∀ x : X, encoder_on_quotient (surface.q x) = encoder x

theorem bimeasurable_realization_refines_both_relations
    {X : Type uX} {Q : Type uQ} {R : Type*}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace R]
    {surface : MeasurableQuotientSurface X Q}
    {encoder : X → R}
    (realization :
      BimeasurableQuotientEncoderRealizationOnSource surface encoder) :
    EncoderRefinesQuotient surface encoder ∧
      QuotientRefinesEncoder surface encoder := by
  constructor
  · intro x y hxy
    calc
      surface.q x = realization.decoder (encoder x) := by
        exact (realization.quotient_eq_decoder_comp_encoder x).symm
      _ = realization.decoder (encoder y) := by
        rw [hxy]
      _ = surface.q y := by
        exact realization.quotient_eq_decoder_comp_encoder y
  · intro x y hxy
    calc
      encoder x = realization.encoder_on_quotient (surface.q x) := by
        exact (realization.encoder_eq_encoder_on_quotient_comp_quotient x).symm
      _ = realization.encoder_on_quotient (surface.q y) := by
        rw [hxy]
      _ = encoder y := by
        exact realization.encoder_eq_encoder_on_quotient_comp_quotient y

/--
Scoped measurable-isomorphism realization for a minimal exact encoder.

If an exact encoder preserves a receiver-law-complete quotient, its induced
quotient decoder is measurable, and the encoder carries no extra distinctions
inside quotient fibres, then any measurable quotient section induces a
bimeasurable realization on the source image.  This proves the usable
minimal-encoder isomorphism contract while leaving the genuinely general
measurable-selection/isomorphism theorem open.
-/
noncomputable def exact_minimal_encoder_has_bimeasurable_quotient_realization
    {X : Type uX} {Q : Type uQ} {R : Type*} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace R]
    [MeasurableSpace E] [Inhabited Q]
    {surface : MeasurableQuotientSurface X Q}
    {receiver : C → Kernel X E}
    {encoder : X → R}
    (h_complete : ReceiverLawCompleteQuotient surface receiver)
    (h_encoder_exact : EncoderReceiverLawPreserving encoder receiver)
    (h_no_extra_state : QuotientRefinesEncoder surface encoder)
    (h_encoder_measurable : Measurable encoder)
    {repr : Q → X} (h_repr : Measurable repr)
    (h_repr_section : ∀ q_state : Q, surface.q (repr q_state) = q_state)
    (h_decoder_measurable :
      Measurable
        (quotientDecoderOfEncoderRefinement surface encoder
          (encoder_refines_quotient_of_receiver_law_complete
            h_complete h_encoder_exact))) :
    BimeasurableQuotientEncoderRealizationOnSource surface encoder where
  decoder :=
    quotientDecoderOfEncoderRefinement surface encoder
      (encoder_refines_quotient_of_receiver_law_complete
        h_complete h_encoder_exact)
  measurable_decoder := h_decoder_measurable
  encoder_on_quotient := encoder ∘ repr
  measurable_encoder_on_quotient := h_encoder_measurable.comp h_repr
  quotient_eq_decoder_comp_encoder :=
    quotient_factors_through_exact_encoder_set_theoretically
      h_complete h_encoder_exact
  encoder_eq_encoder_on_quotient_comp_quotient := by
    intro x
    exact h_no_extra_state (h_repr_section (surface.q x))

/--
Boundary counterexample for `SGM-STEP-05`.

An exact encoder can be strictly finer than a receiver-law-complete quotient:
take the two-point source `Bool`, the collapsed quotient `Unit`, and the
identity encoder.  With an empty declared receiver family, the quotient is
receiver-law-complete and the encoder is exact, but the quotient does not refine
the encoder.  Therefore an arbitrary exact encoder cannot honestly be claimed
measurably isomorphic to the quotient without an additional no-extra-state /
minimality assumption.
-/
theorem exact_encoder_need_not_be_minimal_counterexample :
    ∃ (surface : MeasurableQuotientSurface Bool Unit)
      (receiver : Empty → Kernel Bool Unit) (encoder : Bool → Bool),
      ReceiverLawCompleteQuotient surface receiver ∧
        EncoderReceiverLawPreserving encoder receiver ∧
        EncoderRefinesQuotient surface encoder ∧
        ¬ QuotientRefinesEncoder surface encoder := by
  let surface : MeasurableQuotientSurface Bool Unit := {
    q := fun _ => ()
    measurable_q := measurable_const
  }
  let receiver : Empty → Kernel Bool Unit := fun c => nomatch c
  let encoder : Bool → Bool := fun x => x
  refine ⟨surface, receiver, encoder, ?_, ?_, ?_, ?_⟩
  · intro x y _h_receiver_law_equal
    rfl
  · intro x y _h_encoder_equal c
    cases c
  · intro x y _h_encoder_equal
    rfl
  · intro h_quotient_refines
    have h_false_eq_true : (false : Bool) = true :=
      h_quotient_refines (x := false) (y := true) rfl
    cases h_false_eq_true

/--
Domain-admission package for the canonical minimal quotient witness.

This is the fail-closed `SGM-STEP-06` contract.  A domain may use the scoped
minimal bimeasurable-realization theorem only after it supplies all semantic
witnesses explicitly: receiver-law completeness, exactness, no-extra-state
minimality, measurable encoder, measurable quotient section, and measurability
of the induced quotient decoder.  The structure is intentionally not an
automatic existence theorem for arbitrary measurable spaces.
-/
structure CanonicalMinimalQuotientWitnessPackage
    {X : Type uX} {Q : Type uQ} {R : Type*} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace R]
    [MeasurableSpace E] [Inhabited Q]
    (surface : MeasurableQuotientSurface X Q)
    (receiver : C → Kernel X E)
    (encoder : X → R) where
  receiver_law_complete : ReceiverLawCompleteQuotient surface receiver
  encoder_exact : EncoderReceiverLawPreserving encoder receiver
  no_extra_state : QuotientRefinesEncoder surface encoder
  encoder_measurable : Measurable encoder
  repr : Q → X
  repr_measurable : Measurable repr
  repr_section : ∀ q_state : Q, surface.q (repr q_state) = q_state
  induced_decoder_measurable :
    Measurable
      (quotientDecoderOfEncoderRefinement surface encoder
        (encoder_refines_quotient_of_receiver_law_complete
          receiver_law_complete encoder_exact))

/--
The canonical witness package is sufficient for the scoped minimal
bimeasurable quotient/encoder realization.

This theorem is the formal claim-narrowing gate: publication may use the
isomorphism language only for witness-supplied domains that inhabit
`CanonicalMinimalQuotientWitnessPackage`; otherwise the claim remains open or
must be weakened.
-/
noncomputable def bimeasurable_realization_of_canonical_minimal_witness_package
    {X : Type uX} {Q : Type uQ} {R : Type*} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace R]
    [MeasurableSpace E] [Inhabited Q]
    {surface : MeasurableQuotientSurface X Q}
    {receiver : C → Kernel X E}
    {encoder : X → R}
    (witness :
      CanonicalMinimalQuotientWitnessPackage surface receiver encoder) :
    BimeasurableQuotientEncoderRealizationOnSource surface encoder :=
  exact_minimal_encoder_has_bimeasurable_quotient_realization
    witness.receiver_law_complete
    witness.encoder_exact
    witness.no_extra_state
    witness.encoder_measurable
    witness.repr_measurable
    witness.repr_section
    witness.induced_decoder_measurable

theorem canonical_minimal_witness_package_refines_both_relations
    {X : Type uX} {Q : Type uQ} {R : Type*} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace R]
    [MeasurableSpace E] [Inhabited Q]
    {surface : MeasurableQuotientSurface X Q}
    {receiver : C → Kernel X E}
    {encoder : X → R}
    (witness :
      CanonicalMinimalQuotientWitnessPackage surface receiver encoder) :
    EncoderRefinesQuotient surface encoder ∧
      QuotientRefinesEncoder surface encoder :=
  bimeasurable_realization_refines_both_relations
    (bimeasurable_realization_of_canonical_minimal_witness_package witness)

/--
Given a measurable representative/section for quotient states, source receiver
kernels induce concrete quotient receiver kernels.
-/
noncomputable def quotientReceiverKernelFromRepresentative
    {X : Type uX} {Q : Type uQ} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace E]
    (receiver : C → Kernel X E)
    (repr : Q → X) (h_repr : Measurable repr)
    (c : C) : Kernel Q E where
  toFun q_state := receiver c (repr q_state)
  measurable' := (receiver c).measurable.comp h_repr

theorem quotientReceiverKernelFromRepresentative_apply
    {X : Type uX} {Q : Type uQ} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace E]
    (receiver : C → Kernel X E)
    (repr : Q → X) (h_repr : Measurable repr)
    (c : C) (q_state : Q) {event : Set E} :
    quotientReceiverKernelFromRepresentative receiver repr h_repr c q_state event =
      receiver c (repr q_state) event := by
  rfl

/--
One-step receiver source-to-quotient bridge: under receiver lumpability, the
explicit representative quotient receiver kernel started at `q x` agrees with
the source receiver kernel at `x` on every measurable receiver event, provided
the chosen representative for `q x` lies in the same quotient fibre as `x`.
-/
theorem quotientReceiverKernelFromRepresentative_apply_of_source_state
    {X : Type uX} {Q : Type uQ} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace E]
    {surface : MeasurableQuotientSurface X Q}
    {receiver : C → Kernel X E}
    (h_lumpable : QuotientReceiverLumpable surface receiver)
    {repr : Q → X} {h_repr : Measurable repr}
    (c : C) (x : X)
    (h_repr_hits : surface.q (repr (surface.q x)) = surface.q x)
    {event : Set E} (h_event : MeasurableSet event) :
    quotientReceiverKernelFromRepresentative receiver repr h_repr c (surface.q x) event =
      receiver c x event := by
  rw [quotientReceiverKernelFromRepresentative_apply receiver repr h_repr c (surface.q x)]
  exact h_lumpable c h_repr_hits h_event

theorem quotientReceiverKernelFromRepresentative_isMarkovKernel
    {X : Type uX} {Q : Type uQ} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace E]
    (receiver : C → Kernel X E)
    (repr : Q → X) (h_repr : Measurable repr)
    (h_markov : ∀ c : C, IsMarkovKernel (receiver c))
    (c : C) :
    IsMarkovKernel (quotientReceiverKernelFromRepresentative receiver repr h_repr c) := by
  refine ⟨fun q_state => ?_⟩
  exact (h_markov c).isProbabilityMeasure (repr q_state)

theorem quotientReceiverAfterTransition_isMarkovKernel
    {X : Type uX} {Q : Type uQ} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace E]
    (surface : MeasurableQuotientSurface X Q)
    (transition : Kernel X X) [IsMarkovKernel transition]
    (receiver : C → Kernel X E)
    (repr : Q → X) (h_repr : Measurable repr)
    (h_receiver_markov : ∀ c : C, IsMarkovKernel (receiver c))
    (c : C) :
    IsMarkovKernel
      ((quotientReceiverKernelFromRepresentative receiver repr h_repr c) ∘ₖ
        (quotientKernelFromRepresentative surface transition repr h_repr)) := by
  letI : IsMarkovKernel
      (quotientKernelFromRepresentative surface transition repr h_repr) :=
    quotientKernelFromRepresentative_isMarkovKernel surface transition repr h_repr
  letI : IsMarkovKernel
      (quotientReceiverKernelFromRepresentative receiver repr h_repr c) :=
    quotientReceiverKernelFromRepresentative_isMarkovKernel receiver repr h_repr
      h_receiver_markov c
  infer_instance

theorem quotientReceiverAfterTransition_apply
    {X : Type uX} {Q : Type uQ} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace E]
    (surface : MeasurableQuotientSurface X Q)
    (transition : Kernel X X)
    (receiver : C → Kernel X E)
    (repr : Q → X) (h_repr : Measurable repr)
    (c : C) (q_state : Q) {event : Set E} (h_event : MeasurableSet event) :
    ((quotientReceiverKernelFromRepresentative receiver repr h_repr c) ∘ₖ
        (quotientKernelFromRepresentative surface transition repr h_repr))
        q_state event =
      ∫⁻ q_next,
        receiver c (repr q_next) event
          ∂(quotientKernelFromRepresentative surface transition repr h_repr q_state) := by
  rw [Kernel.comp_apply' _ _ _ h_event]
  rfl

/--
Every finite power of a source Markov transition is again a Markov kernel.
This is the source-side analogue of the explicit quotient finite-horizon
closure theorem.
-/
theorem sourceTransition_power_isMarkovKernel
    {X : Type uX} [MeasurableSpace X]
    (transition : Kernel X X) [IsMarkovKernel transition]
    (n : ℕ) :
    IsMarkovKernel (transition ^ n) := by
  induction n with
  | zero =>
      rw [pow_zero]
      change IsMarkovKernel (Kernel.id : Kernel X X)
      infer_instance
  | succ n ih =>
      letI : IsMarkovKernel (transition ^ n) := ih
      rw [pow_succ]
      change IsMarkovKernel ((transition ^ n) ∘ₖ transition)
      infer_instance

/--
Source-side finite-horizon receiver surface: after `n` source transition steps,
applying a source receiver kernel remains a Markov kernel.
-/
theorem sourceReceiverAfterTransitionPower_isMarkovKernel
    {X : Type uX} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace E]
    (transition : Kernel X X) [IsMarkovKernel transition]
    (receiver : C → Kernel X E)
    (h_receiver_markov : ∀ c : C, IsMarkovKernel (receiver c))
    (c : C) (n : ℕ) :
    IsMarkovKernel ((receiver c) ∘ₖ (transition ^ n)) := by
  have h_transition_power : IsMarkovKernel (transition ^ n) :=
    sourceTransition_power_isMarkovKernel transition n
  have h_receiver : IsMarkovKernel (receiver c) := h_receiver_markov c
  letI : IsMarkovKernel (transition ^ n) := h_transition_power
  letI : IsMarkovKernel (receiver c) := h_receiver
  infer_instance

theorem sourceReceiverAfterTransitionPower_apply
    {X : Type uX} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace E]
    (transition : Kernel X X)
    (receiver : C → Kernel X E)
    (c : C) (n : ℕ) (x : X) {event : Set E}
    (h_event : MeasurableSet event) :
    ((receiver c) ∘ₖ (transition ^ n)) x event =
      ∫⁻ x_next, receiver c x_next event ∂((transition ^ n) x) := by
  rw [Kernel.comp_apply' _ _ _ h_event]

/--
Chapman-Kolmogorov style finite-horizon decomposition for the source receiver
surface.  Receiver observations after `m + n` source steps decompose through an
intermediate source state.
-/
theorem sourceReceiverAfterTransitionPower_add_apply
    {X : Type uX} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace E]
    (transition : Kernel X X)
    (receiver : C → Kernel X E)
    (c : C) (m n : ℕ) (x : X) {event : Set E}
    (h_event : MeasurableSet event) :
    ((receiver c) ∘ₖ (transition ^ (m + n))) x event =
      ∫⁻ x_mid,
        ((receiver c) ∘ₖ (transition ^ m)) x_mid event
          ∂((transition ^ n) x) := by
  rw [Kernel.pow_add]
  rw [← Kernel.comp_assoc]
  rw [Kernel.comp_apply' _ _ _ h_event]

/--
Finite-horizon Markov closure for the explicit representative quotient kernel:
every finite power of the quotient transition is again a Markov kernel.

This still depends on the explicit measurable representative/section supplied
to `quotientKernelFromRepresentative`; it does not prove canonical quotient
existence.
-/
theorem quotientKernelFromRepresentative_power_isMarkovKernel
    {X : Type uX} {Q : Type uQ}
    [MeasurableSpace X] [MeasurableSpace Q]
    (surface : MeasurableQuotientSurface X Q)
    (transition : Kernel X X) [IsMarkovKernel transition]
    (repr : Q → X) (h_repr : Measurable repr)
    (n : ℕ) :
    IsMarkovKernel
      ((quotientKernelFromRepresentative surface transition repr h_repr) ^ n) := by
  let qkernel := quotientKernelFromRepresentative surface transition repr h_repr
  have h_qkernel : IsMarkovKernel qkernel :=
    quotientKernelFromRepresentative_isMarkovKernel surface transition repr h_repr
  change IsMarkovKernel (qkernel ^ n)
  induction n with
  | zero =>
      rw [pow_zero]
      change IsMarkovKernel (Kernel.id : Kernel Q Q)
      infer_instance
  | succ n ih =>
      letI : IsMarkovKernel qkernel := h_qkernel
      letI : IsMarkovKernel (qkernel ^ n) := ih
      rw [pow_succ]
      change IsMarkovKernel ((qkernel ^ n) ∘ₖ qkernel)
      infer_instance

/--
Finite-horizon receiver surface: after `n` quotient transition steps, applying
a quotient receiver kernel remains a Markov kernel.

This is a finite-horizon typed kernel closure theorem, not yet a proof that the
quotient preserves every declared stochastic receiver-law family.
-/
theorem quotientReceiverAfterTransitionPower_isMarkovKernel
    {X : Type uX} {Q : Type uQ} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace E]
    (surface : MeasurableQuotientSurface X Q)
    (transition : Kernel X X) [IsMarkovKernel transition]
    (receiver : C → Kernel X E)
    (repr : Q → X) (h_repr : Measurable repr)
    (h_receiver_markov : ∀ c : C, IsMarkovKernel (receiver c))
    (c : C) (n : ℕ) :
    IsMarkovKernel
      ((quotientReceiverKernelFromRepresentative receiver repr h_repr c) ∘ₖ
        ((quotientKernelFromRepresentative surface transition repr h_repr) ^ n)) := by
  let qkernel := quotientKernelFromRepresentative surface transition repr h_repr
  let qreceiver := quotientReceiverKernelFromRepresentative receiver repr h_repr c
  have h_qkernel_power : IsMarkovKernel (qkernel ^ n) :=
    quotientKernelFromRepresentative_power_isMarkovKernel surface transition repr h_repr n
  have h_qreceiver : IsMarkovKernel qreceiver :=
    quotientReceiverKernelFromRepresentative_isMarkovKernel receiver repr h_repr
      h_receiver_markov c
  change IsMarkovKernel (qreceiver ∘ₖ (qkernel ^ n))
  letI : IsMarkovKernel (qkernel ^ n) := h_qkernel_power
  letI : IsMarkovKernel qreceiver := h_qreceiver
  infer_instance

theorem quotientReceiverAfterTransitionPower_apply
    {X : Type uX} {Q : Type uQ} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace E]
    (surface : MeasurableQuotientSurface X Q)
    (transition : Kernel X X)
    (receiver : C → Kernel X E)
    (repr : Q → X) (h_repr : Measurable repr)
    (c : C) (n : ℕ) (q_state : Q) {event : Set E}
    (h_event : MeasurableSet event) :
    ((quotientReceiverKernelFromRepresentative receiver repr h_repr c) ∘ₖ
        ((quotientKernelFromRepresentative surface transition repr h_repr) ^ n))
        q_state event =
      ∫⁻ q_next,
        receiver c (repr q_next) event
          ∂(((quotientKernelFromRepresentative surface transition repr h_repr) ^ n)
              q_state) := by
  rw [Kernel.comp_apply' _ _ _ h_event]
  rfl

/--
Chapman-Kolmogorov style finite-horizon decomposition for the quotient receiver
surface.  Receiver observations after `m + n` quotient steps decompose through
an intermediate quotient state: first run `n` quotient steps, then evaluate the
receiver-after-`m`-steps law.

This is a typed finite-horizon recursion theorem for the quotient-side process.
It still does not identify this quotient-side law with the source process law;
that source-to-quotient preservation theorem remains a separate obligation.
-/
theorem quotientReceiverAfterTransitionPower_add_apply
    {X : Type uX} {Q : Type uQ} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace E]
    (surface : MeasurableQuotientSurface X Q)
    (transition : Kernel X X)
    (receiver : C → Kernel X E)
    (repr : Q → X) (h_repr : Measurable repr)
    (c : C) (m n : ℕ) (q_state : Q) {event : Set E}
    (h_event : MeasurableSet event) :
    ((quotientReceiverKernelFromRepresentative receiver repr h_repr c) ∘ₖ
        ((quotientKernelFromRepresentative surface transition repr h_repr) ^ (m + n)))
        q_state event =
      ∫⁻ q_mid,
        ((quotientReceiverKernelFromRepresentative receiver repr h_repr c) ∘ₖ
            ((quotientKernelFromRepresentative surface transition repr h_repr) ^ m))
            q_mid event
          ∂(((quotientKernelFromRepresentative surface transition repr h_repr) ^ n)
              q_state) := by
  let qkernel := quotientKernelFromRepresentative surface transition repr h_repr
  let qreceiver := quotientReceiverKernelFromRepresentative receiver repr h_repr c
  change (qreceiver ∘ₖ (qkernel ^ (m + n))) q_state event =
    ∫⁻ q_mid, (qreceiver ∘ₖ (qkernel ^ m)) q_mid event ∂((qkernel ^ n) q_state)
  rw [Kernel.pow_add]
  rw [← Kernel.comp_assoc]
  rw [Kernel.comp_apply' _ _ _ h_event]

/--
Exact finite-horizon transition-law preservation target for `SGM-STEP-04`.

It states that the quotient transition powered for `n` steps from `q x`
matches the pushforward of the source transition powered for `n` steps from
`x`, on every measurable quotient event.  This is the transition-law bridge
needed before proving full finite-horizon receiver-law preservation.
-/
def FiniteHorizonQuotientTransitionLawPreserved
    {X : Type uX} {Q : Type uQ}
    [MeasurableSpace X] [MeasurableSpace Q]
    (surface : MeasurableQuotientSurface X Q)
    (transition : Kernel X X)
    (repr : Q → X) (h_repr : Measurable repr) : Prop :=
  ∀ (n : ℕ) (x : X) {event : Set Q},
    MeasurableSet event →
      ((quotientKernelFromRepresentative surface transition repr h_repr) ^ n)
          (surface.q x) event =
        (transition ^ n) x (surface.q ⁻¹' event)

/--
Base case for the exact finite-horizon quotient transition-law preservation
target.  At horizon zero, both sides are Dirac laws and the equality is just
membership through the quotient preimage.
-/
theorem finiteHorizonQuotientTransitionLawPreserved_zero
    {X : Type uX} {Q : Type uQ}
    [MeasurableSpace X] [MeasurableSpace Q]
    (surface : MeasurableQuotientSurface X Q)
    (transition : Kernel X X)
    (repr : Q → X) (h_repr : Measurable repr)
    (x : X) {event : Set Q} (h_event : MeasurableSet event) :
    ((quotientKernelFromRepresentative surface transition repr h_repr) ^ 0)
        (surface.q x) event =
      (transition ^ 0) x (surface.q ⁻¹' event) := by
  rw [pow_zero, pow_zero]
  change
    (Kernel.id (surface.q x)) event =
      (Kernel.id x) (surface.q ⁻¹' event)
  rw [Kernel.id_apply, Kernel.id_apply]
  rw [Measure.dirac_apply' _ h_event]
  rw [Measure.dirac_apply' _ (surface.measurable_q h_event)]
  rfl

/--
One-step case for the exact finite-horizon quotient transition-law
preservation target.  At horizon one, preservation is exactly transition
lumpability plus the requirement that the representative of `q x` lies in
`x`'s quotient fibre.
-/
theorem finiteHorizonQuotientTransitionLawPreserved_one_of_lumpable
    {X : Type uX} {Q : Type uQ}
    [MeasurableSpace X] [MeasurableSpace Q]
    {surface : MeasurableQuotientSurface X Q}
    {transition : Kernel X X}
    (h_transition_lumpable : QuotientTransitionLumpable surface transition)
    {repr : Q → X} {h_repr : Measurable repr}
    (h_repr_hits : ∀ x : X, surface.q (repr (surface.q x)) = surface.q x)
    (x : X) {event : Set Q} (h_event : MeasurableSet event) :
    ((quotientKernelFromRepresentative surface transition repr h_repr) ^ 1)
        (surface.q x) event =
      (transition ^ 1) x (surface.q ⁻¹' event) := by
  rw [pow_one, pow_one]
  exact quotientKernelFromRepresentative_apply_of_source_state
    h_transition_lumpable x (h_repr_hits x) h_event

/--
Induction step for exact finite-horizon quotient transition-law preservation.

This theorem is deliberately conditional: it does not smuggle in full stochastic
closure.  It states the reusable source-to-quotient transfer step needed by
`SGM-STEP-04`: if the `n`-step source law is already preserved from every source
state, then one source transition followed by that preserved `n`-step bridge
agrees with one quotient transition followed by `n` quotient steps.  The proof
uses the quotient-kernel pushforward identity plus `lintegral_map`.
-/
theorem finiteHorizonQuotientTransitionLawPreserved_succ_of_preserved
    {X : Type uX} {Q : Type uQ}
    [MeasurableSpace X] [MeasurableSpace Q]
    {surface : MeasurableQuotientSurface X Q}
    {transition : Kernel X X}
    (h_transition_lumpable : QuotientTransitionLumpable surface transition)
    {repr : Q → X} {h_repr : Measurable repr}
    (h_repr_section : ∀ q_state : Q, surface.q (repr q_state) = q_state)
    (n : ℕ)
    (h_pres_n :
      ∀ (x : X) {event : Set Q}, MeasurableSet event →
        ((quotientKernelFromRepresentative surface transition repr h_repr) ^ n)
            (surface.q x) event =
          (transition ^ n) x (surface.q ⁻¹' event))
    (x : X) {event : Set Q} (h_event : MeasurableSet event) :
    ((quotientKernelFromRepresentative surface transition repr h_repr) ^ (n + 1))
        (surface.q x) event =
      (transition ^ (n + 1)) x (surface.q ⁻¹' event) := by
  let qkernel := quotientKernelFromRepresentative surface transition repr h_repr
  have h_qkernel_source_map :
      qkernel (surface.q x) = Measure.map surface.q (transition x) := by
    ext s hs
    rw [quotientKernelFromRepresentative_apply_of_source_state
      h_transition_lumpable x (h_repr_section (surface.q x)) hs]
    rw [Measure.map_apply surface.measurable_q hs]
  change (qkernel ^ (n + 1)) (surface.q x) event =
    (transition ^ (n + 1)) x (surface.q ⁻¹' event)
  rw [Nat.add_comm n 1]
  rw [Kernel.pow_add_apply_eq_lintegral qkernel 1 n (surface.q x) h_event]
  rw [Kernel.pow_add_apply_eq_lintegral transition 1 n x
    (surface.measurable_q h_event)]
  simp only [pow_one]
  rw [h_qkernel_source_map]
  have h_measurable_integrand :
      Measurable fun q_mid => (qkernel ^ n) q_mid event := by
    exact (qkernel ^ n).measurable_coe h_event
  rw [MeasureTheory.lintegral_map h_measurable_integrand surface.measurable_q]
  exact lintegral_congr fun x_mid => h_pres_n x_mid h_event

/--
Exact finite-horizon transition-law preservation for an explicitly sectioned
lumpable quotient.

This discharges the recursive transition part of `SGM-STEP-04` in the scoped
setting where the quotient has a declared measurable representative/section and
the source transition is lumpable through the quotient map.  It is still not a
canonical-existence theorem for arbitrary quotients.
-/
theorem finiteHorizonQuotientTransitionLawPreserved_of_lumpable
    {X : Type uX} {Q : Type uQ}
    [MeasurableSpace X] [MeasurableSpace Q]
    {surface : MeasurableQuotientSurface X Q}
    {transition : Kernel X X}
    (h_transition_lumpable : QuotientTransitionLumpable surface transition)
    {repr : Q → X} {h_repr : Measurable repr}
    (h_repr_section : ∀ q_state : Q, surface.q (repr q_state) = q_state) :
    FiniteHorizonQuotientTransitionLawPreserved
      surface transition repr h_repr := by
  intro n
  induction n with
  | zero =>
      intro x event h_event
      exact finiteHorizonQuotientTransitionLawPreserved_zero
        surface transition repr h_repr x h_event
  | succ n ih =>
      intro x event h_event
      exact finiteHorizonQuotientTransitionLawPreserved_succ_of_preserved
        h_transition_lumpable h_repr_section n
        (fun x {event} h_event => ih x h_event) x h_event

/--
Exact finite-horizon receiver-law preservation target for `SGM-STEP-04`.

It states that observing with any declared receiver after `n` quotient steps
from `q x` gives the same event law as observing with the source receiver after
`n` source steps from `x`.  The declarations above prove the typed source and
quotient sides separately; this proposition is the remaining semantic bridge.
-/
def FiniteHorizonReceiverLawPreserved
    {X : Type uX} {Q : Type uQ} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace E]
    (surface : MeasurableQuotientSurface X Q)
    (transition : Kernel X X)
    (receiver : C → Kernel X E)
    (repr : Q → X) (h_repr : Measurable repr) : Prop :=
  ∀ (c : C) (n : ℕ) (x : X) {event : Set E},
    MeasurableSet event →
      ((quotientReceiverKernelFromRepresentative receiver repr h_repr c) ∘ₖ
          ((quotientKernelFromRepresentative surface transition repr h_repr) ^ n))
          (surface.q x) event =
        ((receiver c) ∘ₖ (transition ^ n)) x event

/--
Base case for the exact finite-horizon receiver-law preservation target.  At
horizon zero, preservation follows from receiver lumpability and the
representative hitting the fibre of each source state.
-/
theorem finiteHorizonReceiverLawPreserved_zero_of_receiver_lumpable
    {X : Type uX} {Q : Type uQ} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace E]
    {surface : MeasurableQuotientSurface X Q}
    {transition : Kernel X X}
    {receiver : C → Kernel X E}
    (h_receiver_lumpable : QuotientReceiverLumpable surface receiver)
    {repr : Q → X} {h_repr : Measurable repr}
    (h_repr_hits : ∀ x : X, surface.q (repr (surface.q x)) = surface.q x)
    (c : C) (x : X) {event : Set E} (h_event : MeasurableSet event) :
    ((quotientReceiverKernelFromRepresentative receiver repr h_repr c) ∘ₖ
        ((quotientKernelFromRepresentative surface transition repr h_repr) ^ 0))
        (surface.q x) event =
      ((receiver c) ∘ₖ (transition ^ 0)) x event := by
  rw [pow_zero, pow_zero]
  change
    ((quotientReceiverKernelFromRepresentative receiver repr h_repr c) ∘ₖ
        (Kernel.id : Kernel Q Q)) (surface.q x) event =
      ((receiver c) ∘ₖ (Kernel.id : Kernel X X)) x event
  rw [Kernel.comp_id, Kernel.comp_id]
  exact quotientReceiverKernelFromRepresentative_apply_of_source_state
    h_receiver_lumpable c x (h_repr_hits x) h_event

/--
Receiver-law preservation reduces to transition-law preservation plus receiver
lumpability.

This is the second reusable `SGM-STEP-04` bridge: once the quotient transition
law is known to be the pushforward of the source transition law at every finite
horizon, every receiver that is constant on quotient fibres has the same
finite-horizon event law on the quotient process and the source process.  The
proof is intentionally assumption-explicit and does not claim that the
transition-preservation premise has already been recursively discharged.
-/
theorem finiteHorizonReceiverLawPreserved_of_transition_preserved
    {X : Type uX} {Q : Type uQ} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace E]
    {surface : MeasurableQuotientSurface X Q}
    {transition : Kernel X X}
    {receiver : C → Kernel X E}
    (h_receiver_lumpable : QuotientReceiverLumpable surface receiver)
    {repr : Q → X} {h_repr : Measurable repr}
    (h_repr_section : ∀ q_state : Q, surface.q (repr q_state) = q_state)
    (h_transition_preserved :
      FiniteHorizonQuotientTransitionLawPreserved
        surface transition repr h_repr) :
    FiniteHorizonReceiverLawPreserved
      surface transition receiver repr h_repr := by
  intro c n x event h_event
  let qkernel := quotientKernelFromRepresentative surface transition repr h_repr
  let qreceiver := quotientReceiverKernelFromRepresentative receiver repr h_repr c
  have h_transition_measure :
      (qkernel ^ n) (surface.q x) =
        Measure.map surface.q ((transition ^ n) x) := by
    ext s hs
    rw [h_transition_preserved n x hs]
    rw [Measure.map_apply surface.measurable_q hs]
  change (qreceiver ∘ₖ (qkernel ^ n)) (surface.q x) event =
    ((receiver c) ∘ₖ (transition ^ n)) x event
  rw [Kernel.comp_apply' _ _ _ h_event]
  rw [Kernel.comp_apply' _ _ _ h_event]
  rw [h_transition_measure]
  change (∫⁻ q_state, receiver c (repr q_state) event
      ∂Measure.map surface.q ((transition ^ n) x)) =
    ∫⁻ x_mid, receiver c x_mid event ∂((transition ^ n) x)
  have h_measurable_integrand :
      Measurable fun q_state => receiver c (repr q_state) event := by
    exact ((receiver c).measurable_coe h_event).comp h_repr
  rw [MeasureTheory.lintegral_map h_measurable_integrand surface.measurable_q]
  exact lintegral_congr fun x_mid =>
    h_receiver_lumpable c (h_repr_section (surface.q x_mid)) h_event

/--
Exact finite-horizon receiver-law preservation for an explicitly sectioned
lumpable quotient.

Combining transition lumpability, receiver lumpability, and a measurable
quotient section, the quotient process preserves every declared finite-horizon
receiver event law.  This is the scoped Markov/receiver closure theorem for the
explicit representative construction; canonical section existence and the
minimal stochastic refinement/no-go theorem remain separate obligations.
-/
theorem finiteHorizonReceiverLawPreserved_of_lumpable
    {X : Type uX} {Q : Type uQ} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace E]
    {surface : MeasurableQuotientSurface X Q}
    {transition : Kernel X X}
    {receiver : C → Kernel X E}
    (h_transition_lumpable : QuotientTransitionLumpable surface transition)
    (h_receiver_lumpable : QuotientReceiverLumpable surface receiver)
    {repr : Q → X} {h_repr : Measurable repr}
    (h_repr_section : ∀ q_state : Q, surface.q (repr q_state) = q_state) :
    FiniteHorizonReceiverLawPreserved
      surface transition receiver repr h_repr := by
  exact finiteHorizonReceiverLawPreserved_of_transition_preserved
    h_receiver_lumpable h_repr_section
    (finiteHorizonQuotientTransitionLawPreserved_of_lumpable
      h_transition_lumpable h_repr_section)

theorem quotientReceiverKernelFromRepresentative_law_independent_of_section_value
    {X : Type uX} {Q : Type uQ} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace E]
    {surface : MeasurableQuotientSurface X Q}
    {receiver : C → Kernel X E}
    (h_lumpable : QuotientReceiverLumpable surface receiver)
    {repr₁ repr₂ : Q → X} {h_repr₁ : Measurable repr₁} {h_repr₂ : Measurable repr₂}
    {c : C} {q_state : Q}
    (h_repr₁_hits : surface.q (repr₁ q_state) = q_state)
    (h_repr₂_hits : surface.q (repr₂ q_state) = q_state)
    {event : Set E} (h_event : MeasurableSet event) :
    quotientReceiverKernelFromRepresentative receiver repr₁ h_repr₁ c q_state event =
      quotientReceiverKernelFromRepresentative receiver repr₂ h_repr₂ c q_state event := by
  rw [quotientReceiverKernelFromRepresentative_apply receiver repr₁ h_repr₁ c q_state]
  rw [quotientReceiverKernelFromRepresentative_apply receiver repr₂ h_repr₂ c q_state]
  exact h_lumpable c (h_repr₁_hits.trans h_repr₂_hits.symm) h_event

/--
Closed stochastic quotient/lumpability obligation for the explicit
representative construction.

Once a measurable quotient surface has a measurable section, the source
transition is lumpable through the quotient, and the declared receiver kernels
are likewise quotient-lumpable, the stochastic quotient package is closed at
the level needed by the OC Core replay:

* the representative-pushforward quotient transition is a Markov kernel;
* every finite-horizon quotient transition law agrees with the pushed-forward
  source transition law;
* every declared finite-horizon receiver law is preserved by the quotient
  process.
-/
theorem scoped_stochastic_quotient_lumpability_obligation_closed
    {X : Type uX} {Q : Type uQ} {C : Type uC} {E : Type uE}
    [MeasurableSpace X] [MeasurableSpace Q] [MeasurableSpace E]
    {surface : MeasurableQuotientSurface X Q}
    {transition : Kernel X X} [IsMarkovKernel transition]
    {receiver : C → Kernel X E}
    (h_transition_lumpable : QuotientTransitionLumpable surface transition)
    (h_receiver_lumpable : QuotientReceiverLumpable surface receiver)
    {repr : Q → X} {h_repr : Measurable repr}
    (h_repr_section : ∀ q_state : Q, surface.q (repr q_state) = q_state) :
    IsMarkovKernel
        (quotientKernelFromRepresentative surface transition repr h_repr) ∧
      FiniteHorizonQuotientTransitionLawPreserved
        surface transition repr h_repr ∧
      FiniteHorizonReceiverLawPreserved
        surface transition receiver repr h_repr := by
  constructor
  · exact quotientKernelFromRepresentative_isMarkovKernel
      surface transition repr h_repr
  · constructor
    · exact finiteHorizonQuotientTransitionLawPreserved_of_lumpable
        h_transition_lumpable h_repr_section
    · exact finiteHorizonReceiverLawPreserved_of_lumpable
        h_transition_lumpable h_receiver_lumpable h_repr_section

end StochasticMetakernelMathlib
end OCMinimalObligationSpine
