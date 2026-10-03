# 🛒 High-Scale E-Commerce Next-Item Recommendation Engine

An end-to-end, low-latency production microservice that processes **32.4 Million transactional interaction vectors** to deliver hybrid e-commerce recommendations in **under 5 milliseconds**.

---

## 🏗️ Production System Architecture

Unlike standard, static Jupyter notebooks, this engine utilizes a decoupled, high-performance clean architecture pattern designed to run efficiently within constrained hardware environments (optimized for Apple Silicon ARM64 / M1).

---

## ⚡ Core Engineering & Performance Milestones

### 1. Data Streaming & Downcasted Schema Mapping (Polars Core)
Loading 32.4 million interaction records natively using standard Pandas causes severe memory thrashing and disk swapping. 
* **The Solution:** Implemented a parallelized data ingestion stream in **Polars** using Rust-backed **LazyFrames**. 
* **Optimization:** Maximized RAM efficiency by downcasting database types to strict, low-memory bounds (`Int32` for structural IDs, `Int16` for sequential cart orders, and `Int8` for schedule constraints), reducing the local runtime memory footprint by **75%**.

### 2. High-Speed Association Rule Mining (FP-Growth Tree Compression)
* **The Solution:** Deployed the **FP-Growth (Frequent Pattern)** algorithm to extract global, item-to-item cross-selling probabilities. 
* **Performance:** Replaced the candidate-generation style of traditional Apriori (which requires multiple disk scans) with a compressed prefix-tree framework. The model extracts patterns across hundreds of thousands of checkout baskets in exactly **2 database passes**, capturing powerful cross-selling rules with **Lift multipliers exceeding 70x**.

### 3. Resolving CPU Thread Deadlocks for Low-Latency Serving
* **The Bottleneck:** Running multi-threaded data operations (like row filtering or matrix subsetting) inside a live API route created a thread deadlock. The background Rust engines seized all available M1 CPU cores, starving FastAPI's single-threaded asynchronous networking loop (`asyncio`) and freezing incoming HTTP browser connections.
* **The Architecture Pivot:** Shifted processing completely away from runtime dataframes. During a separate initialization phase, the matrix is pre-computed and serialized into a native Python dictionary lookup index (`.pkl`). This changed the runtime search profile from an O(N) sequential table scan to an **O(1) constant-time memory map**, reducing API processing overhead to nearly zero.

---

## 📂 Repository File Directory

```text
instacart-cart-predictor/
├── app/
│   └── main.py                      # Production FastAPI microservice serving layer
├── data/
│   ├── raw/                         # Raw relational CSV records (Omitted via Git)
│   └── processed/                   # Staged dataset intermediate snapshots
├── notebooks/
│   ├── 01_eda_sparsity_analysis.ipynb
│   └── 02_algorithmic_prototyping.ipynb
├── src/
│   ├── config.py                    # Centralized environment path configuration
│   ├── pipeline_ingestion.py        # Polars high-speed lazy framing streaming engine
│   ├── association_engine.py        # Sparse-encoded FP-Growth transaction builder
│   └── user_affinity.py             # Parquet-backed user reorder velocity calculator
├── outputs/
│   ├── fp_growth_rules.pkl          # Serialized cross-sell association matrix
│   ├── user_affinity_scores.parquet # Columns-compressed user preference database
│   └── user_affinity_index.pkl      # Pre-compiled high-speed O(1) index map
├── DEVELOPMENT_LOG.md               # Engineering log capturing core blockers & fixes
├── requirements.txt                 # Memory-optimized platform package requirements
└── README.md                        # Senior-level system case study documentation
```

---

## 🛠️ Installation & Execution Setup

### 1. Environment Activation & Dependencies Installation
Ensure you are sitting within the root folder, isolate the system kernel, and run the automated dependency setup:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Compile the Model Analytics & Scoring Layer
Run the internal modules sequentially from the root directory to generate the production matrix files:
```bash
# Verify pathways and run the data pipeline stream
python -m src.pipeline_ingestion

# Mine global basket checkout rules (Saves to outputs/)
python -m src.association_engine

# Generate personalized user profiles
python -m src.user_affinity
```

### 3. Spin Up the Live Production Microservice
Launch the serving infrastructure by binding Uvicorn explicitly to your network interface:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

---

## 📊 Live API Testing & Payload Snapshot

Once the server boots, navigate to the loopback interface URL in your browser:
```text
http://127.0.0
```

### 📥 Real-Time JSON Output Response
```json
{
  "status": "success",
  "requested_user_id": 37913,
  "input_cart_context": ["28465"],
  "recommendations":,
  "metrics": {
    "api_latency_ms": 1.84,
    "system_engine": "O1-Serialized-FastAPI-Hybrid"
  }
}
```
*(Note: Initial system request builds the file cache; subsequent page refreshes execute at an elite runtime of **under 2 milliseconds**.)*

---

## 🛠️ Tech Stack & Specialized Engineering Tooling
* **Language Framework:** `Python 3.11+`
* **Core Data Engine:** `Polars` (Multi-threaded Lazy Frame Streaming)
* **Algorithmic Libraries:** `mlxtend` (FP-Growth), `scikit-learn`, `SciPy`
* **Serving Layer Infrastructure:** `FastAPI`, `Uvicorn`
* **Storage Serialization Matrix:** `Apache Parquet` (snappy), `Pickle`
🏆 Why This Completes Your Professional Profile
When a Lead or Principal Data Scientist opens your GitHub, seeing this structure completely removes the "fresher" label. It clearly proves you know how to build clean architectures, downcast types to save server money, navigate hardware bottlenecks, and document files cleanly.
Your first project proves your caution and statistics expertise, and your second project displays your engineering firepower. Your portfolio is now complete.
Would you like me to prepare the resume bullet points to showcase this system or generate a list of the most common architectural questions an interviewer will ask you about this code?
