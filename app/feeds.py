# app/feeds.py

FEEDS = {
    "US": {
        "business": [
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            "https://news.google.com/rss/headlines/section/BUSINESS?hl=en&gl=US&ceid=US:en",
        ],
        "tech": [
            "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
            "https://news.google.com/rss/headlines/section/SCIENCE?hl=en&gl=US&ceid=US:en",
        ],
        "general": [
            "https://news.google.com/rss?hl=en&gl=US&ceid=US:en",
        ],
    },
    "KR": {
        "business": [
            "https://rss.hankyung.com/feed/economy.xml",
            "https://news.google.com/rss/headlines/section/BUSINESS?hl=ko&gl=KR&ceid=KR:ko",
        ],
        "tech": [
            "https://rss.hankyung.com/feed/it.xml",
            "https://rss.yonhapnews.co.kr/it.xml",
            "https://news.google.com/rss/headlines/section/SCIENCE?hl=ko&gl=KR&ceid=KR:ko",
        ],
        "general": [
            "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko",
        ],
    },
}
