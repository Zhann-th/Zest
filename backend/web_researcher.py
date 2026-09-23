import urllib.parse
import requests
from bs4 import BeautifulSoup
import re

class WebResearcher:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }

    def search_web(self, query, max_results=5):
        """Searches Wikipedia & Web for reliable topic summaries, stats, and facts."""
        results = []

        try:
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
            w_resp = requests.get(wiki_url, headers=self.headers, timeout=4)
            if w_resp.status_code == 200:
                w_data = w_resp.json()
                if w_data.get("title") and w_data.get("extract"):
                    results.append({
                        "title": f"{w_data['title']} - Overview",
                        "snippet": w_data['extract'],
                        "url": w_data.get("content_urls", {}).get("desktop", {}).get("page", "https://wikipedia.org")
                    })
        except Exception as e:
            print("Wiki API error:", e)

        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                ddg_results = list(ddgs.text(query, max_results=max_results))
                for item in ddg_results:
                    href = item.get("href", "")

                    if any(x in href for x in ["google.com/mail", "reddit.com/r/recipes"]):
                        continue
                    results.append({
                        "title": item.get("title", ""),
                        "snippet": item.get("body", ""),
                        "url": href
                    })
        except Exception as e:
            print("DDGS search error:", e)

        if len(results) < max_results:
            try:
                url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                resp = requests.get(url, headers=self.headers, timeout=5)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for result in soup.find_all('div', class_='result'):
                        t_tag = result.find('a', class_='result__a')
                        s_tag = result.find('a', class_='result__snippet')
                        if t_tag and s_tag:
                            href = t_tag.get('href', '')
                            if not any(x in href for x in ["google.com/mail", "login"]):
                                results.append({
                                    "title": t_tag.get_text().strip(),
                                    "snippet": s_tag.get_text().strip(),
                                    "url": href
                                })
                        if len(results) >= max_results:
                            break
            except Exception as ex:
                print(f"Fallback search error: {ex}")

        return results[:max_results]

    def extract_slide_content_from_web(self, query, max_slides=3):
        """Searches the web and formats extracted information directly into PowerPoint slide structures."""
        raw_results = self.search_web(query, max_results=max_slides * 2)

        if not raw_results:
            return [{
                "title": f"Overview of {query.title()}",
                "bullets": [
                    f"Key market and technology insights for {query}.",
                    "Strategic implications and competitive positioning.",
                    "Industry trends and growth forecast."
                ],
                "source": "Web Research Engine"
            }]

        slides = []
        for idx, res in enumerate(raw_results[:max_slides]):
            title = res['title']
            title = re.sub(r' - Wikipedia.*$', '', title)
            title = re.sub(r' - .*$', '', title)
            title = re.sub(r' \| .*$', '', title)
            if len(title) > 55:
                title = title[:52] + "..."

            snippet = res['snippet']
            sentences = [s.strip() for s in re.split(r'\. |\n', snippet) if len(s.strip()) > 15]

            bullets = []
            stat_num = ""
            stat_label = ""

            for sent in sentences:
                stat_match = re.search(r'(\d+%(?:\.\d+)?|\$\d+(?:\.\d+)?\s*(?:billion|million|B|M)?|\d+\s*(?:billion|million))', sent, re.IGNORECASE)
                if stat_match and not stat_num:
                    stat_num = stat_match.group(1)
                    stat_label = sent[:65] + "..." if len(sent) > 65 else sent
                else:
                    if len(sent) < 130:
                        bullets.append(sent)

            if len(bullets) < 2:
                bullets.append(f"Context: {snippet[:110]}...")

            slide_type = "stat_callout" if stat_num else "bullets"

            slides.append({
                "title": title or f"Research: {query}",
                "bullets": bullets[:4],
                "layout": slide_type,
                "stat_num": stat_num,
                "stat_label": stat_label,
                "source": res['url']
            })

        return slides
