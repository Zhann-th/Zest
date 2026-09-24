import json
import os
import re
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
TRAINING_FILE = os.path.join(DATA_DIR, "training_memory.json")
DEFAULT_TRAINING_DATA = {
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
                {"title": "Future Roadmap", "bullets": ["Q1: Core platform launch", "Q2: AI feature expansion", "Q3: Global scaling"]}
            ]
        },
        {
            "keyword": "executive summary",
            "slides_count": 3,
            "theme": "corporate_navy",
            "structure": [
                {"title": "Strategic Highlights", "bullets": ["Key operational milestones achieved", "Performance metrics exceeding targets", "Quarterly growth indicators"]},
                {"title": "Financial Performance", "layout": "stat_callout", "stat_num": "+35%", "stat_label": "Year-over-Year Revenue Growth", "bullets": ["Cost optimization initiatives successful", "EBITDA expansion across divisions"]},
                {"title": "Next Steps & Action Items", "bullets": ["Resource allocation focus", "Key milestone deadlines", "Risk management strategy"]}
            ]
        },
        {
            "keyword": "tech architecture",
            "slides_count": 4,
            "theme": "vibrant_gradient",
            "structure": [
                {"title": "System Architecture", "bullets": ["High-throughput microservices", "Scalable cloud infrastructure", "Event-driven message broker"]},
                {"title": "Data Pipeline", "bullets": ["Real-time data ingestion", "Automated ETL processing", "Secure database clustering"]},
                {"title": "Security & Compliance", "bullets": ["End-to-end encryption at rest & transit", "Role-based access control (RBAC)", "SOC2 & ISO compliance ready"]},
                {"title": "Performance Metrics", "layout": "stat_callout", "stat_num": "99.99%", "stat_label": "System Uptime SLA", "bullets": ["Sub-50ms latency globally", "Auto-scaling infrastructure"]}
            ]
        }
    ],
    "custom_rules": [
        "Maximum 4 bullet points per slide for optimal readability.",
        "Use stat_callout layout whenever numeric metrics are present.",
        "Titles should be action-oriented and under 8 words."
    ]
}
class AIProcessor:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.training_data = self._load_training_memory()
    def _load_training_memory(self):
        if os.path.exists(TRAINING_FILE):
            try:
                with open(TRAINING_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading training file: {e}")
        with open(TRAINING_FILE, 'w') as f:
            json.dump(DEFAULT_TRAINING_DATA, f, indent=2)
        return DEFAULT_TRAINING_DATA
    def _save_training_memory(self):
        with open(TRAINING_FILE, 'w') as f:
            json.dump(self.training_data, f, indent=2)
    def train_custom_rule(self, rule_text):
        """Adds a custom presentation rule to the AI memory."""
        if rule_text not in self.training_data["custom_rules"]:
            self.training_data["custom_rules"].append(rule_text)
            self._save_training_memory()
            return True
        return False
    def train_template(self, keyword, theme, slides_structure):
        """Trains the AI with a custom template mapping."""
        existing = False
        for item in self.training_data["intent_templates"]:
            if item["keyword"].lower() == keyword.lower():
                item["theme"] = theme
                item["structure"] = slides_structure
                item["slides_count"] = len(slides_structure)
                existing = True
                break
        if not existing:
            self.training_data["intent_templates"].append({
                "keyword": keyword.lower(),
                "slides_count": len(slides_structure),
                "theme": theme,
                "structure": slides_structure
            })
        self._save_training_memory()
        return True
    def parse_user_prompt(self, prompt, web_researcher=None):
        """
        Parses natural language prompt and generates structured presentation commands.
        Supports intent detection, web search integration, and template matching.
        """
        prompt_lower = prompt.lower()
        needs_web_search = any(w in prompt_lower for w in ["search", "internet", "web", "online", "research", "find facts", "google"])
        matched_template = None
        for tmpl in self.training_data["intent_templates"]:
            if tmpl["keyword"] in prompt_lower:
                matched_template = tmpl
                break
        theme = "modern_dark"
        if "corporate" in prompt_lower or "navy" in prompt_lower or "finance" in prompt_lower:
            theme = "corporate_navy"
        elif "vibrant" in prompt_lower or "tech" in prompt_lower or "dark" in prompt_lower:
            theme = "vibrant_gradient"
        elif "clean" in prompt_lower or "light" in prompt_lower or "white" in prompt_lower:
            theme = "clean_light"
        elif matched_template:
            theme = matched_template.get("theme", "modern_dark")
        count_match = re.search(r'(\d+)\s*(?:slide|slides|page|pages)', prompt_lower)
        target_count = int(count_match.group(1)) if count_match else 4
        if needs_web_search and web_researcher:
            topic = re.sub(r'create|generate|make|presentation|pptx|deck|slides?|search|web|online|research|about|on', '', prompt, flags=re.IGNORECASE).strip()
            topic = topic or prompt
            web_slides = web_researcher.extract_slide_content_from_web(topic, max_slides=target_count)
            return {
                "action": "CREATE_DECK",
                "title": f"Presentation: {topic.title()}",
                "subtitle": "Generated with Live Web Intelligence",
                "theme": theme,
                "slides": web_slides,
                "source": "live_web_search"
            }
        if matched_template:
            return {
                "action": "CREATE_DECK",
                "title": f"{matched_template['keyword'].title()} Deck",
                "subtitle": f"Generated using trained AI template ({theme} theme)",
                "theme": theme,
                "slides": matched_template["structure"],
                "source": "trained_template"
            }
        topic = re.sub(r'create|generate|make|presentation|pptx|deck|slides?|about|on', '', prompt, flags=re.IGNORECASE).strip()
        topic = topic or "Strategic Overview"
        generated_slides = [
            {
                "title": f"Introduction to {topic.title()}",
                "bullets": [
                    f"Overview of core concepts and objectives in {topic}.",
                    "Key focus areas and strategic priorities.",
                    "Scope of presentation and expected outcomes."
                ]
            },
            {
                "title": f"Key Pillars of {topic.title()}",
                "bullets": [
                    "Pillar 1: Core foundational capabilities.",
                    "Pillar 2: Operational efficiency and speed.",
                    "Pillar 3: Long-term value creation."
                ]
            },
            {
                "title": f"Market Impact & Data",
                "layout": "stat_callout",
                "stat_num": "4.8x",
                "stat_label": "Accelerated Growth Factor",
                "bullets": [
                    "Measurable impact across target segments.",
                    "Improved decision making and adoption rates."
                ]
            },
            {
                "title": "Conclusion & Next Steps",
                "bullets": [
                    "Summary of key findings and recommendations.",
                    "Immediate action items for implementation.",
                    "Q&A and contact details."
                ]
            }
        ]
        return {
            "action": "CREATE_DECK",
            "title": topic.title(),
            "subtitle": "AI Generated Presentation Deck",
            "theme": theme,
            "slides": generated_slides[:target_count],
            "source": "custom_ai_generation"
        }
    def get_training_summary(self):
        """Returns the current training state of the AI engine."""
        return {
            "trained_templates_count": len(self.training_data.get("intent_templates", [])),
            "templates": [t["keyword"] for t in self.training_data.get("intent_templates", [])],
            "custom_rules": self.training_data.get("custom_rules", [])
        }