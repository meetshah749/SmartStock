"""
Investor Risk Profile and Risk Alignment Evaluation Service.
Calculates server-side investor risk categories (CONSERVATIVE, BALANCED, AGGRESSIVE)
based on empirical assessment of time horizon, risk tolerance, drawdown capacity, and market knowledge.
Includes strict regulatory disclaimer that this is risk preference alignment, not guaranteed financial advice.
"""

from typing import Dict, Any, Tuple
from app.schemas.auth import OnboardingCreate


def calculate_investor_risk_profile(answers: OnboardingCreate) -> Tuple[str, int, Dict[str, Any]]:
    """
    Calculate an objective risk category from onboarding survey answers.
    Returns: (risk_category, risk_score, breakdown_details)
    Categories: CONSERVATIVE, BALANCED, AGGRESSIVE
    """
    score = 0
    breakdown = {}

    # 1. Experience Level (1 to 5)
    exp = (answers.experience_level or "beginner").lower()
    if "advanced" in exp:
        exp_pts = 5
    elif "intermediate" in exp:
        exp_pts = 3
    else:
        exp_pts = 1
    score += exp_pts
    breakdown["experience_points"] = exp_pts

    # 2. Financial Knowledge (1 to 5)
    know = (answers.knowledge_level or "intermediate").lower()
    if "advanced" in know or "expert" in know:
        know_pts = 5
    elif "intermediate" in know:
        know_pts = 3
    else:
        know_pts = 1
    score += know_pts
    breakdown["knowledge_points"] = know_pts

    # 3. Stated Risk Tolerance (1 to 5)
    risk_tol = (answers.risk_tolerance or "medium").lower()
    if "high" in risk_tol or "aggressive" in risk_tol:
        risk_pts = 5
    elif "medium" in risk_tol or "moderate" in risk_tol or "balanced" in risk_tol:
        risk_pts = 3
    else:
        risk_pts = 1
    score += risk_pts
    breakdown["stated_risk_tolerance_points"] = risk_pts

    # 4. Investment Horizon (1 to 5)
    horizon = (answers.investment_horizon or "3-5 years").lower()
    if "5+" in horizon or "long" in horizon or "10" in horizon:
        horizon_pts = 5
    elif "3-5" in horizon or "medium" in horizon:
        horizon_pts = 4
    elif "1-3" in horizon:
        horizon_pts = 3
    else:
        horizon_pts = 2
    score += horizon_pts
    breakdown["horizon_points"] = horizon_pts

    # 5. Drawdown Tolerance (1 to 5)
    dd = (answers.max_drawdown_preference or "10% - 20%").lower()
    if ">35" in dd or "high" in dd or "35%" in dd:
        dd_pts = 5
    elif "20" in dd or "30" in dd:
        dd_pts = 4
    elif "10" in dd:
        dd_pts = 3
    else:
        dd_pts = 1
    score += dd_pts
    breakdown["drawdown_tolerance_points"] = dd_pts

    # 6. Investment Style (1 to 5)
    style = (answers.investment_style or "growth").lower()
    if "momentum" in style or "speculation" in style:
        style_pts = 5
    elif "growth" in style:
        style_pts = 4
    elif "value" in style:
        style_pts = 3
    else:
        style_pts = 2
    score += style_pts
    breakdown["style_points"] = style_pts

    # Total score ranges: 7 to 30
    if score <= 12:
        category = "CONSERVATIVE"
        description = (
            "Focus on capital preservation, low volatility stocks, and stable dividends. "
            "Lower tolerance for portfolio drawdowns."
        )
    elif score <= 22:
        category = "BALANCED"
        description = (
            "Seeks balanced capital appreciation with calculated risk exposure across diverse sectors. "
            "Moderate tolerance for intermediate market fluctuations."
        )
    else:
        category = "AGGRESSIVE"
        description = (
            "Aims for maximum capital growth potential, actively accepting higher price volatility and "
            "wider cyclical drawdowns."
        )

    breakdown["total_score"] = score
    breakdown["max_possible_score"] = 30
    breakdown["profile_description"] = description
    breakdown["disclaimer"] = (
        "Risk Alignment is a probabilistic assessment for user preference matching; "
        "not guaranteed financial advice or investment solicitation."
    )

    return category, score, breakdown
