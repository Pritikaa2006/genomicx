from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    split,
    when,
    avg,
    regexp_extract,
    count,
    length
)


def create_spark_session():
    spark = (
        SparkSession.builder
        .appName("GenomicX-Variant-Pipeline")
        .master("local[1]")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .getOrCreate()
    )
    return spark

    spark.sparkContext.setLogLevel("WARN")

    return spark


def load_vcf(spark, file_path):
    print("\nLoading VCF file...")

    raw_df = (
        spark.read
        .text(file_path)
    )

    return raw_df


def parse_vcf(raw_df):
    print("Parsing VCF data...")

    # Remove VCF metadata/header lines
    data_df = raw_df.filter(
        ~col("value").startswith("#")
    )

    # Split tab-separated VCF fields
    split_df = data_df.select(
        split(col("value"), "\t").alias("fields")
    )

    # Extract mandatory VCF fields
    variant_df = split_df.select(
        col("fields")[0].alias("chromosome"),

        col("fields")[1]
        .cast("integer")
        .alias("position"),

        col("fields")[2].alias("variant_id"),

        col("fields")[3].alias("reference"),

        col("fields")[4].alias("alternate"),

        when(
            col("fields")[5] == ".",
            None
        ).otherwise(
            col("fields")[5].cast("double")
        ).alias("quality"),

        col("fields")[6].alias("filter"),

        col("fields")[7].alias("info")
    )

    # Extract INFO fields
    variant_df = (
        variant_df

        .withColumn(
            "AC",
            regexp_extract(
                col("info"),
                r"(?:^|;)AC=([^;]+)",
                1
            )
        )

        .withColumn(
            "AN",
            regexp_extract(
                col("info"),
                r"(?:^|;)AN=([^;]+)",
                1
            )
        )

        .withColumn(
            "DP",
            regexp_extract(
                col("info"),
                r"(?:^|;)DP=([^;]+)",
                1
            )
        )

        .withColumn(
            "AF",
            regexp_extract(
                col("info"),
                r"(?:^|;)AF=([^;]+)",
                1
            )
        )

        .withColumn(
            "EAS_AF",
            regexp_extract(
                col("info"),
                r"(?:^|;)EAS_AF=([^;]+)",
                1
            )
        )

        .withColumn(
            "EUR_AF",
            regexp_extract(
                col("info"),
                r"(?:^|;)EUR_AF=([^;]+)",
                1
            )
        )

        .withColumn(
            "AFR_AF",
            regexp_extract(
                col("info"),
                r"(?:^|;)AFR_AF=([^;]+)",
                1
            )
        )

        .withColumn(
            "AMR_AF",
            regexp_extract(
                col("info"),
                r"(?:^|;)AMR_AF=([^;]+)",
                1
            )
        )

        .withColumn(
            "SAS_AF",
            regexp_extract(
                col("info"),
                r"(?:^|;)SAS_AF=([^;]+)",
                1
            )
        )

        .withColumn(
            "NS",
            regexp_extract(
                col("info"),
                r"(?:^|;)NS=([^;]+)",
                1
            )
        )
    )

    # Convert INFO fields safely.
    # Missing INFO values become NULL instead of
    # causing Spark ANSI casting errors.
    variant_df = (
        variant_df

        .withColumn(
            "AC",
            when(col("AC") == "", None)
            .otherwise(col("AC").cast("integer"))
        )

        .withColumn(
            "AN",
            when(col("AN") == "", None)
            .otherwise(col("AN").cast("integer"))
        )

        .withColumn(
            "DP",
            when(col("DP") == "", None)
            .otherwise(col("DP").cast("integer"))
        )

        .withColumn(
            "AF",
            when(col("AF") == "", None)
            .otherwise(col("AF").cast("double"))
        )

        .withColumn(
            "EAS_AF",
            when(col("EAS_AF") == "", None)
            .otherwise(col("EAS_AF").cast("double"))
        )

        .withColumn(
            "EUR_AF",
            when(col("EUR_AF") == "", None)
            .otherwise(col("EUR_AF").cast("double"))
        )

        .withColumn(
            "AFR_AF",
            when(col("AFR_AF") == "", None)
            .otherwise(col("AFR_AF").cast("double"))
        )

        .withColumn(
            "AMR_AF",
            when(col("AMR_AF") == "", None)
            .otherwise(col("AMR_AF").cast("double"))
        )

        .withColumn(
            "SAS_AF",
            when(col("SAS_AF") == "", None)
            .otherwise(col("SAS_AF").cast("double"))
        )

        .withColumn(
            "NS",
            when(col("NS") == "", None)
            .otherwise(col("NS").cast("integer"))
        )
    )

    return variant_df


def classify_variants(variant_df):
    print("Classifying variants...")

    classified_df = variant_df.withColumn(
        "variant_type",
        when(
            (length(col("reference")) == 1) &
            (length(col("alternate")) == 1),
            "SNP"
        ).otherwise("INDEL")
    )

    return classified_df


def calculate_statistics(variant_df):
    print("\n========== GENOMIC STATISTICS ==========")

    total_variants = variant_df.count()

    print(f"Total variants: {total_variants}")

    print("\nVariant types:")

    variant_df.groupBy("variant_type") \
        .count() \
        .show()

    print("\nChromosome distribution:")

    variant_df.groupBy("chromosome") \
        .count() \
        .orderBy("chromosome") \
        .show()

    print("\nAllele frequency statistics:")

    variant_df.select(
        avg("AF").alias("average_AF"),
        avg("DP").alias("average_DP")
    ).show()

    rare_variants = variant_df.filter(
        col("AF") < 0.01
    ).count()

    print(
        f"Rare variants (AF < 0.01): "
        f"{rare_variants}"
    )

    common_variants = variant_df.filter(
        col("AF") >= 0.05
    ).count()

    print(
        f"Common variants (AF >= 0.05): "
        f"{common_variants}"
    )

    high_depth_variants = variant_df.filter(
        col("DP") >= 10000
    ).count()

    print(
        f"High-depth variants (DP >= 10000): "
        f"{high_depth_variants}"
    )

    print("\nPopulation-specific allele frequencies:")

    variant_df.select(
        avg("EAS_AF").alias("East_Asian_AF"),
        avg("EUR_AF").alias("European_AF"),
        avg("AFR_AF").alias("African_AF"),
        avg("AMR_AF").alias("American_AF"),
        avg("SAS_AF").alias("South_Asian_AF")
    ).show()

    print("\nQuality statistics:")

    variant_df.select(
        avg("quality").alias("average_quality")
    ).show()

    print("\nTop variants by allele frequency:")

    variant_df.select(
        "chromosome",
        "position",
        "reference",
        "alternate",
        "variant_type",
        "AF",
        "DP"
    ).orderBy(
        col("AF").desc()
    ).show(10)

def build_api_summary(variant_df):
    """
    Create a compact JSON-friendly result for FastAPI.
    """

    total_variants = variant_df.count()

    snps = variant_df.filter(
        col("variant_type") == "SNP"
    ).count()

    indels = variant_df.filter(
        col("variant_type") == "INDEL"
    ).count()

    # Chromosome distribution
    chromosome_rows = (
        variant_df
        .groupBy("chromosome")
        .count()
        .orderBy("chromosome")
        .collect()
    )

    chromosome_distribution = [
        {
            "chromosome": row["chromosome"],
            "count": row["count"]
        }
        for row in chromosome_rows
    ]

    # Genomic QC statistics
    qc_row = (
        variant_df
        .select(
            avg("quality").alias("mean_quality"),
            avg("AF").alias("mean_af"),
            avg("DP").alias("mean_dp")
        )
        .collect()[0]
    )

    rare_variants = variant_df.filter(
        col("AF") < 0.01
    ).count()

    common_variants = variant_df.filter(
        col("AF") >= 0.05
    ).count()

    high_depth_variants = variant_df.filter(
        col("DP") >= 10000
    ).count()

    pass_variants = variant_df.filter(
        col("filter") == "PASS"
    ).count()

    filtered_variants = variant_df.filter(
        (col("filter").isNotNull()) &
        (col("filter") != "PASS")
    ).count()

    # First 10 variants for the dashboard
    variants = (
        variant_df
        .select(
            "chromosome",
            "position",
            "variant_id",
            "reference",
            "alternate",
            "quality",
            "filter",
            "AF",
            "DP",
            "variant_type"
        )
        .limit(10)
        .collect()
    )

    variant_list = []

    for row in variants:
        variant_list.append({
            "chromosome": row["chromosome"],
            "position": row["position"],
            "variant_id": row["variant_id"],
            "reference": row["reference"],
            "alternate": row["alternate"],
            "quality": row["quality"],
            "filter": row["filter"],
            "AF": row["AF"],
            "DP": row["DP"],
            "variant_type": row["variant_type"]
        })

    return {
        "summary": {
            "variants": total_variants,
            "snps": snps,
            "indels": indels,
            "chromosomes": len(chromosome_distribution),
            "mean_quality": qc_row["mean_quality"],
            "mean_af": qc_row["mean_af"],
            "mean_dp": qc_row["mean_dp"]
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
            variant_list
    }


def save_as_parquet(variant_df, output_path):
    print(
        f"\nSaving processed data to: {output_path}"
    )

    (
        variant_df
        .write
        .mode("overwrite")
        .parquet(output_path)
    )

    print(
        "Parquet data successfully created."
    )
def process_vcf(
    spark,
    input_file,
    output_path=None
):
    """
    Reusable Spark processing function.

    This is the function FastAPI will call when
    a user uploads a VCF file.
    """

    raw_df = load_vcf(
        spark,
        input_file
    )

    variant_df = parse_vcf(
        raw_df
    )

    variant_df = classify_variants(
        variant_df
    )

    result = build_api_summary(
        variant_df
    )

    if output_path:
        save_as_parquet(
            variant_df,
            output_path
        )

    return result


# --------------------------------------------------
# Standalone execution
# --------------------------------------------------

input_file = (
    "data/raw/1000genomes_chr22.vcf.gz"
)


def main():

    spark = create_spark_session()

    try:

        raw_df = load_vcf(
            spark,
            input_file
        )

        variant_df = parse_vcf(
            raw_df
        )

        variant_df = classify_variants(
            variant_df
        )

        print(
            "\n========== PROCESSED DATA =========="
        )

        variant_df.show(
            10,
            truncate=False
        )

        calculate_statistics(
            variant_df
        )

        save_as_parquet(
            variant_df,
            "data/processed/variants_parquet"
        )

    finally:

        spark.stop()


if __name__ == "__main__":
    main()