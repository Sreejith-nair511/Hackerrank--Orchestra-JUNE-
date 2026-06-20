import os
import json

class Agent7_UserHistoryRisk:
    def __init__(self):
        self.history = {}

    def run(self, user_id: str) -> dict:
        if user_id not in self.history:
            self.history[user_id] = 0
        self.history[user_id] += 1
        
        score = min(self.history[user_id] * 10, 80)
        return {
            "history_risk_score": score
        }

class Agent8_9_DebateAndJudge:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.is_mock = not bool(self.api_key)
        if not self.is_mock:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
            except Exception:
                self.is_mock = True

    def run(self, claim_text: str, coverage: dict, contradiction: dict, risk: dict) -> dict:
        if self.is_mock:
            status = "supported"
            just = "Mock judge approved."
            if coverage["coverage_score"] < 50:
                status = "insufficient_evidence"
                just = coverage["required_next_image"]
            elif contradiction["contradicted"]:
                status = "contradicted"
                just = contradiction["contradiction_reason"]
            return {"claim_status": status, "claim_status_justification": just, "debate_trace": "Mock trace"}

        prompt = f"""
        You are the Final Judge for an insurance claim.
        Claim: "{claim_text}"
        Coverage Score: {coverage['coverage_score']}
        Contradicted: {contradiction['contradicted']} ({contradiction['contradiction_reason']})
        History Risk: {risk['history_risk_score']}

        Rules:
        - If Coverage < 50 -> insufficient_evidence
        - If Contradicted == True -> contradicted
        - Else -> supported
        - History Risk MUST NEVER override image evidence. It is just context.

        Debate:
        Agent A: User claims this, let's believe them.
        Agent B: We must check coverage and contradiction.
        Agent C: Follow the rules strictly.

        Respond ONLY with a JSON object with:
        - "claim_status": one of ["supported", "contradicted", "insufficient_evidence"]
        - "claim_status_justification": explicit reasoning
        - "debate_trace": brief summary of the multi-agent debate
        """
        try:
            chat = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},
                temperature=0.1
            )
            return json.loads(chat.choices[0].message.content)
        except Exception:
            return {
                "claim_status": "contradicted", 
                "claim_status_justification": "Fallback error", 
                "debate_trace": "Error during API call"
            }
