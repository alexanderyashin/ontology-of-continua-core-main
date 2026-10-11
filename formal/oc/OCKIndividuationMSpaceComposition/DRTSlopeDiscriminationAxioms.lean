import OCKIndividuationMSpaceComposition.DRTSlopeDiscrimination

/-!
# Trusted-base audit for finite-error DRT discrimination

This module is intentionally an executable audit, not a theorem export.  Its
compiler output is retained in the managed DAG receipt: the four public DRT
selection results must have no axioms beyond Lean's standard trusted logical
base used by the existing OC corpus.
-/

#print axioms OCKIndividuationMSpaceComposition.bounded_slope_error_selects_nearer_model
#print axioms OCKIndividuationMSpaceComposition.drt_cubic_quadratic_slope_gap
#print axioms OCKIndividuationMSpaceComposition.drt_error_below_one_twelfth_selects_cubic
#print axioms OCKIndividuationMSpaceComposition.drt_error_below_one_twelfth_selects_quadratic
#print axioms OCKIndividuationMSpaceComposition.midpoint_slope_is_not_a_unique_model_selection
