# ACIC 2022 Data Challenge — FAQ

This FAQ is based on the **official ACIC 2022 Data Challenge FAQ** originally published by **Mathematica**. Since the original website is currently not reachable, we maintain an **archived PDF copy** and reproduce the most relevant parts here in a **clean, repository-friendly format** (lightly paraphrased for clarity).

**Note:** Sections that are purely competition-specific are omitted, except for the **results/output format**, which can still be useful for evaluation tooling.

## Contents
- [A. Results / output format](#a-results--output-format)
- [B. Treatment, timing, and data structure](#b-treatment-timing-and-data-structure)
- [C. Assumptions and causal structure](#c-assumptions-and-causal-structure)
- [D. Variables and data types](#d-variables-and-data-types)
- [E. DGPs and dataset organization](#e-dgps-and-dataset-organization)

---

## A. Results / output format

## A. Results / output format

### Can I choose my own column names for results files?
Yes. However, to use the built-in evaluation tools, we **strongly recommend** sticking to the standard schema (see: [Results Format](https://github.com/JDenzel-UHH/CIDL/blob/main/documentation/ACIC22%20-%20Results%20Format.md)).

**Overall / by-year / by-subgroup SATT**
- `dataset.num, variable, level, year, satt, lower90, upper90`

**Practice-level SATT (if included)**
- `dataset.num, variable, level, year, id.practice, satt, lower90, upper90`

> Tip: Keep `variable`, `level`, and `year` consistent with the subgroup/year definitions used in the ACIC documentation to avoid ambiguous joins during evaluation.

---

## B. Treatment, timing, and data structure

### How can I identify which observations are receiving the treatment when?
Actual exposure happens **only when** `Z = 1` **and** `post = 1`.

- `Z` is a **time-invariant, practice-level** indicator of belonging to the *eventual* treatment group.
  - For a given practice (and its patients), `Z` is **0 in all four years** or **1 in all four years**.
- `post` is a **time-varying** indicator for whether the intervention period has begun:
  - `post = 0` in **Years 1–2**
  - `post = 1` in **Years 3–4**

Therefore, **the interaction `Z * post`** identifies actual receipt of the intervention.

### How is treatment status determined?
Treatment is assigned at the **practice level**, meaning all patients within the same practice share the same treatment-group membership (`Z`).

Treatment assignment can depend on:
- practice-level covariates (`X`),
- patient-level covariates (`V`), and
- **pre-treatment outcomes** (e.g., outcome values in Years 1 and 2).

### If both patient- and practice-level covariates are time-invariant, how can the outcome vary over time?
Two main reasons:
1. **Stochastic variation** (randomness) in outcomes over time.
2. The **response surface** (how covariates map to outcomes) can itself change over time.

Additionally, **practice-level averages of patient covariates** (in Track 2) can vary by year because they reflect the average characteristics of patients present in that practice-year (patient composition can change over time).

---

## C. Assumptions and causal structure

### What is the causal structure of the data?
In real-world applications, the true causal structure is unknown—analysts must rely on assumptions and/or flexible methods.

In ACIC22, the organizers explicitly **rule out unobserved confounding** in the simulated DGPs:
- there is **no unobserved variable `U`** that affects both the outcome `Y` and treatment assignment `Z`.

### The ignorability assumption for Years 3–4 requires pre-treatment outcomes, but these values don’t exist for everyone. Can we assume missingness depends only on pre-treatment observables?
Yes. In the DGPs, missingness of pre-period outcomes (e.g., due to “joining Medicare”) depends **only on pre-treatment observables**.

### The ignorability assumption states something like `Y_it1(0) - Y_it0(0) ⟂ Z_i | X_i`. What does `X_i` stand for here?
`X_i` is shorthand for **all pre-treatment observables**, including:
- measured covariates (`X1–X9` and `V1–V5`), and also
- other pre-treatment observables such as **pre-period outcomes** and **practice size**.

---

## D. Variables and data types

### What are the datatypes for each of the variables in the dataset?
The organizers grouped variables as follows:

**Continuous**
- `Y`, `V1`, `V2`, `V4`, `X6`, `X7`, `X8`, `X9`,
- practice-level averages (Track 2), e.g.:
  - `V1_avg`, `V2_avg`, `V3_avg`, `V4_avg`, `V5_A_avg`, `V5_B_avg`, `V5_C_avg`,
- and `n.patients`

**Unordered categorical** (each has 3 values)
- `X2`, `X4`, `V5`

**Binary**
- `V3`, `X1`, `X3`, `X5`

---

## E. DGPs and dataset organization

### Can participants tell which of the 3,400 datasets came from which of the 17 DGPs?
No. The relationship between datasets and DGPs was intentionally **obfuscated**.

Motivation: In real observational studies, it is usually unclear whether confounding exists (measured or unmeasured), how strong it is, and which factors drive it. The DGPs do **not** include unmeasured confounding, but dealing with a range of possible and unknown **measured confounding** scenarios is part of the challenge.

### What distinguishes the 17 DGPs and the 3,400 datasets?
- The **joint distribution** of `(Y, Z, post, X, V)` differs across the **17 DGPs** (e.g., degree/type of confounding).
- For each DGP, the organizers generated **200 datasets** using different random seeds.
  - That yields `17 × 200 = 3,400` datasets per track.

- This setup mirrors prior causal inference competitions.

