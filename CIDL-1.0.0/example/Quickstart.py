"""
Quickstart (CIDL / ACIC22)

Minimal end-to-end test:
1) Load two example datasets into RAM
2) Load matching ground-truth effects
3) Print small previews for quick inspection

Prerequisites:
- CIDL installed (see documentation/CIDL - Installation Guide.md)
- S3 access configured (see documentation/ACIC22 - Access Configuration (S3).md)

Go further:
- Data documentation: documentation/ACIC22 - Data Info.md
- FAQ: documentation/ACIC22 - FAQ.md
- Results schema: documentation/ACIC22 - Results Format.md
- Full workflow notebook: example/Standard Workflow.ipynb
"""

import cidl.data_loader as loader
import cidl.truth_loader as truth

INDICES = [1, 12]

def main():
    data_dict = loader.load_datasets(indices=INDICES)
    truth_dict = truth.load_truth(indices=INDICES)

    print(f"Loaded {len(data_dict)} dataset(s): {sorted(data_dict.keys())}")
    for idx in INDICES:
        df = data_dict[idx]
        print(f"Dataset {idx}: shape={df.shape}, first columns={list(df.columns)[:10]}...")
    print(f"Loaded truth for {len(truth_dict)} dataset(s): {sorted(truth_dict.keys())}")
    print("Quickstart OK: datasets and ground truth loaded successfully.")

    return data_dict, truth_dict

if __name__ == "__main__":
    data_dict, truth_dict = main()

    df1 = data_dict[1]
    print("Dataset 1 — head():")
    print(df1.head())

    truth1 = truth_dict[1]
    print("Truth 1 — head():")
    print(truth1.head()) 
