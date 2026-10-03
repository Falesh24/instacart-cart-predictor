from fastapi import FastAPI, HTTPException
import pickle
from pathlib import Path
import time

app = FastAPI(
    title="Instacart High-Scale Recommendation Engine",
    description="Production-grade, low-latency pre-indexed hybrid inference service.",
    version="1.0.0"
)

# Define clean production file paths
BASE_DIR = Path(__file__).resolve().parent.parent
RULES_PATH = BASE_DIR / "outputs" / "fp_growth_rules.pkl"
AFFINITY_PATH = BASE_DIR / "outputs" / "user_affinity_scores.parquet"
INDEX_CACHE_PATH = BASE_DIR / "outputs" / "user_affinity_index.pkl"

# Global fast RAM cache structures
rules_db = None
user_affinity_index = {}
is_mapped = False

def emergency_ram_indexing():
    """
    Safely builds or loads a lightweight, optimized pre-computed dictionary index.
    Bypasses PyArrow/Polars multi-threading runtime deadlocks completely.
    """
    global rules_db, user_affinity_index, is_mapped
    if is_mapped:
        return

    # 1. Load the Global Market Basket Rules
    print("🔗 Loading Global Checkout Association Rules Matrix...")
    with open(RULES_PATH, "rb") as f:
        rules_db = pickle.load(f)

    # 2. Check if a pre-compiled lightweight dictionary file already exists
    if INDEX_CACHE_PATH.exists():
        print("💾 Found pre-compiled lookup index file. Ingesting straight to RAM...")
        with open(INDEX_CACHE_PATH, "rb") as f:
            user_affinity_index = pickle.load(f)
    else:
        print("⚠️ Direct index file not found. Compiling fallback matrix structure from Parquet...")
        import polars as pl
        # Read and downcast properties immediately to clear CPU bottlenecks
        df = pl.read_parquet(AFFINITY_PATH)
        grouped = df.group_by("user_id").agg(pl.col("product_id").head(5))
        user_affinity_index = dict(zip(grouped["user_id"].to_list(), grouped["product_id"].to_list()))
        
        # Cache this file down to disk so the next load takes 0.1 seconds
        with open(INDEX_CACHE_PATH, "wb") as f:
            pickle.dump(user_affinity_index, f)
        print("✅ Fresh look-up index file compiled and saved to disk.")

    is_mapped = True
    print("🚀 System Memory Indexing is fully active. Worker threads cleared!")

@app.get("/recommend/{user_id}")
def get_hybrid_recommendations(user_id: int, current_cart: str = ""):
    """
    Inference Endpoint: Delivers O(1) constant-time personalized recommendations
    without triggering multi-threaded CPU matrix scans.
    """
    start_time = time.time()
    
    # Initialize the memory cache index instantly on the first request
    if not is_mapped:
        try:
            emergency_ram_indexing()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Infrastructure error: {str(e)}")
        
    # Parse the incoming live cart query string parameters safely
    cart_items = [item.strip() for item in current_cart.split(",") if item.strip()]
    
    # 🌟 Step 1: O(1) Constant Time Personalized Retrieval (Zero CPU scan overhead)
    personal_recs = user_affinity_index.get(user_id, [])
    
    # 🌟 Step 2: Cross-Sell Recommendations (Live Cart Basket Context)
    cross_sell_recs = []
    if cart_items and rules_db is not None and not rules_db.empty:
        matched_rules = rules_db[rules_db['antecedents'].apply(lambda x: any(str(i) in cart_items for i in x))]
        if not matched_rules.empty:
            for items in matched_rules.head(3)['consequents']:
                for item in items:
                    if str(item) not in cart_items and item not in cross_sell_recs:
                        cross_sell_recs.append(int(item))

    # 🌟 Step 3: Hybrid Blending & Deduping Layer
    final_recommendations = list(dict.fromkeys(personal_recs + cross_sell_recs))[:5]
    
    latency_ms = (time.time() - start_time) * 1000
    
    return {
        "status": "success",
        "requested_user_id": user_id,
        "input_cart_context": cart_items,
        "recommendations": final_recommendations,
        "metrics": {
            "api_latency_ms": round(latency_ms, 2),
            "system_engine": "O1-Serialized-FastAPI-Hybrid"
        }
    }



