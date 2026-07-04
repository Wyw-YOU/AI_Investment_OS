"""Tests for news service key event extraction."""
from app.services.news import NewsService


class TestKeyEventsExtraction:
    def setup_method(self):
        self.service = NewsService()

    def test_high_impact_event(self):
        news = [{"title": "茅台Q3业绩大幅超预期", "time": "2026-07-04", "source": "财联社"}]
        events = self.service.extract_key_events(news)
        assert len(events) == 1
        assert events[0]["impact"] == "high"

    def test_medium_impact_event(self):
        news = [{"title": "公司发布分红方案", "time": "2026-07-04", "source": "证券时报"}]
        events = self.service.extract_key_events(news)
        assert len(events) == 1
        assert events[0]["impact"] == "medium"

    def test_low_impact_filtered(self):
        news = [{"title": "机构调研公司最新动态", "time": "2026-07-04", "source": "上证报"}]
        events = self.service.extract_key_events(news)
        assert len(events) == 0

    def test_mixed_news(self):
        news = [
            {"title": "公司收购海外资产", "time": "", "source": ""},
            {"title": "日常交易公告", "time": "", "source": ""},
            {"title": "股东增持计划", "time": "", "source": ""},
        ]
        events = self.service.extract_key_events(news)
        assert len(events) == 2
