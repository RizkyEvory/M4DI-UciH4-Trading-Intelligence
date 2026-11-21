"""
M4DI~UciH4 Trading Intelligence System
News Impact Scorer
Evaluates market impact severity based on Category, Sentiment extremity, Recency, and Volatility keywords.
"""
from datetime import datetime
from typing import Tuple, Dict, Any, Optional

from config.constants import (
    IMPACT_LOW,
    IMPACT_MEDIUM,
    IMPACT_HIGH,
    IMPACT_CRITICAL,
    NEWS_CAT_INTEREST_RATES,
    NEWS_CAT_INFLATION,
    NEWS_CAT_GEOPOLITICAL,
    NEWS_CAT_EARNINGS,
    NEWS_CAT_ECONOMIC,
    NEWS_CAT_REGULATION,
    NEWS_CAT_MA,
    NEWS_CAT_ANALYST_RATINGS,
    NEWS_CAT_PRODUCT_LAUNCHES,
    NEWS_CAT_COMPANY_ANNOUNCEMENTS,
    NEWS_CAT_MARKET_SENTIMENT
)

# Base Category Weight (0 - 100)
CATEGORY_BASE_IMPACT: Dict[str, float] = {
    NEWS_CAT_INTEREST_RATES: 85.0,     # Central Bank decisions dictate macro trend
    NEWS_CAT_INFLATION: 80.0,          # CPI/PPI shifts yields & currency
    NEWS_CAT_GEOPOLITICAL: 80.0,       # War, sanctions, trade barriers
    NEWS_CAT_EARNINGS: 70.0,           # Massive single-stock and sector gaps
    NEWS_CAT_ECONOMIC: 70.0,           # NFP, GDP, Retail Sales
    NEWS_CAT_REGULATION: 65.0,         # SEC, Antitrust, Banning
    NEWS_CAT_MA: 60.0,                 # M&A creates major premium revaluations
    NEWS_CAT_ANALYST_RATINGS: 45.0,    # Wall Street upgrades/downgrades
    NEWS_CAT_PRODUCT_LAUNCHES: 40.0,   # Product announcements
    NEWS_CAT_COMPANY_ANNOUNCEMENTS: 35.0,
    NEWS_CAT_MARKET_SENTIMENT: 35.0
}

# High Volatility Trigger Keywords (adds up to 20 points)
VOLATILITY_KEYWORDS = {
    "breaking": 15, "urgent": 15, "emergency": 20, "alert": 10,
    "crisis": 15, "war": 20, "rate hike": 15, "rate cut": 15,
    "default": 20, "bankruptcy": 20, "plunge": 10, "surge": 10,
    "investigation": 10, "banned": 15, "sanction": 15, "tariff": 15
}

# Key Macro / Market Movers
MARKET_MOVERS = {
    "fed", "fomc", "powell", "ecb", "cpi", "nfp", "gdp",
    "treasury", "yields", "dollar", "gold", "oil", "opec",
    "apple", "nvidia", "microsoft", "tesla", "amazon", "alphabet", "meta"
}


class NewsImpactScorer:
    """Calculates quantitative News Impact score (0-100) and classification (LOW, MEDIUM, HIGH, CRITICAL)"""

    @classmethod
    def calculate_impact(
        cls,
        category: str,
        sentiment_score: float,
        title: str,
        description: str = "",
        published_at: Optional[str] = None
    ) -> Tuple[str, float, Dict[str, Any]]:
        """
        Calculates composite impact score and assigns tier.
        Returns:
            (impact_level, impact_score, details_breakdown)
        """
        combined = f"{title} {description}".lower()

        # 1. Base Category Impact
        base_impact = CATEGORY_BASE_IMPACT.get(category, 40.0)

        # 2. Sentiment Extremity Factor (Extremely positive or negative news moves markets much harder)
        abs_sentiment = abs(sentiment_score)
        sentiment_booster = round(abs_sentiment * 18.0, 1)  # 0 to 18 pts

        # 3. Volatility Keywords
        vol_score = 0
        detected_vol_kw = []
        for kw, pts in VOLATILITY_KEYWORDS.items():
            if kw in combined:
                vol_score += pts
                detected_vol_kw.append(kw)
        vol_booster = min(20.0, float(vol_score))

        # 4. Market / Mega-Cap Mover Bonus
        mover_bonus = 0.0
        detected_movers = []
        for mover in MARKET_MOVERS:
            if mover in combined:
                mover_bonus += 5.0
                detected_movers.append(mover)
        mover_bonus = min(15.0, mover_bonus)

        # 5. Recency Time Decay Factor
        recency_factor = 1.0
        hours_old = 0.0
        if published_at:
            try:
                # Handle varying timestamp formats
                ts_clean = published_at.replace("T", " ").replace("Z", "").split(".")[0]
                dt = datetime.strptime(ts_clean[:19], "%Y-%m-%d %H:%M:%S")
                now = datetime.now()
                delta_sec = max(0, (now - dt).total_seconds())
                hours_old = delta_sec / 3600.0

                if hours_old <= 2.0:
                    recency_factor = 1.00
                elif hours_old <= 6.0:
                    recency_factor = 0.90
                elif hours_old <= 24.0:
                    recency_factor = 0.75
                elif hours_old <= 48.0:
                    recency_factor = 0.55
                else:
                    recency_factor = 0.35
            except Exception:
                recency_factor = 0.85

        # Raw total
        raw_score = (base_impact + sentiment_booster + vol_booster + mover_bonus) * recency_factor
        final_score = max(5.0, min(100.0, round(raw_score, 1)))

        # Classification Tiers
        if final_score >= 75.0:
            impact_level = IMPACT_CRITICAL
        elif final_score >= 55.0:
            impact_level = IMPACT_HIGH
        elif final_score >= 35.0:
            impact_level = IMPACT_MEDIUM
        else:
            impact_level = IMPACT_LOW

        breakdown = {
            "base_impact": base_impact,
            "sentiment_booster": sentiment_booster,
            "volatility_booster": vol_booster,
            "mover_bonus": mover_bonus,
            "recency_factor": recency_factor,
            "hours_old": round(hours_old, 1),
            "volatility_keywords": detected_vol_kw,
            "market_movers": detected_movers
        }

        return impact_level, final_score, breakdown
