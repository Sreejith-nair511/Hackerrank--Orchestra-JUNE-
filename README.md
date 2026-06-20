# Multi-Modal Claim Intelligence System (MCIS)

The **Multi-Modal Claim Intelligence System (MCIS)** is an advanced, multi-agent AI framework designed to orchestrate automated insurance claim evaluations. It uses a deterministic, transparent pipeline involving large language models (LLMs), visual reasoning (VLMs), and deterministic logic engines to rigorously evaluate the authenticity, damage severity, and overall legitimacy of claims based on multi-modal evidence.

## System Architecture

MCIS orchestrates 9 specialized AI Agents to evaluate claims and ensure decisions are traceable and accurate:

1. **Claim Understanding Agent**: Uses Groq LLM JSON output to extract object type, claimed damage, and affected part from free-text claims.
2. **Image Quality Agent**: Detects blur, darkness, and resolution anomalies, producing a quality score (0-100).
3. **Image Authenticity Agent**: Detects tampering, duplicates, and AI artifacts via perceptual hashing.
4. **Damage Detection Agent**: Simulated Qwen2.5-VL / Florence-2 visual reasoning to identify precise damage types and severity.
5. **Evidence Coverage Engine**: Calculates an evidence coverage score. If coverage is < 50, it dynamically formulates a Missing Evidence Recommendation.
6. **Claim Contradiction Engine**: Deterministically compares claimed damage against visual evidence extracted by the VLMs to detect discrepancies.
7. **User History Risk Engine**: Temporal analysis of user claim frequency and history to compute an agnostic risk context score.
8. **Multi-Agent Debate**: Orchestrates Support, Challenger, and Reviewer personas to thoroughly evaluate complex cases.
9. **Final Judge**: Synthesizes all inputs and scores into a definitive verdict (`supported`, `contradicted`, `insufficient_evidence`). History and contextual risk never override definitive visual contradiction.

### Unique Features & Innovations
- **Evidence Coverage Score**: A 0-100 metric tracking evidence visibility.
- **Dynamic Evidence Prompting**: Recommends exact missing visual angles to users automatically.
- **Fraud Intelligence Score**: Agnostic risk estimation.
- **Visual Damage Localization**: Bounding region logic for high explainability.
- **Interactive 3D Dashboard**: Real-time investigation tracking via a web dashboard, featuring knowledge graphs and 3D mockups.
- **Comprehensive Audit Logs**: Generates complete investigator reports for human-in-the-loop review.

---

## Setup Instructions

### Prerequisites
- Python 3.9+
- A virtual environment (recommended)

### 1. Installation
First, clone the repository or extract the ZIP file, navigate to the `code/` directory, and install dependencies:

```bash
# Create and activate a virtual environment (optional but recommended)
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Unix/MacOS:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file in the root of the `code` directory (if not already present). You can configure your external APIs here:
```env
GROQ_API_KEY=your_groq_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```
*(Note: The system contains built-in mock fallback mechanisms allowing it to run securely in disconnected environments if keys are not provided).*

---

## Running the Pipeline

### Command Line Evaluation
To run the automated agentic evaluation pipeline on the provided `dataset/test.csv`, use:

```bash
python main.py
```
*Alternatively, you can use `./run.sh` if running on Unix systems.*

This process will read the dataset, evaluate all claims using the multi-agent system, and automatically generate:
- `outputs/output.csv`: The final system predictions following the strict target schema.
- `logs/log.txt`: A comprehensive reasoning audit trail and chat transcript.
- `evaluation_report.md`: A summary of evaluation metrics.

### Web Dashboard
To view the generated investigations through the interactive dashboard visualization:

```bash
python main.py --serve
```
This will start a FastAPI server. You can view the dashboard by opening `http://localhost:8000/` in your web browser. 

## Included Files in Submission
- `code.zip`: The packaged source code containing the multi-agent pipelines and frontend dashboard.
- `output.csv`: The evaluated agent predictions mapping user inputs to verdicts.
- `log.txt`: Chat transcripts illustrating the internal multi-agent debate and reasoning process.
