import OCMaturityCompletionCycle.EmpiricalCouplingPrediction

/-!
These fixtures encode the exact failure modes of the empirical prediction.
They show that conditional separation and nondegenerate regime support are
material; they are not empirical evidence that either condition holds.
-/

#check OCMaturityCompletionCycle.couplingBlindSignature_no_exactPredictiveStitcher
#check OCMaturityCompletionCycle.couplingAugmentedSignature_restores_exactPredictiveStitching
#check OCMaturityCompletionCycle.noConditionalSeparation_noBrierGain
#check OCMaturityCompletionCycle.degenerateRegimeWeight_noBrierGain
