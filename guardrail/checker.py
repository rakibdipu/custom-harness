"""
Guardrail Checker - Quality + Policy gate before video is made
If script fails, harness regenerates. LLM output is NEVER trusted blindly.
"""
import re
import logging
from config import Config

logger = logging.getLogger(__name__)

# Banned keywords (Facebook/YouTube policy violations)
# Using specific phrases to avoid false positives on historical/educational content
BANNED_KEYWORDS = [
    "kill yourself", "how to kill", "murder tutorial", "suicide method",
    "rape", "porn", "nude", "sex video", "drug deal",
    "bomb making", "terrorist attack", "hack account", "scam people",
    "hate speech", "racist slur", "nazi propaganda",
]

# Engagement quality signals (at least 1 required in hook)
HOOK_POWER_WORDS = [
    "never", "always", "secret", "truth", "lies", "wrong", "mistake",
    "most people", "nobody tells", "shocked", "proven", "science",
    "warning", "stop", "instantly", "powerful", "dangerous", "real",
    "hidden", "exposed", "finally", "nobody", "everyone", "why",
    "bizarre", "exact", "actually", "brutal", "harsh",
]


class GuardrailChecker:
    def __init__(self):
        self.config = Config()

    def check(self, script: dict, content_type: str = "short_reel") -> dict:
        """
        Run all guardrail checks on a script.
        Returns: {"passed": bool, "score": float, "reason": str, "word_count": int}
        """
        issues = []
        score = 10.0
        word_count = 0  # initialised here so it's always defined in the return value

        # --- 1. Structure check ---
        base_keys = ["title", "hook", "voiceover", "image_prompts"]
        for key in base_keys:
            if key not in script or not script[key]:
                issues.append(f"Missing required field: {key}")
                score -= 3.0

        has_sections = bool(
            script.get("sections") or script.get("chapters") or
            script.get("story_acts") or script.get("scenes") or script.get("bits")
        )
        if not has_sections:
            issues.append("Missing content sections (or chapters/story_acts/scenes/bits)")
            score -= 3.0

        has_cta = bool(
            script.get("cta") or script.get("outro") or
            script.get("moral") or script.get("punchline")
        )
        if not has_cta:
            issues.append("Missing CTA / outro / moral / punchline")
            score -= 2.0

        if score < 4:
            return {
                "passed": False,
                "score": max(0.0, round(score, 1)),
                "reason": " | ".join(issues),
                "word_count": word_count,
            }

        # --- 2. Word count check (content-type aware) ---
        voiceover = script.get("voiceover", "")
        word_count = len(voiceover.split())
        
        if content_type in ["long_video", "storytelling_video"]:
            min_words, max_words = 300, 2500
        else:
            min_words = self.config.MIN_SCRIPT_WORDS
            max_words = self.config.MAX_SCRIPT_WORDS

        if word_count < min_words:
            issues.append(f"Too short: {word_count} words (min {min_words})")
            score -= 2.5
        elif word_count > max_words:
            issues.append(f"Too long: {word_count} words (max {max_words})")
            score -= 1.0

        # --- 3. Policy check (banned keywords) ---
        full_text = f"{script.get('title','')} {script.get('hook','')} {voiceover}".lower()
        for banned in BANNED_KEYWORDS:
            if banned in full_text:
                issues.append(f"Policy violation: banned phrase '{banned}'")
                score -= 4.0

        # --- 4. Hook quality check ---
        hook = script.get("hook", "").lower()
        hook_power_count = sum(1 for word in HOOK_POWER_WORDS if word in hook)
        if hook_power_count < 1:
            issues.append("Weak hook: missing power words")
            score -= 1.5
        elif hook_power_count >= 2:
            score = min(10.0, score + 0.5)  # Bonus for strong hook

        # --- 5. Title check ---
        title = script.get("title", "")
        if len(title) > 100:
            issues.append("Title too long (>100 chars)")
            score -= 0.5
        if len(title) < 15:
            issues.append("Title too short (<15 chars)")
            score -= 1.0

        # --- 6. CTA check ---
        cta = (script.get("cta") or script.get("outro") or script.get("moral") or script.get("punchline") or "").lower()
        cta_keywords = ["follow", "subscribe", "like", "share", "comment",
                        "tell", "drop", "tag", "save", "think", "try",
                        "lesson", "moral", "remember", "never", "watch", "next"]
        if not any(kw in cta for kw in cta_keywords):
            issues.append("CTA missing action or engagement words")
            score -= 1.0

        # --- 7. Sections check ---
        sections = (
            script.get("sections") or script.get("chapters") or
            script.get("story_acts") or script.get("scenes") or script.get("bits") or []
        )
        if len(sections) < 2:
            issues.append("Not enough sections (need at least 2)")
            score -= 2.0

        # --- 8. Image prompts check ---
        image_prompts = script.get("image_prompts", [])
        if len(image_prompts) < 3:
            issues.append("Need at least 3 image prompts")
            score -= 1.0

        # Final verdict
        score = max(0.0, round(score, 1))
        passed = score >= self.config.MIN_GUARDRAIL_SCORE and not any(
            "Policy violation" in issue for issue in issues
        )

        if issues:
            logger.warning(f"Guardrail issues: {issues}")

        return {
            "passed": passed,
            "score": score,
            "reason": " | ".join(issues) if issues else "All checks passed",
            "word_count": word_count,
        }
