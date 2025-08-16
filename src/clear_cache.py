from scraper.core import ArticleScraper

def clear_article_cache():
    scraper = ArticleScraper()
    scraper.cache.clear()
    print(f"Article cache cleared")


if __name__ == "__main__":
    clear_article_cache()
