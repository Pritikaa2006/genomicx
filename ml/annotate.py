import os


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

CLINVAR_FILE = os.path.join(
    BASE_DIR,
    "data",
    "clinical",
    "clinvar_chr22.vcf"
)

def load_clinvar_annotations():
    annotations = {}

    if not os.path.exists(CLINVAR_FILE):
        print("ClinVar annotation file not found. Continuing without ClinVar annotations.")
        return annotations

    with open(
        CLINVAR_FILE,
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as file:

        for line in file:

            if line.startswith("#"):
                continue

            parts = line.rstrip("\n").split("\t")

            if len(parts) < 8:
                continue

            chrom = parts[0]
            position = parts[1]
            ref = parts[3]
            alt = parts[4]
            info = parts[7]

            key = (
                chrom,
                position,
                ref,
                alt
            )

            annotations[key] = {
                "clinical_significance": extract_clinical_significance(info),
                "clinvar_id": extract_clinvar_id(info)
            }

    return annotations


def extract_clinical_significance(info):
    for field in info.split(";"):

        if field.startswith("CLNSIG="):
            value = field.split("=", 1)[1]

            return value.replace("_", " ")

    return "Not available"


def extract_clinvar_id(info):
    for field in info.split(";"):

        if field.startswith("ALLELEID="):
            return field.split("=", 1)[1]

    return "Not available"


def annotate_variant(
    annotations,
    chromosome,
    position,
    reference,
    alternate
):

    key = (
        chromosome,
        str(position),
        reference,
        alternate
    )

    return annotations.get(
        key,
        {
            "clinical_significance": "Not available",
            "clinvar_id": "Not available"
        }
    )