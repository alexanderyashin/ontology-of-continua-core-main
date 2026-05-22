# OC 043 Operational Protocol

## Purpose

Convert a domain description into a bounded OC analysis without claiming more than evidence supports.

## Required Inputs

- domain name and source statement;
- observables;
- constraints and invariants;
- current state variables;
- candidate operators;
- pressure/contradiction statement;
- available evidence or replay surface;
- falsifier and acceptance criteria;
- intended use: scientific, publication, internal tool, product, or business.

## Procedure

1. Recover exact source statement.
2. Declare claim ceiling: formal, descriptive, empirical, product, business, or public.
3. Map observables and constraints.
4. Select typed operators and justify each role.
5. Define falsifier and counterexample search.
6. Bind evidence:
   - formal proof for formal claims;
   - executable replay or dataset for empirical claims;
   - no-send gate for product/business claims.
7. Run boundary checks:
   - no universal overclaim;
   - no empirical language without data;
   - no ROI/legal/client wording without external gate.
8. Emit one verdict:
   - proved at ceiling;
   - refuted;
   - repaired and proved at ceiling;
   - blocked by external evidence.

## Outputs

- source-bound proposition;
- OC variable/operator map;
- falsifier;
- evidence/replay artifact refs;
- dependency closure;
- allowed wording;
- forbidden wording;
- next action if blocked.
