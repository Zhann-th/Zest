"""
trainer.py — Модуль обучаемой памяти.
JSON-хранилище пользовательских шаблонов, правил и правок.
Позволяет «обучать» систему под конкретного пользователя.
"""
import json
import os
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
TRAINING_FILE = os.path.join(DATA_DIR, "training_memory.json")
DEFAULT_MEMORY = {
    "intent_templates": [
        {
            "keyword": "pitch deck",
            "slides_count": 5,
            "theme": "modern_dark",
            "structure": [
                {"title": "The Problem", "bullets": ["Current industry bottlenecks", "Unmet market needs", "Pain points experienced by target users"]},
                {"title": "Our Solution", "bullets": ["Innovative AI-powered platform", "Key value proposition", "Core competitive advantages"]},
                {"title": "Market Opportunity", "layout": "stat_callout", "stat_num": "$50B+", "stat_label": "Total Addressable Market size by 2028", "bullets": ["Rapid industry growth rate of 24% YoY", "Expanding global target segment"]},
                {"title": "Business Model", "bullets": ["Subscription / SaaS revenue", "Enterprise licensing tiers", "High margin unit economics"]},
                {"title": "Future Roadmap", "bullets": ["Q1: Core platform launch", "Q2: AI feature expansion", "Q3: Global scaling"]},
            ],
        },
        {
            "keyword": "executive summary",
            "slides_count": 3,
            "theme": "corporate_navy",
            "structure": [
                {"title": "Strategic Highlights", "bullets": ["Key operational milestones achieved", "Performance metrics exceeding targets", "Quarterly growth indicators"]},
                {"title": "Financial Performance", "layout": "stat_callout", "stat_num": "+35%", "stat_label": "Year-over-Year Revenue Growth", "bullets": ["Cost optimization initiatives successful", "EBITDA expansion across divisions"]},
                {"title": "Next Steps & Action Items", "bullets": ["Resource allocation focus", "Key milestone deadlines", "Risk management strategy"]},
            ],
        },
        {
            "keyword": "tech architecture",
            "slides_count": 4,
            "theme": "vibrant_gradient",
            "structure": [
                {"title": "System Architecture", "bullets": ["High-throughput microservices", "Scalable cloud infrastructure", "Event-driven message broker"]},
                {"title": "Data Pipeline", "bullets": ["Real-time data ingestion", "Automated ETL processing", "Secure database clustering"]},
                {"title": "Security & Compliance", "bullets": ["End-to-end encryption at rest & transit", "Role-based access control (RBAC)", "SOC2 & ISO compliance ready"]},
                {"title": "Performance Metrics", "layout": "stat_callout", "stat_num": "99.99%", "stat_label": "System Uptime SLA", "bullets": ["Sub-50ms latency globally", "Auto-scaling infrastructure"]},
            ],
        },
    ],
    "custom_rules": [
        "Maximum 4 bullet points per slide for optimal readability.",
        "Use stat_callout layout whenever numeric metrics are present.",
        "Titles should be action-oriented and under 8 words.",
    ],
}
class Trainer:
    """Обучаемая память: шаблоны, правила, персистентность."""
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.memory = self._load()
    def _load(self):
        """Загружает JSON-память из файла."""
        if os.path.exists(TRAINING_FILE):
            try:
                with open(TRAINING_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Ошибка загрузки training_memory.json: {e}")
        self.memory = DEFAULT_MEMORY
        self._save()
        return DEFAULT_MEMORY
    def _save(self):
        """Сохраняет текущую память в JSON-файл."""
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(TRAINING_FILE, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)
    def save(self):
        """Публичный метод сохранения."""
        self._save()
    def load(self):
        """Публичный метод перезагрузки из файла."""
        self.memory = self._load()
        return self.memory
    def add_rule(self, rule_text):
        """
        Добавляет пользовательское правило в память.
        Returns:
            bool — True если добавлено, False если уже существует
        """
        rule_text = rule_text.strip()
        if not rule_text:
            return False
        rules = self.memory.setdefault("custom_rules", [])
        if rule_text not in rules:
            rules.append(rule_text)
            self._save()
            return True
        return False
    def get_rules(self):
        """Возвращает список всех правил."""
        return self.memory.get("custom_rules", [])
    def remove_rule(self, rule_index):
        """Удаляет правило по индексу (0-based)."""
        rules = self.memory.get("custom_rules", [])
        if 0 <= rule_index < len(rules):
            removed = rules.pop(rule_index)
            self._save()
            return removed
        return None
    def add_template(self, keyword, theme, structure):
        """
        Обучает AI новому шаблону. Обновляет существующий по ключевому слову.
        Args:
            keyword: ключевое слово-триггер
            theme: тема оформления
            structure: list[dict] — структура слайдов
        Returns:
            bool — True
        """
        keyword = keyword.lower().strip()
        templates = self.memory.setdefault("intent_templates", [])
        for tmpl in templates:
            if tmpl["keyword"].lower() == keyword:
                tmpl["theme"] = theme
                tmpl["structure"] = structure
                tmpl["slides_count"] = len(structure)
                self._save()
                return True
        templates.append({
            "keyword": keyword,
            "slides_count": len(structure),
            "theme": theme,
            "structure": structure,
        })
        self._save()
        return True
    def match_template(self, prompt):
        """
        Ищет совпадающий шаблон по ключевому слову в промпте.
        Args:
            prompt: строка запроса
        Returns:
            dict | None — найденный шаблон или None
        """
        prompt_lower = prompt.lower()
        templates = self.memory.get("intent_templates", [])
        for tmpl in templates:
            if tmpl["keyword"] in prompt_lower:
                return tmpl
        return None
    def get_templates(self):
        """Возвращает список всех шаблонов."""
        return self.memory.get("intent_templates", [])
    def remove_template(self, keyword):
        """Удаляет шаблон по ключевому слову."""
        keyword = keyword.lower().strip()
        templates = self.memory.get("intent_templates", [])
        for i, tmpl in enumerate(templates):
            if tmpl["keyword"].lower() == keyword:
                removed = templates.pop(i)
                self._save()
                return removed
        return None
    def get_summary(self):
        """Возвращает сводку обученного состояния."""
        templates = self.memory.get("intent_templates", [])
        rules = self.memory.get("custom_rules", [])
        return {
            "trained_templates_count": len(templates),
            "templates": [t["keyword"] for t in templates],
            "custom_rules_count": len(rules),
            "custom_rules": rules,
        }