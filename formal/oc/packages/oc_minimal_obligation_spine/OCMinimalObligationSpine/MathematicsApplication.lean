namespace OCMinimalObligationSpine.MathematicsApplication

def CHSHPRConstraints (a0 a1 b0 b1 : Bool) : Prop :=
  a0 = b0 /\
    a0 = b1 /\
    a1 = b0 /\
    Not (a1 = b1)

theorem chsh_pr_box_has_no_noncontextual_global_section :
    Not (Exists fun a0 : Bool =>
      Exists fun a1 : Bool =>
        Exists fun b0 : Bool =>
          Exists fun b1 : Bool => CHSHPRConstraints a0 a1 b0 b1) := by
  rintro ⟨a0, a1, b0, b1, h00, h01, h10, h11⟩
  apply h11
  exact h10.trans (h00.symm.trans h01)

def LiftedCHSHPRConstraints
    (a0 a1 b0 b1 contextualBit : Bool) : Prop :=
    a0 = b0 /\
    a0 = b1 /\
    a1 = b0 /\
    if contextualBit then a1 = b1 else Not (a1 = b1)

theorem zero_contextual_bits_are_insufficient :
    Not (Exists fun a0 : Bool =>
      Exists fun a1 : Bool =>
        Exists fun b0 : Bool =>
          Exists fun b1 : Bool =>
            LiftedCHSHPRConstraints a0 a1 b0 b1 false) := by
  simpa [LiftedCHSHPRConstraints, CHSHPRConstraints] using
    chsh_pr_box_has_no_noncontextual_global_section

theorem one_contextual_slack_bit_is_sufficient :
    Exists fun a0 : Bool =>
      Exists fun a1 : Bool =>
        Exists fun b0 : Bool =>
          Exists fun b1 : Bool =>
            LiftedCHSHPRConstraints a0 a1 b0 b1 true := by
  exact ⟨false, false, false, false, by simp [LiftedCHSHPRConstraints]⟩

theorem minimum_contextual_lift_dimension_is_one :
    (Not (Exists fun a0 : Bool =>
        Exists fun a1 : Bool =>
          Exists fun b0 : Bool =>
            Exists fun b1 : Bool =>
              LiftedCHSHPRConstraints a0 a1 b0 b1 false)) /\
      (Exists fun a0 : Bool =>
        Exists fun a1 : Bool =>
          Exists fun b0 : Bool =>
            Exists fun b1 : Bool =>
              LiftedCHSHPRConstraints a0 a1 b0 b1 true) := by
  exact And.intro zero_contextual_bits_are_insufficient
    one_contextual_slack_bit_is_sufficient

def FiberInvariant
    (relation : Setoid State) (kernel : State -> Law) : Prop :=
  forall left right, relation.r left right -> kernel left = kernel right

def quotientKernel
    (relation : Setoid State)
    (kernel : State -> Law)
    (invariant : FiberInvariant relation kernel) :
    Quotient relation -> Law :=
  Quotient.lift kernel (fun left right related => invariant left right related)

theorem quotient_kernel_computes_on_representatives
    (relation : Setoid State)
    (kernel : State -> Law)
    (invariant : FiberInvariant relation kernel)
    (state : State) :
    quotientKernel relation kernel invariant (Quotient.mk relation state) =
      kernel state := by
  rfl

theorem quotient_kernel_is_unique
    (relation : Setoid State)
    (kernel : State -> Law)
    (invariant : FiberInvariant relation kernel)
    (candidate : Quotient relation -> Law)
    (agreesOnRepresentatives : forall state,
      candidate (Quotient.mk relation state) = kernel state) :
    candidate = quotientKernel relation kernel invariant := by
  funext quotientState
  refine Quotient.inductionOn quotientState ?_
  intro state
  simpa [quotientKernel] using agreesOnRepresentatives state

theorem quotient_kernel_preserves_pointwise_laws
    (relation : Setoid State)
    (kernel : State -> Law)
    (invariant : FiberInvariant relation kernel)
    (law : Law -> Prop)
    (sourceLaw : forall state, law (kernel state)) :
    forall quotientState,
      law (quotientKernel relation kernel invariant quotientState) := by
  intro quotientState
  refine Quotient.inductionOn quotientState ?_
  intro state
  simpa [quotientKernel] using sourceLaw state

abbrev Event (Carrier : Type u) := Carrier -> Prop

def eventEmpty : Event Carrier := fun _ => False

def eventComplement (event : Event Carrier) : Event Carrier :=
  fun point => Not (event point)

def eventIUnion (events : Nat -> Event Carrier) : Event Carrier :=
  fun point => Exists fun index => events index point

def eventPreimage
    (mapping : Source -> Target) (event : Event Target) : Event Source :=
  fun point => event (mapping point)

structure SigmaSpace (Carrier : Type u) where
  measurable : Event Carrier -> Prop
  measurable_empty : measurable eventEmpty
  measurable_complement :
    forall event, measurable event -> measurable (eventComplement event)
  measurable_iUnion :
    forall events : Nat -> Event Carrier,
      (forall index, measurable (events index)) ->
        measurable (eventIUnion events)

def IsMeasurable
    (source : SigmaSpace Source)
    (target : SigmaSpace Target)
    (mapping : Source -> Target) : Prop :=
  forall event, target.measurable event ->
    source.measurable (eventPreimage mapping event)

def finalQuotientSigmaSpace
    (relation : Setoid State)
    (source : SigmaSpace State) :
    SigmaSpace (Quotient relation) where
  measurable := fun event =>
    source.measurable (eventPreimage (Quotient.mk relation) event)
  measurable_empty := by
    simpa using source.measurable_empty
  measurable_complement := by
    intro event measurableEvent
    simpa [eventPreimage, eventComplement] using
      source.measurable_complement
        (eventPreimage (Quotient.mk relation) event) measurableEvent
  measurable_iUnion := by
    intro events measurableEvents
    simpa [eventPreimage, eventIUnion] using
      source.measurable_iUnion
        (fun index => eventPreimage (Quotient.mk relation) (events index))
        measurableEvents

theorem invariant_measurable_kernel_descends_to_final_quotient
    (relation : Setoid State)
    (source : SigmaSpace State)
    (target : SigmaSpace Law)
    (kernel : State -> Law)
    (invariant : FiberInvariant relation kernel)
    (measurableKernel : IsMeasurable source target kernel) :
    IsMeasurable (finalQuotientSigmaSpace relation source) target
      (quotientKernel relation kernel invariant) := by
  intro event measurableEvent
  change source.measurable
    (eventPreimage (Quotient.mk relation)
      (eventPreimage (quotientKernel relation kernel invariant) event))
  have sourcePreimage :
      eventPreimage (Quotient.mk relation)
        (eventPreimage (quotientKernel relation kernel invariant) event) =
      eventPreimage kernel event := by
    funext state
    rfl
  rw [sourcePreimage]
  exact measurableKernel event measurableEvent

end OCMinimalObligationSpine.MathematicsApplication
