
# GenomicX

### Scalable Genomic Data Processing, Variant Analytics & Explainable AI Platform

GenomicX is a research-focused genomic analytics platform that processes VCF genomic variant data, performs quality control and variant analysis, integrates ClinVar annotations, and provides explainable machine learning for ClinVar-labelled variant classification.

The platform combines scalable data processing, structured storage, machine learning, and an interactive web dashboard into a single workflow.

---

## 🚀 Live Demo

**Live Application:**  
https://genomicx-dashboard.onrender.com

**Backend API:**  
https://genomicx.onrender.com

---

## 🎯 Key Features

- VCF / VCF.GZ dataset ingestion
- Genomic variant validation and parsing
- Variant quality-control analytics
- SNP and INDEL classification
- Chromosome distribution analysis
- Allele-frequency and depth statistics
- ClinVar-based variant annotation
- XGBoost-based variant classification
- SHAP explainability
- Pandas vs PySpark scalability benchmarking
- PostgreSQL + Parquet storage architecture
- Interactive React dashboard
- Pipeline monitoring
- Variant annotation explorer
- Downloadable PDF analysis reports
- REST API using FastAPI
- Cloud deployment

---

## 🏗️ Architecture

```text
                    ┌──────────────────────┐
                    │     React Dashboard  │
                    │   GenomicX Frontend  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      FastAPI API     │
                    │      REST Backend    │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       VCF Processing      ML Pipeline      Annotation
              │                │                │
              ▼                ▼                ▼
          PySpark          XGBoost            ClinVar
              │                │
              │                ▼
              │              SHAP
              │
              ▼
       ┌───────────────┐
       │ Parquet / DB  │
       │ PostgreSQL    │
       └───────────────┘
