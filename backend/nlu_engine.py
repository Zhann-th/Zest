"""
nlu_engine.py — Модуль распознавания запросов (NLU).

Rule-based NLU для понимания команд на русском и английском:
- Классификация интентов (CREATE_DECK, EDIT_SLIDE, DELETE_SLIDE, ADD_SLIDE, SEARCH_WEB)
- Извлечение сущностей (тема, номер слайда, текст, количество, тема оформления)
- Поддержка уточняющих вопросов при неоднозначности
"""

import re




INTENT_CREATE = "CREATE_DECK"
INTENT_EDIT = "EDIT_SLIDE"
INTENT_DELETE = "DELETE_SLIDE"
INTENT_ADD = "ADD_SLIDE"
INTENT_SEARCH = "SEARCH_WEB"
INTENT_UNKNOWN = "UNKNOWN"




CREATE_PATTERNS_RU = [
    r"созда[йть].*презентаци",
    r"сделай.*презентаци",
    r"генер(?:ируй|ировать).*(?:презентаци|слайд|deck)",
    r"сделай.*слайд",
    r"создай.*deck",
    r"создай.*слайд",
    r"новую?\s+презентаци",
    r"построй.*презентаци",
]

CREATE_PATTERNS_EN = [
    r"create.*(?:presentation|deck|slides?|pptx)",
    r"generate.*(?:presentation|deck|slides?|pptx)",
    r"make.*(?:presentation|deck|slides?|pptx)",
    r"build.*(?:presentation|deck|slides?|pptx)",
    r"new\s+(?:presentation|deck)",
]

EDIT_PATTERNS_RU = [
    r"замени.*(?:заголовок|текст|буллет|содержимое).*(?:слайд|стр)",
    r"измени.*(?:слайд|стр)",
    r"(?:поменяй|обнови|перепиш).*(?:слайд|стр)",
    r"правь.*(?:слайд|стр)",
    r"отредактируй.*(?:слайд|стр)",
]

EDIT_PATTERNS_EN = [
    r"(?:edit|change|modify|update|replace).*(?:slide|page|title|text|bullet)",
    r"(?:rename|rewrite).*(?:slide|page|title)",
    r"set.*(?:title|text|heading).*(?:slide|page)",
]

DELETE_PATTERNS_RU = [
    r"удали.*(?:слайд|стр)",
    r"убери.*(?:слайд|стр)",
    r"убрать.*(?:слайд|стр)",
]

DELETE_PATTERNS_EN = [
    r"(?:delete|remove|drop).*(?:slide|page)",
]

ADD_PATTERNS_RU = [
    r"добав[ьи].*слайд",
    r"вставь.*слайд",
    r"добавить.*слайд",
]

ADD_PATTERNS_EN = [
    r"(?:add|insert|append).*(?:slide|page)",
]

SEARCH_PATTERNS_RU = [
    r"найди.*(?:информацию|факты|данные|статистику)",
    r"поиск.*(?:информаци|интернет|факт)",
    r"загугл[ий]",
    r"в интернете",
    r"из интернета",
]

SEARCH_PATTERNS_EN = [
    r"(?:search|find|lookup|google|research).*(?:web|internet|online|info|facts|data)",
    r"(?:from|on)\s+(?:the\s+)?(?:web|internet|online)",
]

THEME_KEYWORDS = {
    "modern_dark": ["modern", "dark", "модерн", "тёмн", "темн"],
    "corporate_navy": ["corporate", "navy", "finance", "корпоратив", "делов", "бизнес"],
    "vibrant_gradient": ["vibrant", "gradient", "tech", "ярк", "градиент", "технолог"],
    "clean_light": ["clean", "light", "white", "минимал", "свет", "бел", "чист"],
}


class NLUEngine:
    """Rule-based NLU для распознавания интентов и сущностей."""

    def parse_intent(self, text):
        """
        Анализирует текстовый запрос и возвращает интент + сущности.

        Args:
            text: строка пользовательского запроса

        Returns:
            dict:
                intent: str — одно из INTENT_*
                entities: dict — извлечённые сущности:
                    - topic: str
                    - slide_count: int
                    - slide_index: int (для EDIT/DELETE)
                    - new_title: str
                    - new_text: str
                    - theme: str
                    - needs_web_search: bool
                confidence: float (0.0 - 1.0)
                raw_text: str
        """
        text_lower = text.lower().strip()

        entities = {
            "topic": self._extract_topic(text),
            "slide_count": self._extract_slide_count(text_lower),
            "slide_index": self._extract_slide_index(text_lower),
            "new_title": self._extract_new_title(text_lower, text),
            "new_text": self._extract_new_text(text_lower, text),
            "theme": self._detect_theme(text_lower),
            "needs_web_search": self._needs_web_search(text_lower),
        }

        intent, confidence = self._classify_intent(text_lower, entities)

        return {
            "intent": intent,
            "entities": entities,
            "confidence": confidence,
            "raw_text": text.strip(),
        }




    def _classify_intent(self, text_lower, entities):
        """Определяет интент по regex-паттернам. Возвращает (intent, confidence)."""

        for patterns, intent in [
            (DELETE_PATTERNS_RU + DELETE_PATTERNS_EN, INTENT_DELETE),
            (EDIT_PATTERNS_RU + EDIT_PATTERNS_EN, INTENT_EDIT),
            (ADD_PATTERNS_RU + ADD_PATTERNS_EN, INTENT_ADD),
            (SEARCH_PATTERNS_RU + SEARCH_PATTERNS_EN, INTENT_SEARCH),
            (CREATE_PATTERNS_RU + CREATE_PATTERNS_EN, INTENT_CREATE),
        ]:
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return intent, 0.85

        if entities.get("needs_web_search"):
            return INTENT_SEARCH, 0.6

        if entities.get("slide_count", 0) > 0:
            return INTENT_CREATE, 0.5

        if entities.get("topic"):
            return INTENT_CREATE, 0.4

        return INTENT_UNKNOWN, 0.1




    def _extract_topic(self, text):
        """Извлекает основную тему из промпта."""

        topic = text.strip()
        remove_words_ru = [
            r"\bсозда[йть]\w*\b", r"\bсделай\b", r"\bгенер(?:ируй|ировать)\w*\b", r"\bпострой\b",
            r"\bпрезентаци\w*\b", r"\bслайд\w*\b", r"\bна\s+тему\b", r"\bо\b", r"\bпро\b",
            r"\bс\s+интернета\b", r"\bиз\s+интернета\b", r"\bнайди\b", r"\bпоиск\w*\b",
            r"\bинформаци\w*\b", r"\bфакт\w*\b", r"\bданн\w*\b", r"\bdeck\w*\b", r"\bpptx\b",
            r"\bна\b",
        ]
        remove_words_en = [
            r"\bcreate\b", r"\bgenerate\b", r"\bmake\b", r"\bbuild\b", r"\bpresentation\b",
            r"\bslides?\b", r"\bdeck\b", r"\bpptx\b", r"\babout\b", r"\bon\b", r"\bwith\b",
            r"\bsearch\b", r"\bweb\b", r"\binternet\b", r"\bonline\b", r"\bresearch\b",
            r"\bfind\b", r"\bfacts?\b", r"\binformation\b",
        ]

        for word in remove_words_ru + remove_words_en:
            topic = re.sub(word, "", topic, flags=re.IGNORECASE)

        topic = re.sub(r"\d+\s*[-\s]?\s*(?:slide|slides|слайд\w*|page|pages|стр\w*)", "", topic, flags=re.IGNORECASE)

        topic = re.sub(r"\ba\b|\ban\b|\bthe\b|\bfor\b|\bmy\b", "", topic, flags=re.IGNORECASE)

        topic = re.sub(r"\b\d+\b", "", topic)

        for theme_name, keywords in THEME_KEYWORDS.items():
            for kw in keywords:
                topic = re.sub(rf"\b{kw}\w*\b", "", topic, flags=re.IGNORECASE)

        topic = re.sub(r"\s+", " ", topic).strip()
        topic = re.sub(r"^[\s,.\-—:]+|[\s,.\-—:]+$", "", topic)

        return topic if len(topic) > 1 else ""

    def _extract_slide_count(self, text_lower):
        """Извлекает количество слайдов из текста."""

        match = re.search(r"(\d+)\s*[-\s]?\s*(?:slide|slides|слайд\w*|page|pages|стр\w*)", text_lower)
        if match:
            return int(match.group(1))

        return 0  # Не указано

    def _extract_slide_index(self, text_lower):
        """Извлекает номер слайда для редактирования/удаления."""

        patterns = [
            r"(\d+)\s*[-—]?\s*(?:й|го|ый|ой|ий)?\s*слайд",
            r"слайд\w*\s*(?:номер|№|#)?\s*(\d+)",
            r"slide\s*(?:number|#|№)?\s*(\d+)",
            r"(?:page|стр)\w*\s*(?:номер|#|№)?\s*(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return int(match.group(1))

        return 0

    def _extract_new_title(self, text_lower, original_text):
        """Извлекает новый заголовок из команды редактирования."""

        patterns = [
            r"(?:заголовок|title)\s+.*?(?:на|to|=|:)\s*[\u00ab\u201c\"'\u2018](.*?)[\u00bb\u201d\"'\u2019]",
            r"(?:на|to|=|:)\s*[\u00ab\u201c\"'\u2018](.*?)[\u00bb\u201d\"'\u2019]",
            r"(?:заголовок|title)\s*(?:на|to|=|:)\s+(.+?)(?:\.|$)",
        ]
        for pattern in patterns:
            match = re.search(pattern, original_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_new_text(self, text_lower, original_text):
        """Извлекает новый текст для замены."""
        patterns = [
            r"(?:текст|text|содержимое)\s*(?:на|to|=|:)\s*[«\"'](.*?)[»\"']",
            r"(?:текст|text|содержимое)\s*(?:на|to|=|:)\s+(.+?)(?:\.|$)",
        ]
        for pattern in patterns:
            match = re.search(pattern, original_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    def _detect_theme(self, text_lower):
        """Определяет тему оформления из текста."""
        for theme_name, keywords in THEME_KEYWORDS.items():
            for kw in keywords:

                if re.search(rf"{re.escape(kw)}", text_lower):
                    return theme_name
        return "modern_dark"  # По умолчанию

    def _needs_web_search(self, text_lower):
        """Определяет, нужен ли веб-поиск."""
        all_patterns = SEARCH_PATTERNS_RU + SEARCH_PATTERNS_EN
        for pattern in all_patterns:
            if re.search(pattern, text_lower):
                return True

        triggers = [
            "search", "internet", "web", "online", "google", "research",
            "find facts", "lookup", "интернет", "поиск", "загугл", "найди",
            "из сети", "из интернета",
        ]
        return any(t in text_lower for t in triggers)
