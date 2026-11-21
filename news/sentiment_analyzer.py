"""
M4DI~UciH4 Trading Intelligence System
Deterministic Financial Sentiment Analyzer
High-precision local lexicon and rule-based engine built specifically for financial markets.
Zero cloud dependency, zero fabricated AI claims, fully transparent and auditable.
"""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

from config.constants import (
    SENTIMENT_POSITIVE,
    SENTIMENT_NEGATIVE,
    SENTIMENT_NEUTRAL
)

# Financial positive dictionary (Token: weight 1.0 to 3.0)
POSITIVE_FINANCIAL_LEXICON: Dict[str, float] = {
    # Earnings & Performance
    "beat": 2.0, "beats": 2.0, "beating": 2.0, "exceeded": 2.0, "exceeds": 2.0,
    "outperform": 2.2, "outperformed": 2.2, "outperforming": 2.2, "record": 1.5,
    "surge": 2.0, "surges": 2.0, "surged": 2.0, "surging": 2.0,
    "rally": 1.8, "rallies": 1.8, "rallied": 1.8, "rallying": 1.8,
    "gain": 1.2, "gains": 1.2, "gained": 1.2, "gaining": 1.2,
    "profit": 1.5, "profits": 1.5, "profitable": 1.5, "profitability": 1.8,
    "growth": 1.4, "growing": 1.4, "grew": 1.4,
    "soar": 2.0, "soars": 2.0, "soared": 2.0, "soaring": 2.0,
    "jump": 1.4, "jumps": 1.4, "jumped": 1.4, "jumping": 1.4,
    "bullish": 2.2, "bull": 1.5, "bulls": 1.5,
    "upgrade": 2.2, "upgrades": 2.2, "upgraded": 2.2, "upgrading": 2.2,
    "dividend": 1.2, "buyback": 1.8, "repurchase": 1.5,
    "optimism": 1.5, "optimistic": 1.5, "positive": 1.2,
    "expansion": 1.5, "expanding": 1.5, "expanded": 1.5,
    "recovery": 1.6, "rebound": 1.6, "rebounds": 1.6, "rebounded": 1.6,
    "breakout": 1.8, "highs": 1.3, "all-time high": 2.5, "ath": 2.5,
    "strength": 1.5, "strong": 1.4, "stronger": 1.5, "robust": 1.8,
    "tailwind": 1.5, "tailwinds": 1.5, "upside": 1.6,
    "acquire": 1.3, "partnership": 1.4, "approval": 1.8, "approved": 1.8,
    "innovation": 1.3, "breakthrough": 2.0, "opportunity": 1.2
}

# Financial negative dictionary (Token: weight 1.0 to 3.0)
NEGATIVE_FINANCIAL_LEXICON: Dict[str, float] = {
    # Losses & Declines
    "miss": 2.0, "misses": 2.0, "missed": 2.0, "missing": 2.0,
    "plunge": 2.2, "plunges": 2.2, "plunged": 2.2, "plunging": 2.2,
    "tumble": 2.0, "tumbles": 2.0, "tumbled": 2.0, "tumbling": 2.0,
    "slump": 2.0, "slumps": 2.0, "slumped": 2.0, "slumping": 2.0,
    "drop": 1.4, "drops": 1.4, "dropped": 1.4, "dropping": 1.4,
    "fall": 1.3, "falls": 1.3, "fell": 1.3, "falling": 1.3,
    "decline": 1.4, "declines": 1.4, "declined": 1.4, "declining": 1.4,
    "loss": 1.6, "losses": 1.8, "losing": 1.4, "lost": 1.4,
    "crash": 2.8, "crashes": 2.8, "crashed": 2.8, "crashing": 2.8,
    "collapse": 2.5, "collapses": 2.5, "collapsed": 2.5, "collapsing": 2.5,
    "bearish": 2.2, "bear": 1.5, "bears": 1.5,
    "downgrade": 2.2, "downgrades": 2.2, "downgraded": 2.2, "downgrading": 2.2,
    "debt": 1.4, "default": 2.8, "defaults": 2.8, "defaulted": 2.8, "bankrupt": 3.0,
    "bankruptcy": 3.0, "insolvency": 2.8, "insolvent": 2.8,
    "lawsuit": 1.8, "probe": 2.0, "investigation": 2.0, "fraud": 3.0,
    "fine": 1.5, "fined": 1.5, "penalty": 1.8, "penalties": 1.8,
    "sanction": 2.0, "sanctions": 2.0, "tariff": 1.8, "tariffs": 1.8,
    "inflation": 1.6, "layoffs": 2.2, "layoff": 2.2, "firing": 1.8, "cut jobs": 2.0,
    "warning": 1.8, "warns": 1.8, "warned": 1.8, "selloff": 2.0, "sell-off": 2.0,
    "weakness": 1.6, "weak": 1.4, "weaker": 1.5, "headwind": 1.6, "downside": 1.6,
    "crisis": 2.5, "panic": 2.5, "recession": 2.2, "stagnation": 1.8
}

# Negator words that invert the subsequent sentiment token
NEGATORS = {
    "not", "never", "failed", "fails", "fail", "neither", "no", "none",
    "unable", "cannot", "hardly", "scarcely", "without", "despite", "stop", "stopped"
}

# Intensifiers (Booster words multiplying subsequent token by 1.5)
INTENSIFIERS = {
    "significantly", "massively", "sharply", "dramatically", "heavily",
    "hugely", "extremely", "substantially", "strongly", "deeply", "severe", "severely"
}

# De-intensifiers (Dampener words multiplying subsequent token by 0.6)
DAMPENERS = {
    "slightly", "moderately", "somewhat", "marginally", "partially", "barely"
}


@dataclass
class SentimentResult:
    """Detailed sentiment scoring breakdown for complete transparency"""
    sentiment: str                        # POSITIVE, NEGATIVE, or NEUTRAL
    score: float                          # Continuous score from -1.0 to +1.0
    intensity: float                      # Magnitude from 0.0 to 1.0
    positive_score: float
    negative_score: float
    positive_tokens: List[str] = field(default_factory=list)
    negative_tokens: List[str] = field(default_factory=list)
    inverted_tokens: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)


class FinancialSentimentAnalyzer:
    """Local, auditable, high-precision financial sentiment scoring engine"""

    @classmethod
    def analyze(cls, text: str) -> SentimentResult:
        """
        Calculates sentiment with negation awareness and financial domain weighting.
        """
        if not text or not text.strip():
            return SentimentResult(
                sentiment=SENTIMENT_NEUTRAL,
                score=0.0,
                intensity=0.0,
                positive_score=0.0,
                negative_score=0.0,
                reasons=["Empty or whitespace text"]
            )

        # Normalize words while retaining hyphenated terms (e.g. sell-off, all-time)
        clean_text = text.lower()
        words = re.findall(r"\b[\w\-']+\b", clean_text)

        pos_score = 0.0
        neg_score = 0.0
        pos_tokens: List[str] = []
        neg_tokens: List[str] = []
        inv_tokens: List[str] = []
        reasons: List[str] = []

        i = 0
        n = len(words)

        while i < n:
            word = words[i]

            # Check 2-word idioms first
            bigram = f"{words[i]} {words[i+1]}" if i + 1 < n else ""
            if bigram in POSITIVE_FINANCIAL_LEXICON:
                w = POSITIVE_FINANCIAL_LEXICON[bigram]
                pos_score += w
                pos_tokens.append(bigram)
                i += 2
                continue
            elif bigram in NEGATIVE_FINANCIAL_LEXICON:
                w = NEGATIVE_FINANCIAL_LEXICON[bigram]
                neg_score += w
                neg_tokens.append(bigram)
                i += 2
                continue

            # Lookback for negator in the preceding 1 or 2 tokens
            is_inverted = False
            multiplier = 1.0

            if i > 0:
                prev_1 = words[i - 1]
                if prev_1 in NEGATORS:
                    is_inverted = True
                elif prev_1 in INTENSIFIERS:
                    multiplier = 1.5
                elif prev_1 in DAMPENERS:
                    multiplier = 0.6

            if i > 1 and not is_inverted:
                prev_2 = words[i - 2]
                if prev_2 in NEGATORS:
                    is_inverted = True

            # Match positive
            if word in POSITIVE_FINANCIAL_LEXICON:
                weight = POSITIVE_FINANCIAL_LEXICON[word] * multiplier
                if is_inverted:
                    neg_score += weight
                    inv_tokens.append(f"not {word}")
                else:
                    pos_score += weight
                    pos_tokens.append(word)

            # Match negative
            elif word in NEGATIVE_FINANCIAL_LEXICON:
                weight = NEGATIVE_FINANCIAL_LEXICON[word] * multiplier
                if is_inverted:
                    pos_score += weight
                    inv_tokens.append(f"not {word}")
                else:
                    neg_score += weight
                    neg_tokens.append(word)

            i += 1

        total_matches = len(pos_tokens) + len(neg_tokens) + len(inv_tokens)
        if total_matches == 0:
            return SentimentResult(
                sentiment=SENTIMENT_NEUTRAL,
                score=0.0,
                intensity=0.0,
                positive_score=0.0,
                negative_score=0.0,
                reasons=["No polarized financial terminology detected"]
            )

        # Normalize score into range -1.0 to +1.0
        net = pos_score - neg_score
        total = pos_score + neg_score
        raw_score = net / total if total > 0 else 0.0

        # Continuous score scaling
        continuous_score = max(-1.0, min(1.0, round(raw_score, 3)))
        intensity = round(min(1.0, total / 6.0), 3)

        # Thresholds: |score| >= 0.15 for polarized sentiment
        if continuous_score >= 0.15:
            sentiment = SENTIMENT_POSITIVE
            reasons.append(f"Dominant positive signals: {', '.join(pos_tokens[:5])}")
        elif continuous_score <= -0.15:
            sentiment = SENTIMENT_NEGATIVE
            reasons.append(f"Dominant negative signals: {', '.join(neg_tokens[:5])}")
        else:
            sentiment = SENTIMENT_NEUTRAL
            reasons.append("Balanced or neutral market commentary")

        if inv_tokens:
            reasons.append(f"Negation inverters applied: {', '.join(inv_tokens[:3])}")

        return SentimentResult(
            sentiment=sentiment,
            score=continuous_score,
            intensity=intensity,
            positive_score=round(pos_score, 2),
            negative_score=round(neg_score, 2),
            positive_tokens=pos_tokens,
            negative_tokens=neg_tokens,
            inverted_tokens=inv_tokens,
            reasons=reasons
        )
