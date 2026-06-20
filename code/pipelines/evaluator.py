import json
import datetime
from agents.agent_1_2 import Agent1_ClaimUnderstanding, Agent2_ImageQuality
from agents.agent_3_4 import Agent3_ImageAuthenticity, Agent4_DamageDetection
from agents.agent_5_6 import Agent5_EvidenceCoverage, Agent6_ContradictionDetection
from agents.agent_7_8_9 import Agent7_UserHistoryRisk, Agent8_9_DebateAndJudge

class MCISPipieline:
    def __init__(self):
        self.agent1 = Agent1_ClaimUnderstanding()
        self.agent2 = Agent2_ImageQuality()
        self.agent3 = Agent3_ImageAuthenticity()
        self.agent4 = Agent4_DamageDetection()
        self.agent5 = Agent5_EvidenceCoverage()
        self.agent6 = Agent6_ContradictionDetection()
        self.agent7 = Agent7_UserHistoryRisk()
        self.agent8_9 = Agent8_9_DebateAndJudge()

    def evaluate_claim(self, user_id, claim_id, text, image_paths):
        logs = []
        logs.append(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
        logs.append(f"Claim ID: {claim_id}")
        logs.append(f"User ID: {user_id}")
        logs.append(f"Claim Text: {text}")
        logs.append(f"Images: {image_paths}")

        replay = {
            "claim_id": claim_id,
            "user_id": user_id,
            "claim_text": text,
            "images": image_paths,
            "nodes": []
        }

        # Agent 1: Understanding
        a1_out = self.agent1.run(text)
        logs.append(f"[Agent 1] Extraction: {json.dumps(a1_out)}")
        replay["nodes"].append({
            "id": "agent1", "name": "Claim Understanding",
            "inputs": {"text": text}, "outputs": a1_out, "status": "Success"
        })

        # Agent 2: Quality
        a2_out = self.agent2.run(image_paths)
        logs.append(f"[Agent 2] Quality: {json.dumps(a2_out)}")
        replay["nodes"].append({
            "id": "agent2", "name": "Image Quality",
            "inputs": {"images": image_paths}, "outputs": a2_out, 
            "status": "Success" if a2_out["quality_score"] > 50 else "Warning"
        })

        # Agent 3: Authenticity
        a3_out = self.agent3.run(image_paths)
        logs.append(f"[Agent 3] Authenticity: {json.dumps(a3_out)}")
        replay["nodes"].append({
            "id": "agent3", "name": "Authenticity Analysis",
            "inputs": {"images": image_paths}, "outputs": a3_out, 
            "status": "Success" if a3_out["authenticity_score"] > 50 else "Warning"
        })

        # Agent 4: Damage Detection
        a4_out = self.agent4.run(image_paths, a1_out.get("object_type", "unknown"), a1_out.get("object_part", "unknown"))
        logs.append(f"[Agent 4] Damage Detection: {json.dumps(a4_out)}")
        replay["nodes"].append({
            "id": "agent4", "name": "Damage Detection",
            "inputs": {"images": image_paths, "object_type": a1_out.get("object_type", "unknown")}, 
            "outputs": a4_out, "status": "Success"
        })

        # Agent 5: Coverage
        a5_out = self.agent5.run(image_paths, a1_out.get("object_part", "unknown"))
        logs.append(f"[Agent 5] Coverage: {json.dumps(a5_out)}")
        replay["nodes"].append({
            "id": "agent5", "name": "Evidence Coverage",
            "inputs": {"images": image_paths, "object_part": a1_out.get("object_part", "unknown")}, 
            "outputs": a5_out, "status": "Success" if a5_out["coverage_score"] >= 50 else "Failure"
        })

        # Agent 6: Contradiction
        a6_out = self.agent6.run(a1_out.get("claimed_damage", "unknown"), a4_out.get("damage_type", "none"), a5_out["coverage_score"])
        logs.append(f"[Agent 6] Contradiction: {json.dumps(a6_out)}")
        replay["nodes"].append({
            "id": "agent6", "name": "Contradiction Detection",
            "inputs": {"claimed": a1_out.get("claimed_damage", "unknown"), "detected": a4_out.get("damage_type", "none")}, 
            "outputs": a6_out, "status": "Warning" if a6_out["contradicted"] else "Success"
        })

        # Agent 7: User History Risk
        a7_out = self.agent7.run(user_id)
        logs.append(f"[Agent 7] History Risk: {json.dumps(a7_out)}")
        replay["nodes"].append({
            "id": "agent7", "name": "Risk Analysis",
            "inputs": {"user_id": user_id}, "outputs": a7_out, "status": "Success"
        })

        # Calculate combined Fraud Score (Unique Feature 3)
        fraud_score = min(
            (100 - a2_out["quality_score"]) * 0.2 +
            (100 - a3_out["authenticity_score"]) * 0.4 +
            (30 if a6_out["contradicted"] else 0) +
            (a7_out["history_risk_score"] * 0.4),
            100
        )
        logs.append(f"[Fraud Intelligence] Score: {round(fraud_score, 2)}")
        replay["fraud_score"] = round(fraud_score, 2)

        # Agents 8 & 9: Debate & Judge
        a89_out = self.agent8_9.run(text, a5_out, a6_out, a7_out)
        logs.append(f"[Agent 8 & 9] Debate & Final Decision: {json.dumps(a89_out)}")
        replay["nodes"].append({
            "id": "agent89", "name": "Final Judge",
            "inputs": {"coverage": a5_out, "contradiction": a6_out, "risk": a7_out}, 
            "outputs": a89_out, "status": "Success"
        })

        # Format CSV Result
        evidence_met = a5_out["coverage_score"] >= 50
        risk_flags = a2_out["quality_flags"] + a3_out["authenticity_flags"]
        
        result = {
            "user_id": user_id,
            "image_paths": "|".join(image_paths),
            "user_claim": text,
            "claim_object": a1_out.get("object_type", "unknown"),
            "evidence_standard_met": str(evidence_met).lower(),
            "evidence_standard_met_reason": "Sufficient coverage" if evidence_met else a5_out.get("required_next_image", "Not visible"),
            "risk_flags": json.dumps(risk_flags),
            "issue_type": a1_out.get("claimed_damage", "unknown"),
            "object_part": a1_out.get("object_part", "unknown"),
            "claim_status": a89_out.get("claim_status", "contradicted"),
            "claim_status_justification": a89_out.get("claim_status_justification", ""),
            "supporting_image_ids": image_paths[0] if image_paths and evidence_met else "",
            "valid_image": str(a2_out["quality_score"] > 20).lower(),
            "severity": a4_out.get("severity", "low")
        }

        return result, "\n".join(logs), replay
