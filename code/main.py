import os
from dotenv import load_dotenv
load_dotenv()
import pandas as pd
from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from pipelines.evaluator import MCISPipieline

app = FastAPI(title="MCIS Dashboard API")

# Mount dashboard static files
dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard")
if os.path.exists(dashboard_path):
    app.mount("/dashboard", StaticFiles(directory=dashboard_path), name="dashboard")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(dashboard_path, "index.html"))

@app.get("/api/stats")
def get_stats():
    # Read from output.csv to simulate Supabase aggregations
    output_path = os.path.join(os.path.dirname(__file__), "..", "outputs", "output.csv")
    if not os.path.exists(output_path):
        # Fallback to local
        output_path = "outputs/output.csv"
        
    if not os.path.exists(output_path):
        return {
            "most_claimed_damage": "No Data",
            "most_risky_users": 0,
            "most_common_contradictions": 0,
            "evidence_quality_avg": 0,
            "recent_claims": []
        }

    df = pd.read_csv(output_path)
    
    # Calculate stats
    try:
        most_damage = df['issue_type'].mode()[0]
    except:
        most_damage = "Unknown"
        
    # Risky users (flags containing history_risk or fraud_score > 50 if we had it, fallback to counting risk flags)
    risky_users = sum(df['risk_flags'].apply(lambda x: len(eval(x)) > 0 if isinstance(x, str) else False))
    
    contradictions = sum(df['claim_status'] == 'contradicted')
    
    # For evidence quality, we mock an average since it's not directly in csv (we have valid_image flag)
    valid_count = sum(df['valid_image'] == True)
    avg_quality = round((valid_count / len(df)) * 100) if len(df) > 0 else 0
    
    recent_claims = []
    for idx, row in df.head(10).iterrows():
        recent_claims.append({
            "claim_id": f"c{idx}",
            "user_id": row.get("user_id", "unknown"),
            "text": row.get("user_claim", ""),
            "status": row.get("claim_status", ""),
            "severity": row.get("severity", "")
        })

    return {
        "most_claimed_damage": most_damage.title(),
        "most_risky_users": risky_users,
        "most_common_contradictions": contradictions,
        "evidence_quality_avg": avg_quality,
        "recent_claims": recent_claims
    }

@app.get("/api/graph")
def get_graph():
    output_path = os.path.join(os.path.dirname(__file__), "..", "outputs", "output.csv")
    if not os.path.exists(output_path):
        output_path = "outputs/output.csv"
        
    if not os.path.exists(output_path):
        return {"nodes": [], "links": []}

    df = pd.read_csv(output_path)
    nodes = []
    links = []
    
    # Track added nodes to avoid duplicates
    added_nodes = set()
    
    def add_node(n_id, group, label):
        if n_id not in added_nodes:
            nodes.append({"id": n_id, "group": group, "label": label})
            added_nodes.add(n_id)
            
    # Always add the core central node
    add_node("CoreSystem", 0, "Claim Engine")
    
    for idx, row in df.iterrows():
        c_id = f"Claim_{idx}"
        u_id = f"User_{row.get('user_id', 'unknown')}"
        d_type = f"Damage_{row.get('issue_type', 'unknown')}"
        
        # Add nodes
        add_node(c_id, 1, f"Claim {idx}")
        add_node(u_id, 2, u_id)
        add_node(d_type, 3, d_type)
        
        # Add edges
        links.append({"source": c_id, "target": u_id, "value": 1})
        links.append({"source": c_id, "target": d_type, "value": 1})
        links.append({"source": c_id, "target": "CoreSystem", "value": 1})
        
        # Risk Flags
        flags = row.get("risk_flags", "[]")
        if isinstance(flags, str) and flags != "[]" and flags != "none":
            # Just add a generic risk node for visual punch
            r_node = "HighRisk"
            add_node(r_node, 4, "High Risk")
            links.append({"source": u_id, "target": r_node, "value": 2})

    return {"nodes": nodes, "links": links}

@app.get("/api/replay/{claim_id}")
def get_replay(claim_id: str):
    import json
    # Use fallback output path logic
    output_path = os.path.join(os.path.dirname(__file__), "..", "outputs", "output.csv")
    if not os.path.exists(output_path):
        output_path = "outputs/output.csv"
        
    replay_dir = os.path.join(os.path.dirname(output_path), "replays")
    replay_file = os.path.join(replay_dir, f"replay_{claim_id}.json")
    
    if not os.path.exists(replay_file):
        return {"error": "Replay not found"}
        
    with open(replay_file, "r") as f:
        return json.load(f)

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        dataset_dir = os.path.join(os.path.dirname(__file__), "..", "dataset")
        if not os.path.exists(dataset_dir):
            dataset_dir = "dataset"
        os.makedirs(dataset_dir, exist_ok=True)
        dataset_path = os.path.join(dataset_dir, "uploaded_claims.csv")
        with open(dataset_path, "wb") as f:
            f.write(content)
            
        # Run pipeline synchronously
        run_pipeline(custom_dataset_path=os.path.abspath(dataset_path))
        return JSONResponse(status_code=200, content={"message": "Success"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

def run_pipeline(custom_dataset_path=None):
    # Attempt to load the real downloaded test claims if available
    downloaded_path = r"C:\Users\sreej\Downloads\claims\claims\claims.csv"
    
    dataset_path = custom_dataset_path or "../dataset/test.csv"
    output_path = "../outputs/output.csv"
    log_path = "../logs/log.txt"

    if not custom_dataset_path and os.path.exists(downloaded_path):
        dataset_path = downloaded_path
    elif not custom_dataset_path and not os.path.exists(dataset_path):
        dataset_path = "dataset/test.csv"
        output_path = "outputs/output.csv"
        log_path = "logs/log.txt"
        
    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}. Creating mock dataset...")
        os.makedirs(os.path.dirname(dataset_path), exist_ok=True)
        df_mock = pd.DataFrame([
            {"user_id": "u123", "claim_id": "c1", "image_paths": "img1.jpg", "user_claim": "My laptop screen cracked"},
            {"user_id": "u124", "claim_id": "c2", "image_paths": "img_back.jpg", "user_claim": "Rear bumper dent"},
            {"user_id": "u125", "claim_id": "c3", "image_paths": "img_normal.jpg", "user_claim": "My laptop screen cracked"},
            {"user_id": "u123", "claim_id": "c4", "image_paths": "tampered.jpg", "user_claim": "The car bumper is dented"}
        ])
        df_mock.to_csv(dataset_path, index=False)

    pipeline = MCISPipieline()
    df = pd.read_csv(dataset_path)
    
    results = []
    all_logs = []
    
    for idx, row in df.iterrows():
        user_id = str(row.get("user_id", f"u{idx}"))
        claim_id = str(row.get("claim_id", f"c{idx}"))
        text = str(row.get("user_claim", ""))
        images = str(row.get("image_paths", "")).split("|")
        
        result, log_str, replay_session = pipeline.evaluate_claim(user_id, claim_id, text, images)
        results.append(result)
        all_logs.append(log_str)
        all_logs.append("-" * 40)
        
        # Save replay session
        replay_dir = os.path.join(os.path.dirname(output_path), "replays")
        os.makedirs(replay_dir, exist_ok=True)
        with open(os.path.join(replay_dir, f"replay_{claim_id}.json"), "w") as f:
            import json
            json.dump(replay_session, f, indent=2)
            
    res_df = pd.DataFrame(results)
    
    expected_cols = [
        "user_id", "image_paths", "user_claim", "claim_object", 
        "evidence_standard_met", "evidence_standard_met_reason", 
        "risk_flags", "issue_type", "object_part", "claim_status", 
        "claim_status_justification", "supporting_image_ids", 
        "valid_image", "severity"
    ]
    res_df = res_df[expected_cols]
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    res_df.to_csv(output_path, index=False)
    
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w") as f:
        f.write("\n".join(all_logs))
        
    print(f"Processing complete. Output saved to {output_path}. Logs saved to {log_path}.")
    
    # Generate Evaluation Report
    try:
        import sys
        base_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.append(base_dir)
        from evaluation.framework import EvaluationFramework
        eval_fw = EvaluationFramework()
        report_path = os.path.join(base_dir, "..", "evaluation_report.md")
        eval_fw.evaluate(output_path, os.path.abspath(report_path))
    except Exception as e:
        print(f"Evaluation report generation failed: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--serve":
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    else:
        run_pipeline()
