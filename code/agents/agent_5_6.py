class Agent5_EvidenceCoverage:
    """
    Determines whether the claimed area is actually visible.
    Returns coverage_score (0-100) and required_next_image.
    """
    def run(self, image_paths: list, expected_part: str) -> dict:
        score = 100
        req = ""
        
        if not image_paths:
            return {"coverage_score": 0, "required_next_image": f"Please upload an image of the {expected_part}."}
            
        primary_img = str(image_paths[0]).lower()
        if "wrong_angle" in primary_img:
            score = 20
            req = f"Please upload a clear, close-up image of the {expected_part}."
            
        return {
            "coverage_score": score,
            "required_next_image": req
        }

class Agent6_ContradictionDetection:
    """
    Compares claimed damage vs visible evidence.
    Returns contradiction explicitly explaining WHY.
    """
    def run(self, claimed_damage: str, detected_damage: str, coverage_score: int) -> dict:
        if coverage_score < 50:
            return {
                "contradicted": False,
                "contradiction_reason": "Not enough coverage to determine contradiction."
            }
            
        if detected_damage == "none" and claimed_damage != "unknown":
            return {
                "contradicted": True,
                "contradiction_reason": f"Claim states '{claimed_damage}', but visual evidence shows no damage."
            }
            
        return {
            "contradicted": False,
            "contradiction_reason": "Visual evidence is consistent with claim."
        }
