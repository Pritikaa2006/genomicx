import os
import sys
import tempfile

import json
sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )
)

from ml.annotate import (
    load_clinvar_annotations,
    annotate_variant
)

CLINVAR_ANNOTATIONS = load_clinvar_annotations()
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import re
import csv
from pathlib import Path

app = FastAPI(title="GenomicX API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "https://genomicx-dashboard.onrender.com",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
def root():
    return {
        "status": "online",
        "service": "GenomicX API",
        "version": "1.0.0"
    }
class PredictionInput(BaseModel):
    af_tgp: float
    af_exac: float
    af_esp: float
    ref_length: int
    alt_length: int

@app.get("/api/health")
def health(): return {"status":"ok","service":"GenomicX API"}
@app.get("/api/ai-metrics")
def ai_metrics():
    return {
        "model": "XGBoost",
        "dataset": {
            "records": 3806,
            "pathogenic": 128,
            "benign": 3678
        },
        "metrics": {
            "accuracy": 0.9659,
            "precision": 0.5000,
            "recall": 0.9231,
            "f1": 0.6486,
            "roc_auc": 0.9573,
            "pr_auc": 0.6406
        },
        "features": [
            {"name": "AF_EXAC", "importance": 4.253734},
            {"name": "AF_TGP", "importance": 3.592795},
            {"name": "AF_ESP", "importance": 0.875418},
            {"name": "REF length", "importance": 0.0},
            {"name": "ALT length", "importance": 0.0}
        ],
        "note": "Research/demo classification of ClinVar-labelled chromosome 22 variants. Not a medical diagnosis."
    }
@app.get("/api/benchmark")
def benchmark():

    benchmark_file = (
        Path(__file__).resolve().parent.parent
        / "benchmarks"
        / "results"
        / "benchmark_results.csv"
    )

    if not benchmark_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Benchmark results not found."
        )

    results = []

    with open(
        benchmark_file,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            results.append(
                {
                    "dataset_size": int(row["dataset_size"]),
                    "pandas_seconds": float(
                        row["pandas_seconds"]
                    ),
                    "pyspark_seconds": float(
                        row["pyspark_seconds"]
                    ),
                }
            )

    return {
        "benchmark": "Pandas vs PySpark",
        "execution_mode": "Spark local[*]",
        "repetitions": 3,
        "results": results
    }

def parse_info(info):
    out={}
    for item in info.split(';'):
        if '=' in item:
            k,v=item.split('=',1); out[k]=v
    return out

def parse_vcf(text: str):
    variants=[]
    for line in text.splitlines():
        if not line or line.startswith('#'): continue
        parts=line.split('\t')
        if len(parts)<8: continue
        info=parse_info(parts[7])
        ref,alt=parts[3],parts[4]
        vtype='SNP' if len(ref)==1 and len(alt)==1 else 'INDEL'
        try: pos=int(parts[1]); quality=float(parts[5]) if parts[5] not in ('.','') else 0.0
        except ValueError: continue
        try: af=float(info.get('AF',0))
        except ValueError: af=0.0
        variants.append({"chromosome":parts[0],"position":pos,"id":parts[2],"reference":ref,"alternate":alt,"quality":quality,"filter":parts[6],"allele_frequency":af,"variant_type":vtype})
    return variants

@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):

    if not file.filename.lower().endswith((".vcf", ".gz")):
        raise HTTPException(
            status_code=400,
            detail="Please upload a VCF or VCF.GZ file."
        )

    raw = await file.read()

    if not raw:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    try:
        # ------------------------------------------
        # READ VCF WITHOUT STARTING SPARK
        # ------------------------------------------

        import gzip
        import io

        if file.filename.lower().endswith(".gz"):
            raw = gzip.decompress(raw)

        text = raw.decode("utf-8", errors="replace")

        variants = []

        for line in io.StringIO(text):

            line = line.strip()

            if not line or line.startswith("#"):
                continue

            fields = line.split("\t")

            if len(fields) < 8:
                continue

            chromosome = fields[0]
            position = int(fields[1])
            variant_id = fields[2]
            reference = fields[3]
            alternate = fields[4]
            quality_raw = fields[5]
            filter_value = fields[6]
            info = fields[7]

            # ------------------------------------------
            # QUALITY
            # ------------------------------------------

            quality = None

            if quality_raw != ".":
                try:
                    quality = float(quality_raw)
                except ValueError:
                    quality = None

            # ------------------------------------------
            # INFO FIELDS
            # ------------------------------------------

            info_values = {}

            for item in info.split(";"):

                if "=" in item:
                    key, value = item.split("=", 1)
                    info_values[key] = value

            def get_float(key):
                value = info_values.get(key)

                if value in (None, "", "."):
                    return None

                try:
                    return float(value.split(",")[0])
                except ValueError:
                    return None

            def get_int(key):
                value = info_values.get(key)

                if value in (None, "", "."):
                    return None

                try:
                    return int(float(value.split(",")[0]))
                except ValueError:
                    return None

            af = get_float("AF")
            dp = get_int("DP")

            # ------------------------------------------
            # VARIANT TYPE
            # ------------------------------------------

            if len(reference) == 1 and len(alternate) == 1:
                variant_type = "SNP"
            else:
                variant_type = "INDEL"

            variants.append({
                "chromosome": chromosome,
                "position": position,
                "variant_id": variant_id,
                "reference": reference,
                "alternate": alternate,
                "quality": quality,
                "filter": filter_value,
                "AF": af,
                "DP": dp,
                "variant_type": variant_type
            })

        # ------------------------------------------
        # BASIC STATISTICS
        # ------------------------------------------

        total_variants = len(variants)

        snps = sum(
            1 for v in variants
            if v["variant_type"] == "SNP"
        )

        indels = sum(
            1 for v in variants
            if v["variant_type"] == "INDEL"
        )

        qualities = [
            v["quality"]
            for v in variants
            if v["quality"] is not None
        ]

        allele_frequencies = [
            v["AF"]
            for v in variants
            if v["AF"] is not None
        ]

        depths = [
            v["DP"]
            for v in variants
            if v["DP"] is not None
        ]

        mean_quality = (
            sum(qualities) / len(qualities)
            if qualities else None
        )

        mean_af = (
            sum(allele_frequencies) /
            len(allele_frequencies)
            if allele_frequencies else None
        )

        mean_dp = (
            sum(depths) / len(depths)
            if depths else None
        )

        # ------------------------------------------
        # CHROMOSOME DISTRIBUTION
        # ------------------------------------------

        chromosome_counts = {}

        for variant in variants:

            chromosome = variant["chromosome"]

            chromosome_counts[chromosome] = (
                chromosome_counts.get(chromosome, 0) + 1
            )

        chromosome_distribution = [
            {
                "chromosome": chromosome,
                "count": count
            }
            for chromosome, count
            in sorted(chromosome_counts.items())
        ]

        # ------------------------------------------
        # QC
        # ------------------------------------------

        rare_variants = sum(
            1 for v in variants
            if v["AF"] is not None and v["AF"] < 0.01
        )

        common_variants = sum(
            1 for v in variants
            if v["AF"] is not None and v["AF"] >= 0.05
        )

        high_depth_variants = sum(
            1 for v in variants
            if v["DP"] is not None and v["DP"] >= 10000
        )

        pass_variants = sum(
            1 for v in variants
            if v["filter"] == "PASS"
        )

        filtered_variants = sum(
            1 for v in variants
            if v["filter"] != "PASS"
        )

        # ------------------------------------------
        # CLINVAR ANNOTATION
        # ------------------------------------------

        for variant in variants:

            annotation = annotate_variant(
                CLINVAR_ANNOTATIONS,
                variant["chromosome"],
                variant["position"],
                variant["reference"],
                variant["alternate"]
            )

            variant["clinical_significance"] = (
                annotation["clinical_significance"]
            )

            variant["clinvar_id"] = (
                annotation["clinvar_id"]
            )

        # ------------------------------------------
        # API RESULT
        # ------------------------------------------

        result = {
            "summary": {
                "variants": total_variants,
                "snps": snps,
                "indels": indels,
                "chromosomes": len(chromosome_distribution),
                "mean_quality": mean_quality,
                "mean_af": mean_af,
                "mean_dp": mean_dp
            },

            "qc": {
                "rare_variants": rare_variants,
                "common_variants": common_variants,
                "high_depth_variants": high_depth_variants,
                "pass_variants": pass_variants,
                "filtered_variants": filtered_variants
            },

            "chromosome_distribution":
                chromosome_distribution,

            "variants":
                variants[:10],

            "filename":
                file.filename
        }

        return result

    except Exception as exc:

        print(
            f"VCF processing error: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"VCF processing failed: {str(exc)}"
        )
@app.post("/api/predict")
def predict(x: PredictionInput):

    try:
        from ml.predict import predict_variant

        result = predict_variant(
            af_tgp=x.af_tgp,
            af_exac=x.af_exac,
            af_esp=x.af_esp,
            ref_length=x.ref_length,
            alt_length=x.alt_length
        )

        return {
            "label": result["label"],
            "probability": result["probability"],
            "prediction": result["prediction"],
            "note": (
                "Research/demo classification of "
                "ClinVar-labelled genomic variants. "
                "Not a medical diagnosis."
            ),
            "features": [
                [
                    item["name"],
                    item["value"]
                ]
                for item in result["features"]
            ]
        }

    except Exception as exc:

        print(f"Prediction error: {exc}")

        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(exc)}"
        )