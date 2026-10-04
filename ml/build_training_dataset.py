import csv


INPUT_FILE = "data/clinical/clinvar_chr22.vcf"
OUTPUT_FILE = "data/clinical/training_dataset.csv"


def parse_info(info):
    values = {}

    for item in info.split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            values[key] = value

    return values


def get_float(info, key):
    value = info.get(key)

    if not value or value in {".", ""}:
        return None

    try:
        return float(value.split(",")[0])
    except ValueError:
        return None


records = []

with open(INPUT_FILE, "r") as f:

    for line in f:

        if line.startswith("#"):
            continue

        fields = line.rstrip("\n").split("\t")

        if len(fields) != 8:
            continue

        chromosome, position, variant_id, ref, alt, qual, filt, info = fields

        info_data = parse_info(info)

        clinical_significance = info_data.get("CLNSIG", "")

        # Keep only clear labels
        if clinical_significance == "Pathogenic":
            label = 1

        elif clinical_significance == "Benign":
            label = 0

        else:
            continue

        # Keep simple SNVs
        if len(ref) != 1 or len(alt) != 1:
            continue

        af_tgp = get_float(info_data, "AF_TGP")
        af_exac = get_float(info_data, "AF_EXAC")
        af_esp = get_float(info_data, "AF_ESP")

        # Keep variants with at least one population frequency
        if af_tgp is None and af_exac is None and af_esp is None:
            continue

        try:
            qual_value = float(qual) if qual != "." else None
        except ValueError:
            qual_value = None

        records.append({
            "chromosome": chromosome,
            "position": int(position),
            "reference": ref,
            "alternate": alt,
            "qual": qual_value,
            "af_tgp": af_tgp,
            "af_exac": af_exac,
            "af_esp": af_esp,
            "ref_length": len(ref),
            "alt_length": len(alt),
            "clinical_significance": clinical_significance,
            "label": label
        })


# Remove exact duplicate variants
unique_records = {}

for record in records:

    key = (
        record["chromosome"],
        record["position"],
        record["reference"],
        record["alternate"],
        record["label"]
    )

    unique_records[key] = record


records = list(unique_records.values())


fieldnames = [
    "chromosome",
    "position",
    "reference",
    "alternate",
    "qual",
    "af_tgp",
    "af_exac",
    "af_esp",
    "ref_length",
    "alt_length",
    "clinical_significance",
    "label"
]


with open(OUTPUT_FILE, "w", newline="") as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(records)


pathogenic = sum(r["label"] == 1 for r in records)
benign = sum(r["label"] == 0 for r in records)


print("\nTraining dataset created.")
print(f"Total records: {len(records):,}")
print(f"Pathogenic: {pathogenic:,}")
print(f"Benign: {benign:,}")
print(f"Saved to: {OUTPUT_FILE}")