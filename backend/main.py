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

from spark.variant_pipeline import (
    create_spark_session,
    process_vcf
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

    suffix = (
        ".vcf.gz"
        if file.filename.lower().endswith(".gz")
        else ".vcf"
    )

    temp_path = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp_file:

            temp_file.write(raw)
            temp_path = temp_file.name

        spark = create_spark_session()

        project_root = Path(__file__).resolve().parent.parent

        output_dir = (
            project_root
            / "data"
            / "processed"
            / "uploaded_variants_parquet"
        )

        output_dir.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        result = process_vcf(
            spark,
            temp_path,
            str(output_dir)
        )

        # ------------------------------------------
        # CLINVAR ANNOTATION
        # ------------------------------------------

        for variant in result.get("variants", []):

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

        result["filename"] = file.filename

        return result

    except Exception as exc:

        print(
            f"Spark processing error: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Spark processing failed: "
                f"{str(exc)}"
            )
        )

    finally:

        if (
            temp_path
            and os.path.exists(temp_path)
        ):
            os.remove(temp_path)
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