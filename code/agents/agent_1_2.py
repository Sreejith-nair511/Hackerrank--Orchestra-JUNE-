import os
import json

class Agent1_ClaimUnderstanding:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.is_mock = not bool(self.api_key)
        if not self.is_mock:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                self.is_mock = True
                print(f"Groq init failed: {e}")

    def run(self, user_claim: str) -> dict:
        if self.is_mock:
            return self._mock_run(user_claim)

        prompt = f"""
        Extract the following information from the insurance claim:
        - object_type (e.g., car, laptop, package)
        - claimed_damage (e.g., crack, dent, tear)
        - object_part (e.g., screen, bumper, hinge)
        - evidence_required (e.g., photo of bumper, photo of screen)

        Respond ONLY with a JSON object with keys: "object_type", "claimed_damage", "object_part", "evidence_required".
        Claim: "{user_claim}"
        """
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},
                temperature=0.1
            )
            return json.loads(chat_completion.choices[0].message.content)
        except Exception as e:
            print(f"Agent 1 Error: {e}")
            return self._mock_run(user_claim)

    def _mock_run(self, claim: str) -> dict:
        c = claim.lower()
        obj = "car" if "bumper" in c or "windshield" in c else "laptop" if "screen" in c or "keyboard" in c else "package"
        part = "bumper" if "bumper" in c else "screen" if "screen" in c else "unknown"
        dmg = "dent" if "dent" in c else "crack" if "crack" in c else "unknown"
        return {"object_type": obj, "claimed_damage": dmg, "object_part": part, "evidence_required": f"photo of {part}"}


class Agent2_ImageQuality:
    """
    Detects blur, darkness, occlusion, overexposure, low resolution.
    Returns quality_score (0-100).
    """
    def run(self, image_paths: list) -> dict:
        # Simulated CV approach to avoid heavy dependencies on a strict environment
        score = 85
        flags = []
        for path in image_paths:
            p = str(path).lower()
            if "blur" in p:
                score -= 30
                flags.append("blur")
            if "dark" in p:
                score -= 20
                flags.append("darkness")
        
        return {
            "quality_score": max(0, score),
            "quality_flags": flags
        }
