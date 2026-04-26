# Reproducibility

Run from the DRT repository root:

```powershell
python tools/run_workflow.py doctor
python tools/run_workflow.py sims
python tools/run_workflow.py figs
python tools/run_workflow.py pdf
```

On the audited host, doctor, simulations, and figure generation pass. PDF rebuild is blocked because the LaTeX wrapper requires Perl. DRT therefore remains fail-closed.
