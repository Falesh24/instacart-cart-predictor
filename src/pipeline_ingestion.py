import polars as pl
import logging
from src.config import ORDERS_PATH, ORDER_PRODUCTS_PATH, PRODUCTS_PATH

# Set up logging for production tracking
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def stream_and_merge_transactions():
    """
    Streams the massive Instacart dataset using Polars LazyFrames.
    Filters, aggregates, and builds a low-memory Customer-Product interaction matrix.
    """
    logging.info("⚡ Initializing Polars Lazy Query Streams...")

    # 1. Spin up Lazy readers (Does not load data into RAM yet, just creates the blueprint)
    lazy_orders = pl.scan_csv(ORDERS_PATH)
    lazy_interactions = pl.scan_csv(ORDER_PRODUCTS_PATH)
    lazy_products = pl.scan_csv(PRODUCTS_PATH)

    # 2. Optimize schema sizes to save massive RAM on your M1 chip
    lazy_interactions = lazy_interactions.select([
        pl.col("order_id").cast(pl.Int32),
        pl.col("product_id").cast(pl.Int32),
        pl.col("add_to_cart_order").cast(pl.Int16)
    ])

    lazy_orders = lazy_orders.select([
        pl.col("order_id").cast(pl.Int32),
        pl.col("user_id").cast(pl.Int32),
        pl.col("order_number").cast(pl.Int16),
        pl.col("order_dow").cast(pl.Int8),       # Day of Week
        pl.col("order_hour_of_day").cast(pl.Int8) # Hour of Day
    ])

    # 3. Chain execution parameters (Join operations)
    logging.info("🔗 Engineering the relational transaction matrix query...")
    
    # Merge interaction rows with user account information
    transaction_stream = lazy_interactions.join(
        lazy_orders, on="order_id", how="inner"
    ).join(
        lazy_products.select(["product_id", "product_name"]), on="product_id", how="inner"
    )

    # 4. Trigger the physical execution (.collect() forces the multi-threaded calculation)
    logging.info("🏃‍♂️ Running parallelized multi-threaded compilation (Rust Engine)...")
    final_df = transaction_stream.collect(streaming=True)
    
    logging.info(f"✅ Data Ingestion Successful! Matrix Shape: {final_df.shape}")
    return final_df

if __name__ == "__main__":
    df = stream_and_merge_transactions()
    print("\n--- Ingested Head Snapshot ---")
    print(df.head(5))
