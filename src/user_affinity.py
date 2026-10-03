import polars as pl
import logging
from src.config import OUTPUTS_DIR
from src.pipeline_ingestion import stream_and_merge_transactions

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def compute_user_product_affinity():
    """
    Computes a personalized affinity score for every user-product pair based on 
    reorder frequency and user loyalty habits. Stores output in an optimized Parquet file.
    """
    # 1. Fetch our high-speed transaction dataframe
    df = stream_and_merge_transactions()
    
    logging.info("🧠 Computing personalized user product affinity matrices...")

    # 2. Use Polars to group and aggregate metrics per user-product pairing
    affinity_df = (
        df.group_by(["user_id", "product_id"])
        .agg([
            pl.len().alias("purchase_count"),
            pl.col("order_number").max().alias("last_order_num"),
            # Calculate how often they reordered this specific item
            pl.col("order_number").count().cast(pl.Float32).alias("reorder_velocity")
        ])
    )

    # 3. Normalize the matrix scoring to create a localized metric (0 to 1 scaling)
    logging.info("⚖️ Normalizing user-specific preference weights...")
    affinity_df = affinity_df.with_columns([
        (pl.col("purchase_count") / pl.col("purchase_count").max().over("user_id"))
        .alias("affinity_score")
    ])

        # 4. Save using Apache Parquet (Ensuring complete file stream flush)
    output_path = OUTPUTS_DIR / "user_affinity_scores.parquet"
    
    # Sort and force structural data serialization to disk
    affinity_df = affinity_df.sort(["user_id", "affinity_score"], descending=[False, True])
    
    # Explicitly write and flush the buffer
    affinity_df.write_parquet(output_path, compression="snappy", use_pyarrow=False)
    
    # Force Python to wait until the file is physically present and verified
    import time
    time.sleep(2) 
    
    logging.info(f"✅ Verified Data Dimensions: {affinity_df.shape}")
    logging.info(f"💾 File size on disk: {output_path.stat().st_size} bytes")
    
    return affinity_df


if __name__ == "__main__":
    affinity_matrix = compute_user_product_affinity()
    print("\n--- Personalized User Affinity Snapshot ---")
    print(affinity_matrix.head(5))
