import time
import os
import random
import pandas as pd

from pyspark.sql import SparkSession
from pyspark.sql.functions import count


OUTPUT_DIR = "benchmarks/results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DATA_SIZES = [10_000, 100_000, 500_000]


def generate_dataset(n):
    chromosomes = [f"chr{i}" for i in range(1, 23)]

    rows = []

    for i in range(n):
        chromosome = random.choice(chromosomes)
        position = random.randint(1, 250_000_000)
        quality = round(random.uniform(20, 100), 2)

        rows.append(
            {
                "chromosome": chromosome,
                "position": position,
                "quality": quality,
            }
        )

    return pd.DataFrame(rows)


def pandas_benchmark(df):

    start = time.perf_counter()

    result = (
        df.groupby("chromosome")
        .agg(
            variant_count=("position", "count"),
            average_quality=("quality", "mean"),
        )
        .reset_index()
    )

    elapsed = time.perf_counter() - start

    return elapsed, result


def spark_benchmark(spark, df):

    spark_df = spark.createDataFrame(df)

    start = time.perf_counter()

    result = (
        spark_df.groupBy("chromosome")
        .agg(
            count("position").alias("variant_count")
        )
        .collect()
    )

    elapsed = time.perf_counter() - start

    return elapsed, result


def main():

    spark = (
        SparkSession.builder
        .appName("GenomicX-Benchmark")
        .master("local[*]")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("ERROR")

    benchmark_results = []

    print("\n========== GENOMICX SCALABILITY BENCHMARK ==========\n")

    for size in DATA_SIZES:

        print(f"Generating {size:,} variants...")

        df = generate_dataset(size)

        pandas_time, _ = pandas_benchmark(df)

        spark_time, _ = spark_benchmark(
            spark,
            df
        )

        print(
            f"Pandas:  {pandas_time:.4f} seconds"
        )

        print(
            f"PySpark: {spark_time:.4f} seconds"
        )

        benchmark_results.append(
            {
                "dataset_size": size,
                "pandas_seconds": pandas_time,
                "pyspark_seconds": spark_time,
            }
        )

        print()

    results_df = pd.DataFrame(
        benchmark_results
    )

    output_file = (
        f"{OUTPUT_DIR}/benchmark_results.csv"
    )

    results_df.to_csv(
        output_file,
        index=False
    )

    print("========== RESULTS ==========")

    print(results_df)

    print(
        f"\nResults saved to: {output_file}"
    )

    spark.stop()


if __name__ == "__main__":
    main()