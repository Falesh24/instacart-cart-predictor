from pathlib import Path

# Automatically find the root directory of your project
ROOT_DIR = Path(__file__).resolve().parent.parent

# Define standard data pathways
RAW_DATA_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DATA_DIR = ROOT_DIR / "data" / "processed"
OUTPUTS_DIR = ROOT_DIR / "outputs"

# Define explicit paths to your raw CSV files
ORDERS_PATH = RAW_DATA_DIR / "orders.csv"
ORDER_PRODUCTS_PATH = RAW_DATA_DIR / "order_products__prior.csv"
PRODUCTS_PATH = RAW_DATA_DIR / "products.csv"

# Create directories if they don't exist yet
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    print(f"🚀 Project Root Verified: {ROOT_DIR}")
    print(f"📊 Checking Data Source: {ORDERS_PATH.exists() = }")
