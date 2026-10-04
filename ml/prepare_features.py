import pandas as pd


CLINVAR_FILE = "data/clinical/clinvar_ml_dataset.csv"
GENOMIC_FILE = "data/processed/variants_parquet"
OUTPUT_FILE = "data/clinical/ml_features.csv"


def main():

    print("Loading ClinVar labels...")
    clinvar = pd.read_csv(CLINVAR_FILE)

    print("Loading 1000 Genomes features...")
    genomic = pd.read_parquet(GENOMIC_FILE)

    # Consistent data types
    clinvar["chromosome"] = clinvar["chromosome"].astype(str)
    genomic["chromosome"] = genomic["chromosome"].astype(str)

    clinvar["reference"] = clinvar["reference"].astype(str).str.upper()
    clinvar["alternate"] = clinvar["alternate"].astype(str).str.upper()

    genomic["reference"] = genomic["reference"].astype(str).str.upper()
    genomic["alternate"] = genomic["alternate"].astype(str).str.upper()

    clinvar["position"] = pd.to_numeric(
        clinvar["position"],
        errors="coerce"
    )

    genomic["position"] = pd.to_numeric(
        genomic["position"],
        errors="coerce"
    )

    # Exact variant-level match
    merged = clinvar.merge(
        genomic,
        on=[
            "chromosome",
            "position",
            "reference",
            "alternate"
        ],
        how="inner",
        suffixes=("_clinvar", "_genomic")
    )

    print(f"\nClinVar records: {len(clinvar):,}")
    print(f"1000 Genomes records: {len(genomic):,}")
    print(f"Exact variant matches: {len(merged):,}")

    if merged.empty:
        print("\nNo exact matches found.")
        return

    # Keep features suitable for the ML model
    features = merged[
        [
            "chromosome",
            "position",
            "reference",
            "alternate",
            "clinical_significance",
            "label",
            "AF",
            "DP",
            "EAS_AF",
            "EUR_AF",
            "AFR_AF",
            "AMR_AF",
            "SAS_AF",
            "NS"
        ]
    ].copy()

    features.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nFeature dataset saved to:")
    print(OUTPUT_FILE)

    print("\nClass distribution:")
    print(
        features["clinical_significance"]
        .value_counts()
    )

    print("\nPreview:")
    print(features.head())


if __name__ == "__main__":
    main()