# System Architecture

## Multi-Modal Claim Intelligence System (MCIS)

The system orchestrates 9 specialized AI Agents to rigorously evaluate insurance claims in a deterministic, reliable pipeline.

### Agents
1. **Claim Understanding Agent**: Extracts object, damage, and part from text using Groq LLM JSON output.
2. **Image Quality Agent**: Detects blur, darkness, and resolution anomalies (0-100 score).
3. **Image Authenticity Agent**: Detects tampering, duplicates, and AI artifacts via perceptual hashing.
4. **Damage Detection Agent**: Qwen2.5-VL / Florence-2 visual reasoning for precise damage and severity.
5. **Evidence Coverage Engine**: Calculates coverage score; outputs Missing Evidence Recommendation if < 50.
6. **Claim Contradiction Engine**: Deterministically compares claimed damage against visual evidence.
7. **User History Risk Engine**: Temporal analysis of user claim frequency (Fraud context).
8. **Multi-Agent Debate**: Support, Challenger, and Reviewer traces evaluating the case.
9. **Final Judge**: Synthesizes all scores; history *never* overrides visual contradiction. Allowed outputs: `supported`, `contradicted`, `insufficient_evidence`.

### Unique Features
- **Evidence Coverage Score**: 0-100 metric for visibility.
- **Missing Evidence Recommendation**: Dynamic prompt for user follow-up.
- **Fraud Intelligence Score**: Agnostic risk score.
- **Visual Damage Localization**: Bounding regions for explainability.
- **Investigator Report**: Comprehensive audit log generation.
