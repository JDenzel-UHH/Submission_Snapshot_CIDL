# ACIC 2022 — Data Documentation

This document explains the **ACIC 2022 Data Challenge** datasets: **synthetic longitudinal data** designed to **mirror real-world U.S. health policy evaluations** (aiming to reduce **Medicare expenditures**), while providing **ground truth effects** for benchmarking causal methods.

If you want to **run code immediately**, see the repository’s [Quickstart.py](https://github.com/JDenzel-UHH/CIDL/blob/main/example/Quickstart.py).


If you have **data- or modeling-related** questions that are not covered in this documentation, please also see the [ACIC22 FAQ](https://github.com/JDenzel-UHH/CIDL/blob/main/documentation/ACIC22%20FAQ.md).

---

## 1) What are the ACIC22 datasets?

ACIC22 provides **simulated datasets** inspired by a real intervention evaluation. The intervention context is kept generic, but the DGPs (data generating processes) use **summaries** of a real Medicare-like dataset: empirical CDFs, covariate relationships, and intra-class correlations. Importantly, **covariates, outcomes, and treatment assignment are all simulated**, and simulated observations do **not** correspond to real patients/practices.

---

## 2) How many datasets are there? How are they organized?

### Two tracks (same target estimands)
ACIC22 offers two “tracks” to estimate **patient-level effects**

- **Track 1 (patient-level):** ~300,000 patients from ~500 practices over 4 years (~1.2M patient-year rows per dataset).
- **Track 2 (practice-level):** the Track 1 data **aggregated to practice-year means**. Includes `n.patients` for weighting.

### Dataset count
Each track contains **200 realizations** of **17 data-generating processes (DGPs)**:  
**17 × 200 = 3,400 datasets per track**.

### Important: DGP identity is hidden
The mapping “dataset number → DGP” is **purposefully obfuscated** within th datasets (to mimic real-world uncertainty about what drives confounding / heterogeneity). However CIDL provides you with opprtunities to take DGPs into consideration when choosing your datasets. The mapping which dataset belongs to which DGP is given within the truths.

---

## 3) What makes causal inference hard in ACIC22 (and in the real world)?

ACIC22 intentionally “bakes in” several empirical difficulties typical of observational health policy evaluations:

1. **Non-random participation (measured confounding):** practices voluntarily participate; treated and control practices differ systematically.
2. **Longitudinal structure + clustering:** patients are observed over time and clustered within practices. 
3. **Patients enter and leave:** the panel is “open” at the patient level (practice panel is stable).
4. **Highly skewed outcomes:** Medicare spending is variable and skewed (a few very expensive cases).
5. **Impact heterogeneity:** effects differ across subgroups and practices; some may benefit while others may not.

**Critical note:** ACIC22 rules out **unobserved confounding** (see assumptions), but still includes **strong, unknown measured confounding** patterns—which is often where methods fail in practice.

---

## 4) What variables are included? (Data dictionary)

### Common structure: clustering and time
- pateints are clustered within **primary care practices**.
- Treatment is assigned at the **practice level** (all patients in a treated practice share treatment group membership).

### Time
- `year ∈ {1,2,3,4}`
- Years **1–2** are baseline (no intervention); Years **3–4** are intervention period for treated practices.

### Track 1 (patient-year rows)
Unique key: `(id.patient, year)`

Columns:
- `id.patient`: patient identifier  
- `id.practice`: practice identifier  
- `Z`: practice’s treatment-group indicator (`Z=1` treated group, `Z=0` control), **time-invariant** per practice  
- `year`: 1–4  
- `post`: intervention-period indicator (`post=0` in Years 1–2, `post=1` in Years 3–4)  
- `Y`: outcome = **monthly Medicare expenditures** (per patient-year)  
- `X1`–`X5`: practice covariates (binary / unordered categorical), used to define subgroup estimands  
- `X6`–`X9`: additional practice covariates  
- `V1`–`V5`: patient covariates (continuous / unordered categorical / binary)

### Track 2 (practice-year rows, aggregated)
Unique key: `(id.practice, year)`

Same idea, but:
- **no `id.patient`**
- variables are mostly **practice-year averages** of Track 1 patient covariates/outcomes
- `n.patients`: number of patients in practice `id.practice` in `year` (for weighting)

### Data types (useful for preprocessing)
- **Continuous:** `Y`, `V1`, `V2`, `V4`, `X6`–`X9`, practice-level averages (e.g., `V1_avg` …), and `n.patients`
- **Unordered categorical:** `X2`, `X4`, `V5` (each has 3 values)
- **Binary:** `V3`, `X1`, `X3`, `X5`

---

## 5) How were the datasets generated? (DGP overview)

### Base ingredients
- Covariate distributions are constructed to **mirror** a real Medicare-like dataset using empirical summaries (marginals/joints, relationships, ICCs).
- Some covariates are **constructed** (no real-world counterpart) to control confounding strength precisely.
- **All covariates are fixed at baseline values** (the intervention does not affect covariates).
- Treatment and response surfaces are **constructed**; only the outcome’s marginal distribution is calibrated to the real data.

### What differs across the 17 DGPs (“knobs”)
The official results slides describe the design as 17 settings formed by varying:

**A) Confounding**
- **Strength:** Strong = **75%** of selection due to confounders; Weak = **50%**.
- **Source:**  
  - Scenario A: selection depends on **pre-intervention outcome change**(trend-related confounding) and on a **complex varying function of covariates**
  - Scenario B: selection depends on a **complex varying function of covariates**

**B) Impact heterogeneity**
- **Magnitude:** SD of practice-level effects: Large = **$42**, Small = **$17**
- **Idiosyncrasy:** Large = **80%** idiosyncratic, Small = **20%** idiosyncratic
- Drivers include observable subgroup structure (via `X1`–`X5`), practice characteristics, patient age, practice size, plus idiosyncratic components.

---

## 6) Target(s): what should be predicted/estimated?

ACIC22 targets **SATT** (Sample Average Treatment Effect on the Treated): average intervention effect on **monthly spending** among treated patients in the **observed sample** (not a population expectation).

### Core estimands
1. **Overall SATT:** averaged over the two post-intervention years (Years 3–4).
2. **SATT by year:** separate targets for Year 3 and Year 4 (short-run vs longer-run).
3. **Subgroup SATTs (often called CATTs in the slides):** for subgroups defined by each level of `X1`–`X5` (e.g., `X2=A/B/C`).
4. **Practice-specific effects (optional):** practice-level effect estimates for each treated practice (averaged over Years 3–4).

### Track 2 weighting (common mistake)
Even in Track 2, the target is still the **patient-level SATT**, so practice-year values must be aggregated using **weights based on `n.patients`** (practice sizes vary).

---

## 7) Treatment definition

**Actual exposure to the intervention is the interaction `Z * post`:**
- `Z` indicates membership in the *eventual* treatment group and is **time-invariant** per practice (0 for all years or 1 for all years).
- `post` is 0 in Years 1–2 and 1 in Years 3–4 for everyone.
- Therefore, a unit is treated when **`Z=1 AND post=1`**.

---

## 8) Assumptions baked into the DGPs (identifiability)

To make the estimands identifiable, the DGPs satisfy:

1. **Ignorability (no unmeasured confounding):** no unobserved covariates drive both treatment assignment and the change in untreated potential outcomes from pre (Years 1–2) to post (Years 3–4).
   - Note: this does **not** exclude confounding by **observed** pre-period outcome trends.
2. **Overlap for the treatment group:** treated units have treatment probability strictly less than 1 given covariates.

Missing pre-period outcomes for some Year 3–4 patients are also handled: missingness (e.g., “joining Medicare”) depends only on **pre-treatment observables** in these DGPs.

---

## References (official ACIC22 documents)

The official documentation for the ACIC 2022 Data Challenge was provided by Mathematica. At the time of writing, the original website is no longer reachable. For transparency and reproducibility, we maintain archived PDF copies of the official documentation (mirroring the original site content).

