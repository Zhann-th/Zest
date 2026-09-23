"""
web_search.py — Модуль веб-поиска и парсинга.

Поиск информации в интернете через DuckDuckGo и Wikipedia API.
Извлечение фактов, статистик и форматирование в структуры для слайдов.
"""

import re
import urllib.parse
import requests
from bs4 import BeautifulSoup


class WebSearch:
    """Веб-поиск и парсинг фактов для слайдов."""

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
        }




    def search_topic(self, query, max_results=5):
        """
        Ищет информацию по теме из нескольких источников.

        Args:
            query: поисковый запрос
            max_results: максимальное количество результатов

        Returns:
            list[dict] — каждый словарь:
                - title: str
                - snippet: str
                - url: str
                - source: str ("wikipedia" | "duckduckgo" | "ddg_html")
        """
        results = []

        wiki_results = self._search_wikipedia(query)
        results.extend(wiki_results)

        ddg_results = self._search_duckduckgo(query, max_results)
        results.extend(ddg_results)

        if len(results) < max_results:
            fallback = self._search_ddg_html(query, max_results - len(results))
            results.extend(fallback)

        return results[:max_results]




    def scrape_page(self, url, max_sentences=10):
        """
        Извлекает текст со страницы.

        Args:
            url: адрес страницы
            max_sentences: максимальное количество предложений

        Returns:
            dict:
                - title: str
                - text: str
                - sentences: list[str]
        """
        try:
            resp = requests.get(url, headers=self.headers, timeout=6)
            if resp.status_code != 200:
                return {"title": "", "text": "", "sentences": []}

            soup = BeautifulSoup(resp.text, "html.parser")

            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()

            title = soup.title.string.strip() if soup.title and soup.title.string else ""

            paragraphs = []
            for p in soup.find_all("p"):
                text = p.get_text(strip=True)
                if len(text) > 30:
                    paragraphs.append(text)

            full_text = " ".join(paragraphs)

            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", full_text) if len(s.strip()) > 20]

            return {
                "title": title,
                "text": full_text[:2000],
                "sentences": sentences[:max_sentences],
            }
        except Exception as e:
            print(f"Scrape error for {url}: {e}")
            return {"title": "", "text": "", "sentences": []}




    def format_facts(self, query, max_slides=4):
        """
        Ищет информацию и форматирует в готовые структуры для слайдов.

        Args:
            query: тема поиска
            max_slides: максимальное количество слайдов

        Returns:
            list[dict] — слайды с title, bullets, layout, stat_num, stat_label, source
        """
        raw_results = self.search_topic(query, max_results=max_slides * 2)

        if not raw_results:
            return [{
                "title": f"Overview of {query.title()}",
                "bullets": [
                    f"Key insights and analysis for {query}.",
                    "Market trends and strategic implications.",
                    "Future outlook and growth projections.",
                ],
                "layout": "bullets",
                "source": "fallback",
            }]

        slides = []
        for res in raw_results[:max_slides]:

            title = res["title"]
            title = re.sub(r"\s*[-–—|]\s*Wikipedia.*$", "", title)
            title = re.sub(r"\s*[-–—|]\s*.*$", "", title)
            if len(title) > 55:
                title = title[:52] + "..."

            snippet = res["snippet"]
            sentences = [
                s.strip() for s in re.split(r"\. |\n", snippet)
                if len(s.strip()) > 15
            ]

            bullets = []
            stat_num = ""
            stat_label = ""

            for sent in sentences:

                stat_match = re.search(
                    r"(\d+(?:\.\d+)?%|\$\d+(?:\.\d+)?\s*(?:billion|million|trillion|B|M|T)?|\d+\s*(?:billion|million|trillion))",
                    sent, re.IGNORECASE,
                )
                if stat_match and not stat_num:
                    stat_num = stat_match.group(1)
                    stat_label = sent[:65] + "..." if len(sent) > 65 else sent
                else:
                    if len(sent) < 130:
                        bullets.append(sent)

            if len(bullets) < 2:
                bullets.append(f"Context: {snippet[:110]}...")

            layout = "stat_callout" if stat_num else "bullets"

            slides.append({
                "title": title or f"Research: {query}",
                "bullets": bullets[:4],
                "layout": layout,
                "stat_num": stat_num,
                "stat_label": stat_label,
                "source": res.get("url", ""),
            })

        return slides




    def _search_wikipedia(self, query):
        """Поиск через Wikipedia REST API."""
        results = []
        try:
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
            resp = requests.get(wiki_url, headers=self.headers, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("title") and data.get("extract"):
                    results.append({
                        "title": f"{data['title']} - Overview",
                        "snippet": data["extract"],
                        "url": data.get("content_urls", {}).get("desktop", {}).get("page", "https://wikipedia.org"),
                        "source": "wikipedia",
                    })
        except Exception as e:
            print(f"Wikipedia API error: {e}")

        try:
            wiki_url_ru = f"https://ru.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
            resp = requests.get(wiki_url_ru, headers=self.headers, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("title") and data.get("extract"):
                    results.append({
                        "title": f"{data['title']} (Рус.)",
                        "snippet": data["extract"],
                        "url": data.get("content_urls", {}).get("desktop", {}).get("page", "https://ru.wikipedia.org"),
                        "source": "wikipedia_ru",
                    })
        except Exception as e:
            print(f"Wikipedia RU API error: {e}")

        return results

    def _search_duckduckgo(self, query, max_results=5):
        """Поиск через DuckDuckGo (библиотека ddgs)."""
        results = []
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                ddg_results = list(ddgs.text(query, max_results=max_results))
                for item in ddg_results:
                    href = item.get("href", "")
                    if any(x in href for x in ["google.com/mail", "login", "signin"]):
                        continue
                    results.append({
                        "title": item.get("title", ""),
                        "snippet": item.get("body", ""),
                        "url": href,
                        "source": "duckduckgo",
                    })
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")

        return results

    def _search_ddg_html(self, query, max_results=3):
        """Fallback: парсинг HTML-версии DuckDuckGo."""
        results = []
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            resp = requests.get(url, headers=self.headers, timeout=5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for result_div in soup.find_all("div", class_="result"):
                    a_tag = result_div.find("a", class_="result__a")
                    s_tag = result_div.find("a", class_="result__snippet")
                    if a_tag and s_tag:
                        href = a_tag.get("href", "")
                        if not any(x in href for x in ["google.com/mail", "login"]):
                            results.append({
                                "title": a_tag.get_text(strip=True),
                                "snippet": s_tag.get_text(strip=True),
                                "url": href,
                                "source": "ddg_html",
                            })
                    if len(results) >= max_results:
                        break
        except Exception as e:
            print(f"DDG HTML fallback error: {e}")

        return results
