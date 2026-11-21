"""
M4DI~UciH4 Trading Intelligence System
News Classification Engine (11 Institutional Categories)
Classifies financial headlines and descriptions with keyword pattern matching and scoring.
"""
import re
from typing import Dict, List, Tuple

from config.constants import (
    NEWS_CAT_EARNINGS,
    NEWS_CAT_ECONOMIC,
    NEWS_CAT_INTEREST_RATES,
    NEWS_CAT_INFLATION,
    NEWS_CAT_COMPANY_ANNOUNCEMENTS,
    NEWS_CAT_MA,
    NEWS_CAT_REGULATION,
    NEWS_CAT_GEOPOLITICAL,
    NEWS_CAT_ANALYST_RATINGS,
    NEWS_CAT_PRODUCT_LAUNCHES,
    NEWS_CAT_MARKET_SENTIMENT,
    NEWS_CATEGORIES
)

# Comprehensive domain-specific keyword dictionaries with importance weighting (1-3)
CATEGORY_PATTERNS: Dict[str, Dict[str, int]] = {
    NEWS_CAT_EARNINGS: {
        "earnings": 3, "quarterly result": 3, "revenue beat": 3, "revenue miss": 3,
        "eps": 2, "profit jump": 2, "profit plunge": 2, "profit drop": 2,
        "financial results": 2, "net income": 2, "ebitda": 2, "guidance": 2,
        "earnings per share": 3, "q1": 1, "q2": 1, "q3": 1, "q4": 1,
        "quarterly earnings": 3, "beat expectations": 2, "missed expectations": 2,
        "fiscal quarter": 2, "revenue rose": 2, "revenue fell": 2, "profit surge": 2
    },
    NEWS_CAT_INTEREST_RATES: {
        "interest rate": 3, "rate hike": 3, "rate cut": 3, "federal reserve": 3,
        "fed": 2, "fomc": 3, "powell": 2, "central bank": 3, "ecb": 2, "lagarde": 2,
        "bank of england": 2, "boe": 2, "basis points": 3, "monetary policy": 3,
        "quantitative tightening": 3, "quantitative easing": 3, "repo rate": 2,
        "rate decision": 3, "terminal rate": 2, "interest rates": 3, "fed cut": 3, "fed hike": 3
    },
    NEWS_CAT_INFLATION: {
        "inflation": 3, "cpi": 3, "consumer price index": 3, "ppi": 3,
        "producer price index": 3, "core inflation": 3, "pce": 3,
        "price pressures": 2, "cost of living": 2, "deflation": 2, "stagflation": 3,
        "hyperinflation": 3, "sticky inflation": 2, "headline inflation": 3
    },
    NEWS_CAT_ECONOMIC: {
        "gdp": 3, "gross domestic product": 3, "non-farm payroll": 3, "nfp": 3,
        "employment": 2, "unemployment rate": 3, "jobless claims": 3, "jobs report": 3,
        "manufacturing pmi": 3, "services pmi": 3, "retail sales": 3,
        "consumer confidence": 2, "trade deficit": 2, "factory orders": 2,
        "economic growth": 2, "recession": 2, "economic expansion": 2, "labor market": 2
    },
    NEWS_CAT_GEOPOLITICAL: {
        "war": 3, "military": 2, "conflict": 2, "geopolitical": 3, "sanctions": 3,
        "embargo": 3, "russia": 2, "ukraine": 2, "middle east": 2, "gaza": 2,
        "israel": 2, "iran": 2, "china tension": 3, "taiwan": 2, "tariffs": 3,
        "trade war": 3, "missile": 2, "security treaty": 2, "geopolitical risk": 3
    },
    NEWS_CAT_REGULATION: {
        "regulation": 3, "regulatory": 2, "sec": 3, "doj": 2, "investigation": 3,
        "probe": 3, "antitrust": 3, "lawsuit": 2, "court ruling": 2, "compliance": 2,
        "fined": 2, "penalty": 2, "subpoena": 3, "monopoly": 2, "illegal": 2,
        "sec charges": 3, "ftc": 2, "indictment": 3, "sanctioned": 2
    },
    NEWS_CAT_MA: {
        "acquisition": 3, "acquire": 3, "acquires": 3, "acquired": 3, "merger": 3,
        "merging": 3, "buyout": 3, "takeover": 3, "deal valued": 3, "purchase agreement": 2,
        "joint venture": 2, "spin-off": 2, "divestiture": 2, "merger agreement": 3
    },
    NEWS_CAT_ANALYST_RATINGS: {
        "upgrade": 3, "upgrades": 3, "upgraded": 3, "downgrade": 3, "downgrades": 3,
        "downgraded": 3, "analyst": 2, "price target": 3, "overweight": 2,
        "underweight": 2, "outperform": 2, "underperform": 2, "buy rating": 3,
        "sell rating": 3, "hold rating": 2, "target raised": 3, "target lowered": 3,
        "goldman sachs": 2, "morgan stanley": 2, "jp morgan": 2, "barclays": 2
    },
    NEWS_CAT_PRODUCT_LAUNCHES: {
        "launch": 2, "launches": 2, "launched": 2, "unveil": 3, "unveils": 3,
        "unveiled": 3, "debuts": 2, "introduces new": 2, "next-generation": 2,
        "new product": 3, "ai model": 2, "flagship": 2, "rollout": 2,
        "new features": 2, "chip release": 2, "software update": 2
    },
    NEWS_CAT_COMPANY_ANNOUNCEMENTS: {
        "announces": 2, "announced": 2, "press release": 2, "board of directors": 2,
        "ceo": 2, "cfo": 2, "appoints": 2, "resigns": 2, "stepped down": 2,
        "restructuring": 2, "layoffs": 2, "dividend increase": 3, "dividend cut": 3,
        "share buyback": 3, "share repurchase": 3, "annual shareholder": 2
    },
    NEWS_CAT_MARKET_SENTIMENT: {
        "bullish": 2, "bearish": 2, "rally": 2, "sell-off": 2, "market slump": 2,
        "investor sentiment": 3, "risk on": 2, "risk off": 2, "market volatility": 2,
        "wall street": 2, "s&p 500": 2, "nasdaq": 2, "dow jones": 2, "stocks jump": 2,
        "stocks tumble": 2, "market bounce": 2, "equities advance": 2
    }
}


class NewsClassifier:
    """Classifies news articles into standard institutional categories"""

    @staticmethod
    def classify(title: str, description: str = "", content: str = "") -> Tuple[str, float]:
        """
        Scan title, description, and content to identify the dominant category.
        Returns:
            (category_name, confidence_score)
        """
        combined_text = f"{title} {title} {description} {content}".lower()
        if not combined_text.strip():
            return NEWS_CAT_MARKET_SENTIMENT, 0.0

        scores: Dict[str, int] = {cat: 0 for cat in NEWS_CATEGORIES}

        for cat, kw_dict in CATEGORY_PATTERNS.items():
            for kw, weight in kw_dict.items():
                # Word boundary matching for clean match
                pattern = r'\b' + re.escape(kw) + r'\b'
                matches = len(re.findall(pattern, combined_text))
                if matches > 0:
                    scores[cat] += matches * weight

        # Sort by total score descending
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_cat, top_score = ranked[0]

        if top_score == 0:
            # Fallback to market sentiment or company announcement based on simple heuristics
            if any(term in combined_text for term in ["company", "corp", "inc", "ltd"]):
                return NEWS_CAT_COMPANY_ANNOUNCEMENTS, 0.3
            return NEWS_CAT_MARKET_SENTIMENT, 0.2

        total_score = sum(s for _, s in ranked)
        confidence = min(1.0, round(top_score / max(1, (top_score + 4)), 2))
        return top_cat, confidence
