# Experimental Report: Monte Carlo Diagnostics

> **Interpretation boundary.** The results below measure the behavior of a specified synthetic DGP and estimator. They do **not** estimate the causal effect of ESG, audit quality, or investment efficiency in any empirical population.

## Experimental design

The first stage models expected investment using growth, CFO/assets, Q, cash/assets, leverage, firm age, and lagged investment with industry-by-year fixed effects. Its absolute residual is the estimated investment-inefficiency outcome. The second stage models log absolute residuals using lagged standardized ESG, lagged Big Four status, their interaction, firm fixed effects, and industry-by-year fixed effects.

The canonical DGP has 300 synthetic firms over 2015–2024; eight years remain after lag construction, giving 2,400 observations in the second stage. The primary size/power analysis uses 1,000 repetitions per condition under seed 20260827 and independently repeats it under seed 20260828. Sensitivity conditions use N=100 and N=500 with 300 repetitions per seed. All parameters are contained in `config/dgp.yaml`.

## Inference comparison

| Inference method | Intended role | Calibration result | Conclusion |
|---|---|---|---|
| Firm-clustered CR1 | Primary baseline | Pooled N=300 null rejection: 0.065 (MCSE 0.006; 2,000 repetitions) | Mildly oversized under this DGP. |
| Two-way firm–year CR1 | Stress diagnostic | Pooled N=300 null rejection: 0.111 (MCSE 0.007; 2,000 repetitions) | Materially oversized; do not call it a validated default with eight analysis years. |
| Restricted Rademacher wild cluster bootstrap-t at firm level | Finite-sample diagnostic | Pooled null rejection: 0.055 (MCSE 0.009; 600 outer repetitions; 399 inner draws each) | Closest to nominal among implemented diagnostics, but approximate. |

Cluster-robust standard errors rely on a sufficient number of clusters, while standard tests can over-reject with few clusters [1] [2]. The recent multiway-bootstrap literature further motivates direct calibration when time effects are serially correlated [3].

## Power and sample-size sensitivity

| Condition | Firm-clustered rejection | Two-way rejection | Interpretation |
|---|---:|---:|---|
| N=100, full alternative | 0.133 (MCSE 0.014) | 0.162 (MCSE 0.015) | Low power. |
| N=300, half alternative | 0.115 (MCSE 0.007) | 0.155 (MCSE 0.008) | Very limited detection probability. |
| N=300, full alternative | 0.234 (MCSE 0.009) | 0.285 (MCSE 0.010) | Moderate at best; not adequate for precise detection. |
| N=500, full alternative | 0.412 (MCSE 0.020) | 0.455 (MCSE 0.020) | Power improves with cross-sectional scale but remains below conventional 0.80 targets. |

Figure 1 reports the canonical-run curve. The table pools independent seeds and is the preferred summary because it reduces simulation noise.

## Ablation and robustness protocol

| Diagnostic | Question addressed | Expected use in a future empirical paper |
|---|---|---|
| First stage includes lagged ESG | Does omitted ESG information in the expected-investment model contaminate the residual outcome? | Treat change in coefficient as first-stage sensitivity, not confirmation. |
| Raw versus log absolute residual | Is the result driven by the scale transformation? | Report both scale choices, with a predeclared primary outcome. |
| Oracle true deviation | How much is lost when a latent disturbance is replaced with an estimated residual? | Available only in simulation; use to diagnose measurement distortion. |
| MAR-like ESG missingness | Does complete-case analysis react to nonuniform ESG availability? | Require a documented missing-data protocol, multiple-imputation sensitivity where justified, and provider coverage assessment. |
| Firm-block circular-shift ESG placebo | Does timing/dependence produce association after disrupting original alignment? | A significant placebo is a warning flag, not a robustness success. |
| Lead-ESG placebo | Does future exposure predict a prior residual outcome? | Use as a negative-control timing check. |

## Required fixed design choices for comparisons

When comparing alternative implementations inside this synthetic study, three specifications must stay fixed unless the comparison explicitly changes one of them.

| Fixed choice | Canonical value | Reason |
|---|---|---|
| Panel support and lag rule | 300 firms; 2015–2024 DGP; 2016–2023 second-stage years | Controls effective N=2,400 and exposure timing. |
| DGP effect scale and residual variance | Null: 0; half: −0.05/−0.06; full: −0.10/−0.12 on log SD; base SD=0.032 | Makes size/power contrasts interpretable. |
| Inference configuration | α=0.05; firm clustering primary; 399 firm-level restricted Rademacher bootstrap draws for calibration | Avoids attributing differences to a changing inferential target. |

## Research-positioning rather than SOTA comparison

This topic has no defensible common ‘Top-5 SOTA score.’ Relevant studies are empirical panels, analytical models, and systematic reviews with different populations and estimands. Their results cannot be ranked using a shared accuracy metric. The revised paper therefore uses a research-positioning table and reports **size, power, and MCSE** for this simulation, consistent with its methodological purpose. The theme is connected to real-world empirical work on China A-share firms [4], recent theoretical work on disclosure and investment [5], and a China–US bank panel [6], but none provides a direct performance baseline for this DGP.

## Sources

[1] Cameron, A. C., Gelbach, J. B., & Miller, D. L. (2008). Bootstrap-based improvements for inference with clustered errors. *Review of Economics and Statistics*, 90(3), 414–427. [https://doi.org/10.1162/rest.90.3.414](https://doi.org/10.1162/rest.90.3.414)

[2] Cameron, A. C., & Miller, D. L. (2015). A practitioner’s guide to cluster-robust inference. *Journal of Human Resources*, 50(2), 317–372. [https://doi.org/10.3368/jhr.50.2.317](https://doi.org/10.3368/jhr.50.2.317)

[3] Hounyo, U., & Lin, J. (2026). Wild bootstrap inference with multiway clustering and serially correlated time effects. *Journal of Business & Economic Statistics*, 44(2), 601–612. [https://doi.org/10.1080/07350015.2025.2546454](https://doi.org/10.1080/07350015.2025.2546454)

[4] Wang, W., Yu, Y., & Li, X. (2022). ESG performance, auditing quality, and investment efficiency: Empirical evidence from China. *Frontiers in Psychology*, 13, 948674. [https://doi.org/10.3389/fpsyg.2022.948674](https://doi.org/10.3389/fpsyg.2022.948674)

[5] Xue, H. (2025). ESG disclosure, market forces, and investment efficiency. *The Accounting Review*, 100(5), 439–467. [https://doi.org/10.2308/TAR-2023-0707](https://doi.org/10.2308/TAR-2023-0707)

[6] Zheng, C., Khan, M. A. M., Ul-Huq, S. M., Lau, C. K. M., & Islam, R. (2025). The impact of ESG performance on investment efficiency in Chinese and US banks: The moderating role of environmental uncertainty. *European Journal of Finance*, 31(13), 1655–1680. [https://doi.org/10.1080/1351847X.2025.2585972](https://doi.org/10.1080/1351847X.2025.2585972)
