# ESG, Audit Quality, and Investment Efficiency: Synthetic Monte Carlo Diagnostics

This repository reproduces a **synthetic-data Monte Carlo diagnostic** for a two-stage panel workflow linking lagged ESG, a Big Four auditor indicator, and a residual-based investment outcome. It is not an empirical ESG study and contains no real-company financial, ESG, auditor, regulatory, or commercial-vendor observations.

> **Scope.** The package evaluates operating characteristics under a fully documented synthetic data-generating process (DGP). It does not estimate causal effects, validate Big Four status as a measure of audit or assurance quality, calibrate ESG-coverage probabilities, or support conclusions about real firms.

## What changed in the round-two revision

| Topic | Earlier implementation | Corrected round-two implementation |
|---|---|---|
| First-stage sample | The first stage was inadvertently fitted after second-stage lag/lead exclusions. | The first-stage expected-investment equation is fitted on the full **3,000-row** synthetic panel. The second stage then uses **2,400** lag/lead-valid rows. |
| Main evidence | Prior output paths reflected the former sample-flow implementation. | Reported primary results use `outputs/final_run_round2_*` and the two-seed pooled table. |
| Scale interpretation | The DGP log-SD interaction and log-absolute-residual coefficient were reported without an oracle mapping. | An oracle-versus-estimated-residual scale-mapping simulation distinguishes \(\gamma_{INT}\) from \(\beta_3\). |
| Availability | A single “MAR-like” label was used. | Complete, adverse selective-availability, and non-calibrated coverage-aligned synthetic stresses are reported. |
| First-stage FE | Overlap was discussed but not quantified across specifications. | Industry×year, industry+year, and no-first-stage-FE specifications report estimated-residual and oracle outcomes. |
| Big Four mechanism | Former ablation values were based on the former sample flow. | A corrected-sample-flow selection-only ablation is rerun and pooled over two independent seeds. |
| Figure 1 | The inference methods were not displayed side-by-side. | Pooled N=300 grouped bars distinguish firm-clustered and two-way firm–year rejection probabilities. |

## Key pooled synthetic findings

The primary N=300 null combines two independent master seeds and 2,000 outer repetitions. The firm-clustered 5% rejection frequency is **0.064** (MCSE 0.00547 before display rounding), and the two-way firm–year rate is **0.1035** (MCSE 0.00681). Under the full alternative, the corresponding rates are **0.246** and **0.287**. These values are operating characteristics of the specified DGP, not performance guarantees or empirical estimates.

The round-two time grid shows that two-way null rejection depends jointly on the number of analysable time clusters, ESG persistence, and the ESG-dependent residual-variance mechanism. At 28 clusters the two-way rate ranges from 0.043 to 0.081 across the specified grid. The package therefore does not posit a universal “safe” time-cluster threshold.

## Repository layout

```text
config/dgp.yaml                                  # Single source of truth for synthetic DGP settings
src/esg_monte_carlo.py                            # Synthetic DGP, two-stage estimators, covariance and bootstrap routines
src/compare_runs.py                               # Main two-seed pooling and Figure 1 generation
src/run_round2_diagnostics.py                     # Time, scale, availability, and first-stage-FE diagnostics
src/aggregate_round2_diagnostics.py               # Replicate-level pooling for round-two diagnostics
src/run_round2_big4_mechanism.py                  # Corrected-sample-flow Big Four mechanism ablation
src/aggregate_round2_big4_mechanism.py            # Replicate-level pooling for Big Four ablation
tests/test_pipeline.py                            # Core deterministic synthetic-pipeline checks
tests/test_reviewer_revision.py                   # Public aggregate-artifact checks; private DOCX audit is opt-in
data/public/synthetic_example_null.csv            # Synthetic schema example only
outputs/final_run_round2_pooled/                  # Pooled main aggregate table and Figure 1
outputs/round2_pooled/                            # Pooled time, scale, availability, and FE tables/figures
outputs/round2_big4_pooled/                       # Pooled corrected Big Four ablation table/figure
docs/REPOSITORY_BOUNDARY.md                       # Explicit public/private release boundary
```

## Environment

Python 3.11+ is recommended. Install package dependencies in an isolated environment:

```bash
python3 -m pip install -r requirements.txt
```

## Reproduce a lightweight public smoke run

The public package includes pooled results to reproduce the reported tables without rerunning the full Monte Carlo design. The following produces a small synthetic run and runs deterministic tests:

```bash
python3 tests/test_pipeline.py
python3 src/esg_monte_carlo.py \
  --seed 20260827 \
  --reps 3 \
  --sensitivity-reps 2 \
  --bootstrap-reps 19 \
  --output outputs/public_smoke
```

## Reproduce the complete reported synthetic runs

The reported run uses independent master seeds `20260827` and `20260828`, 1,000 primary repetitions per seed, 300 sensitivity repetitions per seed, and 399 inner firm-level restricted wild draws. These commands are computationally intensive:

```bash
python3 src/esg_monte_carlo.py --seed 20260827 --reps 1000 --sensitivity-reps 300 --bootstrap-reps 399 \
  --output outputs/final_run_round2_seed_20260827
python3 src/esg_monte_carlo.py --seed 20260828 --reps 1000 --sensitivity-reps 300 --bootstrap-reps 399 \
  --output outputs/final_run_round2_seed_20260828

python3 src/compare_runs.py \
  outputs/final_run_round2_seed_20260827/tables/table_2_monte_carlo_operating_characteristics.csv \
  outputs/final_run_round2_seed_20260828/tables/table_2_monte_carlo_operating_characteristics.csv \
  outputs/final_run_round2_pooled/tables/table_6_independent_seed_crosscheck.csv \
  --figure-output outputs/final_run_round2_pooled/figures/figure_1_primary_operating_characteristics_pooled.png
```

Run the round-two diagnostic grid and corrected Big Four ablation as follows:

```bash
for SEED in 20260827 20260828; do
  python3 src/run_round2_diagnostics.py --seed "$SEED" --reps 500 --output "outputs/round2_seed_$SEED"
  python3 src/run_round2_big4_mechanism.py --seed "$SEED" --reps 500 --output "outputs/round2_big4_seed_$SEED"
done

python3 src/aggregate_round2_diagnostics.py \
  --seed-dirs outputs/round2_seed_20260827 outputs/round2_seed_20260828 \
  --output outputs/round2_pooled
python3 src/aggregate_round2_big4_mechanism.py \
  --seed-dirs outputs/round2_big4_seed_20260827 outputs/round2_big4_seed_20260828 \
  --output outputs/round2_big4_pooled

python3 tests/test_reviewer_revision.py
```

## Statistical conventions

Binary rejection-rate MCSEs are computed from all pooled outer repetitions as \(\sqrt{\hat p(1-\hat p)/R}\). Coefficient-mean MCSEs are calculated from the stored replicate-level coefficient distribution as its sample standard deviation divided by \(\sqrt{R}\). The firm-level wild-bootstrap routine is a restricted Rademacher **firm-cluster** bootstrap; it is not a multiway wild bootstrap.

For the oracle DGP deviation \(u^*=\sigma(X)z\), with a standard-normal innovation independent of \(X\), \(E[\log|u^*|\mid X]=\log\sigma(X)+E[\log|z|]\). This explains the oracle scale mapping only under the stated DGP and exposure transformation. Estimated-residual coefficients may differ because of first-stage estimation, finite samples, fixed effects, standardization, and selective availability.

## Benchmark positioning and extension protocol

This is a **synthetic statistical diagnostic**, not a machine-learning benchmark. It therefore does not claim a state-of-the-art score or compare its rejection rates with ESG text-classification, question-answering, rating, or empirical-association results. The task definition, three scope-qualified ESG resources, non-comparable related-work table, internal calibration gaps, tested code optimizations, planned ablations, fixed comparison settings, future data-path recommendations, release templates, and physical delivery checklist are documented in [`docs/BENCHMARK_AND_EXPERIMENT_PROTOCOL.md`](docs/BENCHMARK_AND_EXPERIMENT_PROTOCOL.md). The directly paired firm-versus-two-way comparison—its joint-replication definition, MCSE, interval, public aggregate table, figure, and private-record boundary—is documented in [`docs/PAIRED_CLUSTER_DIAGNOSTIC.md`](docs/PAIRED_CLUSTER_DIAGNOSTIC.md).

## Data, license, and release boundary

All reported observations are synthetic. The public release intentionally excludes manuscript DOCX/PDF files, full seed-level outputs, replicate-level rows, raw SEC files, restricted ESG data, credentials, and private review materials. See [`docs/REPOSITORY_BOUNDARY.md`](docs/REPOSITORY_BOUNDARY.md) for the exact whitelist, prohibited patterns, sync procedure, and required clean-clone verification.

The source records discuss published research and provider pages only as literature/context. They do not license or distribute commercial ESG data and do not calibrate the simulation to a vendor database.

## Citation

If you use this package, cite the associated anonymous manuscript after its publication details are available. Until then, describe it as a synthetic Monte Carlo replication package and retain the methodological, non-empirical scope stated above.
