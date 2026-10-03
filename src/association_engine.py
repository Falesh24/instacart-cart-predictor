import polars as pl
import pandas as pd
from mlxtend.frequent_patterns import fpgrowth, association_rules
from mlxtend.preprocessing import TransactionEncoder
import pickle
import logging
from src.config import OUTPUTS_DIR
from src.pipeline_ingestion import stream_and_merge_transactions

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def build_market_basket_rules():
    """
    Memory-optimized market basket analysis using TransactionEncoder 
    and processing a scalable batch size safe for 8GB/16GB M1 Macs.
    """
    df = stream_and_merge_transactions()
    
    logging.info("📦 Grouping items into transaction baskets...")
    basket_df = (
        df.group_by("order_id")
        .agg(pl.col("product_id"))
        .select("product_id")
    )
    
    # Take a safe slice of 50,000 complete checkout baskets (plenty for high-quality rules)
    raw_transactions = basket_df["product_id"].to_list()[:50000]
    logging.info(f"🛒 Processing a memory-optimized slice of {len(raw_transactions)} baskets.")
    
        # 2. Use the specialized TransactionEncoder
    logging.info("📐 Encoding sparse matrix rows via TransactionEncoder...")
    te = TransactionEncoder()
    te_ary = te.fit(raw_transactions).transform(raw_transactions, sparse=True)
    
    # FIX: Cast column names as strings to satisfy Pandas sparse dataframe constraints
    string_column_names = [str(item_id) for item_id in te.columns_]
    
    # Build the DataFrame using the sanitized string column list
    flat_df = pd.DataFrame.sparse.from_spmatrix(te_ary, columns=string_column_names)
    
    logging.info(f"✨ Matrix conversion complete. Virtual array footprint memory allocation minimized.")

    # 3. Fit the FP-Growth Framework 
    logging.info("🧮 Running FP-Growth Frequent Pattern extraction...")
    # Increased min_support slightly to 0.002 to filter out noise quickly and speed up computing
    frequent_itemsets = fpgrowth(flat_df, min_support=0.002, use_colnames=True)
    
    logging.info(f"✨ Discovered {len(frequent_itemsets)} frequent transaction patterns.")
    
    if frequent_itemsets.empty:
        logging.warning("⚠️ No frequent itemsets found. Try lowering min_support.")
        return
        
    # 4. Generate Metric Association Rules
    logging.info("🔗 Building association rules using lift metrics...")
    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.0)
    rules = rules.sort_values(by="lift", ascending=False).reset_index(drop=True)
    
    # Convert itemsets back to strings/lists for easy consumption by our FastAPI layer
    rules['antecedents'] = rules['antecedents'].apply(lambda x: list(x))
    rules['consequents'] = rules['consequents'].apply(lambda x: list(x))
    
    # 5. Serialize the compiled rules engine model to disk
    output_path = OUTPUTS_DIR / "fp_growth_rules.pkl"
    with open(output_path, "wb") as f:
        pickle.dump(rules, f)
        
    logging.info(f"✅ Production Rules Saved successfully to: {output_path}")
    logging.info(f"📊 Total Rules Matrix Shape: {rules.shape}")
    
    return rules

if __name__ == "__main__":
    rules_matrix = build_market_basket_rules()
    if rules_matrix is not None and not rules_matrix.empty:
        print("\n--- Top 5 Strongest E-Commerce Checkout Rules ---")
        print(rules_matrix[["antecedents", "consequents", "support", "confidence", "lift"]].head(5))
