"""
M4DI~UciH4 Trading Intelligence System
News Intelligence Unit & Integration Tests (Phase 4)
Verifies 11-category classification, local NLP sentiment scoring, negation handling,
impact scoring, deduplication, and symbol sentiment aggregation.
"""
import unittest
from unittest.mock import MagicMock
from datetime import datetime, timedelta

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
    SENTIMENT_POSITIVE,
    SENTIMENT_NEGATIVE,
    SENTIMENT_NEUTRAL,
    IMPACT_CRITICAL,
    IMPACT_HIGH,
    IMPACT_MEDIUM,
    IMPACT_LOW
)
from api.models import NormalizedNews
from news.categories import NewsClassifier
from news.sentiment_analyzer import FinancialSentimentAnalyzer
from news.impact_scorer import NewsImpactScorer
from news.deduplicator import NewsDeduplicator
from news.models import EnrichedNewsArticle
from news.news_engine import NewsEngine


class TestNewsClassification(unittest.TestCase):
    """Test classification across all 11 required institutional news categories"""

    def test_classify_earnings(self):
        title = "Apple Q4 Earnings Beat Wall Street Expectations with Record Revenue"
        cat, conf = NewsClassifier.classify(title)
        self.assertEqual(cat, NEWS_CAT_EARNINGS)
        self.assertGreater(conf, 0.4)

    def test_classify_interest_rates(self):
        title = "Federal Reserve Chair Powell Signals 50 Basis Points Rate Cut at Next FOMC"
        cat, conf = NewsClassifier.classify(title)
        self.assertEqual(cat, NEWS_CAT_INTEREST_RATES)
        self.assertGreater(conf, 0.4)

    def test_classify_inflation(self):
        title = "US CPI Inflation Climbs 3.4% YoY as Consumer Price Index Pressures Mount"
        cat, conf = NewsClassifier.classify(title)
        self.assertEqual(cat, NEWS_CAT_INFLATION)
        self.assertGreater(conf, 0.4)

    def test_classify_economic_data(self):
        title = "Non-Farm Payrolls Show 250k Jobs Added as Unemployment Rate Dips"
        cat, conf = NewsClassifier.classify(title)
        self.assertEqual(cat, NEWS_CAT_ECONOMIC)
        self.assertGreater(conf, 0.4)

    def test_classify_geopolitical(self):
        title = "Escalating Middle East Conflict and Trade War Tariffs Rattle Global Markets"
        cat, conf = NewsClassifier.classify(title)
        self.assertEqual(cat, NEWS_CAT_GEOPOLITICAL)
        self.assertGreater(conf, 0.4)

    def test_classify_regulation(self):
        title = "SEC Launches Antitrust Investigation into Major Tech Firm for Alleged Monopoly"
        cat, conf = NewsClassifier.classify(title)
        self.assertEqual(cat, NEWS_CAT_REGULATION)
        self.assertGreater(conf, 0.4)

    def test_classify_mergers_acquisitions(self):
        title = "Broadcom Completes $69 Billion Buyout and Merger Agreement of VMware"
        cat, conf = NewsClassifier.classify(title)
        self.assertEqual(cat, NEWS_CAT_MA)
        self.assertGreater(conf, 0.4)

    def test_classify_analyst_ratings(self):
        title = "Goldman Sachs Upgrades Nvidia to Buy Rating with $150 Price Target"
        cat, conf = NewsClassifier.classify(title)
        self.assertEqual(cat, NEWS_CAT_ANALYST_RATINGS)
        self.assertGreater(conf, 0.4)

    def test_classify_product_launches(self):
        title = "OpenAI Unveils Next-Generation Flagship AI Model with Enhanced Reasoning"
        cat, conf = NewsClassifier.classify(title)
        self.assertEqual(cat, NEWS_CAT_PRODUCT_LAUNCHES)
        self.assertGreater(conf, 0.4)

    def test_classify_company_announcements(self):
        title = "Tesla Board of Directors Announces $10 Billion Share Buyback Program"
        cat, conf = NewsClassifier.classify(title)
        self.assertEqual(cat, NEWS_CAT_COMPANY_ANNOUNCEMENTS)
        self.assertGreater(conf, 0.4)

    def test_classify_market_sentiment(self):
        title = "Wall Street Stocks Rally to All-Time Highs in Broad Bullish Momentum"
        cat, conf = NewsClassifier.classify(title)
        self.assertEqual(cat, NEWS_CAT_MARKET_SENTIMENT)
        self.assertGreater(conf, 0.3)


class TestFinancialSentimentAnalyzer(unittest.TestCase):
    """Test local deterministic financial sentiment quantification"""

    def test_positive_sentiment(self):
        text = "Company surges with record profits and massive revenue beat"
        res = FinancialSentimentAnalyzer.analyze(text)
        self.assertEqual(res.sentiment, SENTIMENT_POSITIVE)
        self.assertGreater(res.score, 0.3)
        self.assertIn("beat", res.positive_tokens)
        self.assertTrue(any("profit" in w for w in res.positive_tokens))

    def test_negative_sentiment(self):
        text = "Stock plunges following earnings miss, massive debt default and bankruptcy fears"
        res = FinancialSentimentAnalyzer.analyze(text)
        self.assertEqual(res.sentiment, SENTIMENT_NEGATIVE)
        self.assertLess(res.score, -0.3)
        self.assertIn("plunges", res.negative_tokens)
        self.assertIn("miss", res.negative_tokens)

    def test_neutral_sentiment(self):
        text = "Federal Reserve holds scheduled meeting to review quarterly baseline statistics"
        res = FinancialSentimentAnalyzer.analyze(text)
        self.assertEqual(res.sentiment, SENTIMENT_NEUTRAL)
        self.assertAlmostEqual(res.score, 0.0, delta=0.2)

    def test_negation_inversion(self):
        # "not beat" should invert beat from positive to negative
        text = "Company failed to beat earnings estimates despite market optimism"
        res = FinancialSentimentAnalyzer.analyze(text)
        # Should detect failed/not inversion
        self.assertTrue(len(res.inverted_tokens) > 0 or res.score <= 0.0)

    def test_intensifier_multiplier(self):
        text_normal = "Revenue beat expectations"
        text_boosted = "Revenue significantly beat expectations"
        res_normal = FinancialSentimentAnalyzer.analyze(text_normal)
        res_boosted = FinancialSentimentAnalyzer.analyze(text_boosted)
        self.assertGreaterEqual(res_boosted.positive_score, res_normal.positive_score)

    def test_empty_string(self):
        res = FinancialSentimentAnalyzer.analyze("")
        self.assertEqual(res.sentiment, SENTIMENT_NEUTRAL)
        self.assertEqual(res.score, 0.0)


class TestNewsImpactScorer(unittest.TestCase):
    """Test market impact severity calculation and recency decay"""

    def test_critical_impact_event(self):
        # Geopolitical war breaking news should score CRITICAL
        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level, score, breakdown = NewsImpactScorer.calculate_impact(
            category=NEWS_CAT_GEOPOLITICAL,
            sentiment_score=-0.85,
            title="BREAKING: Emergency Military Conflict and War Declared in Oil Transit Strait",
            published_at=now_ts
        )
        self.assertIn(level, [IMPACT_CRITICAL, IMPACT_HIGH])
        self.assertGreaterEqual(score, 70.0)

    def test_low_impact_announcement(self):
        # Routine announcement from 3 days ago should score LOW or MEDIUM
        old_ts = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
        level, score, breakdown = NewsImpactScorer.calculate_impact(
            category=NEWS_CAT_COMPANY_ANNOUNCEMENTS,
            sentiment_score=0.05,
            title="Company updates internal corporate sustainability website",
            published_at=old_ts
        )
        self.assertIn(level, [IMPACT_LOW, IMPACT_MEDIUM])
        self.assertLess(score, 50.0)

    def test_recency_decay(self):
        title = "Federal Reserve announces unexpected interest rate decision"
        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        old_ts = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")

        _, score_now, _ = NewsImpactScorer.calculate_impact(NEWS_CAT_INTEREST_RATES, 0.5, title, published_at=now_ts)
        _, score_old, _ = NewsImpactScorer.calculate_impact(NEWS_CAT_INTEREST_RATES, 0.5, title, published_at=old_ts)

        self.assertGreater(score_now, score_old)


class TestNewsDeduplication(unittest.TestCase):
    """Test canonical URL and headline token similarity deduplication"""

    def test_exact_url_deduplication(self):
        item1 = NormalizedNews(title="Title 1", url="https://reuters.com/article1?utm_source=twitter")
        item2 = NormalizedNews(title="Title 1", url="https://reuters.com/article1?utm_source=facebook")
        deduped = NewsDeduplicator.deduplicate([item1, item2])
        self.assertEqual(len(deduped), 1)

    def test_fuzzy_headline_similarity(self):
        item1 = NormalizedNews(title="Apple reports record Q4 earnings beating Wall Street expectations", url="https://source1.com/a")
        item2 = NormalizedNews(title="Apple reports record Q4 earnings beat Wall St expectations", url="https://source2.com/b")
        item3 = NormalizedNews(title="Crude oil surges 5% as OPEC cuts output quotas", url="https://source3.com/c")

        deduped = NewsDeduplicator.deduplicate([item1, item2, item3])
        # item1 and item2 are duplicates of the same story; item3 is unique
        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[1].title, item3.title)


class TestNewsEngine(unittest.TestCase):
    """Test central NewsEngine orchestration and symbol sentiment synthesis"""

    def test_symbol_sentiment_aggregation(self):
        mock_finnhub = MagicMock()
        mock_finnhub.get_company_news.return_value = [
            NormalizedNews(title="Apple earnings surge to new high", description="Robust profit growth", published_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            NormalizedNews(title="Apple unveils breakthrough new AI iPhone", description="Strong consumer demand", published_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            NormalizedNews(title="Apple stock upgraded by Morgan Stanley", description="Target raised to $250", published_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        ]

        engine = NewsEngine(finnhub_client=mock_finnhub)
        profile = engine.get_symbol_sentiment("AAPL")

        self.assertEqual(profile["symbol"], "AAPL")
        self.assertEqual(profile["sentiment"], SENTIMENT_POSITIVE)
        self.assertGreater(profile["sentiment_score"], 0.2)
        self.assertEqual(profile["bullish_count"], 3)
        self.assertEqual(profile["bearish_count"], 0)

    def test_filter_news(self):
        articles = [
            EnrichedNewsArticle(title="Apple Earnings Beat", symbol="AAPL", category=NEWS_CAT_EARNINGS, sentiment=SENTIMENT_POSITIVE, impact=IMPACT_HIGH, impact_score=75.0),
            EnrichedNewsArticle(title="Tesla Misses Delivery Target", symbol="TSLA", category=NEWS_CAT_COMPANY_ANNOUNCEMENTS, sentiment=SENTIMENT_NEGATIVE, impact=IMPACT_MEDIUM, impact_score=45.0),
            EnrichedNewsArticle(title="CPI Inflation Climbs", symbol="", category=NEWS_CAT_INFLATION, sentiment=SENTIMENT_NEGATIVE, impact=IMPACT_CRITICAL, impact_score=85.0)
        ]

        # Filter by symbol
        res_sym = NewsEngine.filter_news(articles, symbol="AAPL")
        self.assertEqual(len(res_sym), 1)
        self.assertEqual(res_sym[0].symbol, "AAPL")

        # Filter by sentiment
        res_sent = NewsEngine.filter_news(articles, sentiment=SENTIMENT_NEGATIVE)
        self.assertEqual(len(res_sent), 2)

        # Filter by min impact score
        res_imp = NewsEngine.filter_news(articles, min_impact_score=70.0)
        self.assertEqual(len(res_imp), 2)


if __name__ == "__main__":
    unittest.main()
