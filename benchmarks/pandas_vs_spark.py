import os
import random
import time

import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, count


OUTPUT_DIR = "benchmarks/results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DATA_SIZES = [
    10_000,
    100_000,
    500_000,
    1_000_000,
    5_000_000,
]

REPEATS = 3


def generate_dataset(n):
    chromosomes = [f"chr{i}" for i in range(1, 23)]

    return pd.DataFrame(
        {
            "chromosome": random.choices(
                chromosomes,
                k=n
            ),
            "position": [
                random.randint(1, 250_000_000)
                for _ in range(n)
            ],
            "quality": [
                round(random.uniform(20, 100), 2)
                for _ in range(n)
            ],
        }
    )


def pandas_benchmark(df):
    times = []

    for _ in range(REPEATS):

        start = time.perf_counter()

        (
            df.groupby("chromosome")
            .agg(
                variant_count=("position", "count"),
                average_quality=("quality", "mean"),
            )
            .reset_index()
        )

        elapsed = time.perf_counter() - start
        times.append(elapsed)

    return sum(times) / len(times)


def spark_benchmark(spark, df):

    # Convert Pandas → Spark before timing.
    spark_df = spark.createDataFrame(df)

    # Warm-up run so Spark startup isn't included
    # in the actual benchmark.
    (
        spark_df.groupBy("chromosome")
        .agg(
            count("position").alias("variant_count"),
            avg("quality").alias("average_quality"),
        )
        .collect()
    )

    times = []

    for _ in range(REPEATS):

        start = time.perf_counter()

        (
            spark_df.groupBy("chromosome")
            .agg(
                count("position").alias("variant_count"),
                avg("quality").alias("average_quality"),
            )
            .collect()
        )

        elapsed = time.perf_counter() - start
        times.append(elapsed)

    return sum(times) / len(times)


def main():

    spark = (
        SparkSession.builder
        .appName("GenomicX-Scalability-Benchmark")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("ERROR")

    benchmark_results = []

    print("\n")
    print("=" * 60)
    print("        GENOMICX SCALABILITY BENCHMARK")
    print("=" * 60)
    print("\n")

    for size in DATA_SIZES:

        print(f"Generating {size:,} variants...")

        start_generation = time.perf_counter()

        df = generate_dataset(size)

        generation_time = time.perf_counter() - start_generation

        print(
            f"Data generation: {generation_time:.3f} seconds"
        )

        pandas_time = pandas_benchmark(df)

        print(
            f"Pandas average:  {pandas_time:.4f} seconds"
        )

        spark_time = spark_benchmark(
            spark,
            df
        )

        print(
            f"PySpark average: {spark_time:.4f} seconds"
        )

        benchmark_results.append(
            {
                "dataset_size": size,
                "pandas_seconds": round(
                    pandas_time,
                    6
                ),
                "pyspark_seconds": round(
                    spark_time,
                    6
                ),
            }
        )

        print("-" * 60)

        # Free the large DataFrame before next iteration.
        del df

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

    print("\n")
    print("=" * 60)
    print("                 RESULTS")
    print("=" * 60)
    print("\n")

    print(
        results_df.to_string(
            index=False
        )
    )

    print(
        f"\nResults saved to: {output_file}"
    )

    spark.stop()


if __name__ == "__main__":
    main()
    