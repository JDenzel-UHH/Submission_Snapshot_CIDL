<div align="center">
  <img width="512" height="512" alt="CIDL_left_bottom_extracted" src="https://github.com/user-attachments/assets/5210f427-15b5-433c-8de3-df331794ca56" />
</div>

# CIDL — Accessing Data for Causal Inference Benchmarking

CIDL provides a simple, reproducible interface to **access and explore benchmark datasets** for developing and validating **causal inference methods**. The current release focuses on datasets created for the **Data Challenge**, held as part of the **Atlantic Causal Inference Conference 2022 (ACIC22)**.

CIDL was developed as part of a **Master’s thesis project** at the **University of Hamburg (UHH)** and is intended to support research in causal inference and predictive modeling.

> Naming convention: content prefixed with **ACIC22** is specific to the ACIC 2022 Data Challenge. **CIDL** is the broader framework and may include additional datasets in future versions.

---

## Purpose

CIDL targets researchers who want **ready-to-use benchmark data** for causal effect estimation, enabling **reproducible evaluation** and **comparison** of methods across standardized simulation settings.

---

## Where to find what?

### 1) Setup / access (required)
The datasets are stored on UHH’s S3-compatible (Cloudian) storage. To request and configure read-only access, follow: [ACIC22 — Access Configuration (S3)](https://github.com/JDenzel-UHH/CIDL/blob/main/documentation/ACIC22%20-%20Access%20Configuration%20(S3).md)

### 2) Data documentation
For an overview of the ACIC22 datasets (structure, variables, DGPs, target estimands), see: [ACIC22 — Data Info](https://github.com/JDenzel-UHH/CIDL/blob/main/documentation/ACIC22%20-%20Data%20Info.md)

If you have data- or modeling-related questions not covered there, see: [ACIC22 — FAQ](https://github.com/JDenzel-UHH/CIDL/blob/main/documentation/ACIC22%20-%20FAQ.md) (Archived from the official challenge documentation; the original website is currently not reachable.)

### 3) Hands-on example
- [Quickstart.py](https://github.com/JDenzel-UHH/CIDL/blob/main/example/Quickstart.py) — minimal “works end-to-end” example

---

## Installation

CIDL is currently available on PyPI as beta version `0.6.0`. Version `1.0.0` will be released after the assessment.

---

## Project Information


### License

This project is licensed under the **MIT License**.

### Author

**Julian Denzel**  
Master’s Thesis Project, University of Hamburg  
julian.denzel@studium.uni-hamburg.de


First issued: **April 2026**
