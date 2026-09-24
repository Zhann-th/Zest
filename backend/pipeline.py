"""
pipeline.py — Оркестратор (центральный пайплайн).
Принимает пользовательский промпт и координирует модули:
    Промпт → NLU (parse_intent) → Маршрутизация → Действие → Результат
Связывает nlu_engine, web_search, trainer и pptx_io.
"""
import os
import uuid
import re
import json
import logging
from pptx_io import PptxIO
from nlu_engine import (
    NLUEngine,
    INTENT_CREATE,
    INTENT_EDIT,
    INTENT_DELETE,
    INTENT_ADD,
    INTENT_SEARCH,
    INTENT_UNKNOWN,
)
from web_search import WebSearch
from trainer import Trainer
from llm_client import LLMClient
from pptx_io import PptxIO
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "outputs")
UPLOAD_DIR = os.path.join(BASE_DIR, "..", "uploads")
class Pipeline:
    """
    Оркестратор AI-пайплайна.
    Использование:
        pipe = Pipeline()
        result = pipe.process_prompt("Создай 5 слайдов про AI")
    """
    def __init__(self):
        self.nlu = NLUEngine()
        self.web = WebSearch()
        self.trainer = Trainer()
        self.pptx = PptxIO()
        self.llm = LLMClient()
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(UPLOAD_DIR, exist_ok=True)
    def process_prompt(self, prompt, existing_filepath=None, template="random"):
        """
        Обрабатывает пользовательский промпт и выполняет действие.
        Args:
            prompt: текстовая команда пользователя
            existing_filepath: путь к загруженному PPTX (для редактирования)
        Returns:
            dict:
                - success: bool
                - action: str (интент)
                - message: str
                - output_filepath: str | None
                - download_url: str | None
                - slides: list | None (для UI)
                - nlu_result: dict
                - source: str
        """
        nlu_result = self.nlu.parse_intent(prompt)
        intent = nlu_result["intent"]
        entities = nlu_result["entities"]
        matched_template = self.trainer.match_template(prompt)
        if intent == INTENT_CREATE:
            return self._handle_create(prompt, entities, matched_template, template)
        elif intent == INTENT_EDIT:
            return self._handle_edit(entities, existing_filepath)
        elif intent == INTENT_DELETE:
            return self._handle_delete(entities, existing_filepath)
        elif intent == INTENT_ADD:
            return self._handle_add(entities, existing_filepath)
        elif intent == INTENT_SEARCH:
            return self._handle_search(entities, prompt, template)
        elif intent == INTENT_UNKNOWN:
            if entities.get("topic"):
                return self._handle_create(prompt, entities, matched_template, template)
            return {
                "success": False,
                "action": INTENT_UNKNOWN,
                "message": "Не удалось распознать команду. Попробуйте: 'Создай презентацию про AI на 5 слайдов'",
                "output_filepath": None,
                "download_url": None,
                "slides": None,
                "nlu_result": nlu_result,
                "source": "unknown",
            }
        return {
            "success": False,
            "action": intent,
            "message": f"Неизвестный интент: {intent}",
            "output_filepath": None,
            "download_url": None,
            "slides": None,
            "nlu_result": nlu_result,
            "source": "error",
        }
    def _handle_create(self, prompt, entities, matched_template, template="random"):
        """Создание новой презентации."""
        topic = entities.get("topic", "") or "Strategic Overview"
        slide_count = entities.get("slide_count", 0) or 4
        theme = entities.get("theme", "modern_dark")
        needs_search = entities.get("needs_web_search", False)
        slides_content = []
        source = "custom_ai_generation"
        if matched_template:
            slides_content = matched_template["structure"]
            theme = matched_template.get("theme", theme)
            source = "trained_template"
            title = f"{matched_template['keyword'].title()} Deck"
            subtitle = f"Generated using trained AI template ({theme} theme)"
        elif needs_search:
            slides_content = self.web.format_facts(topic, max_slides=slide_count)
            source = "live_web_search"
            title = f"Presentation: {topic.title()}"
            subtitle = "Generated with Live Web Intelligence"
        else:
            slides_content = self._generate_topic_slides(topic, slide_count)
            source = "custom_ai_generation"
            title = topic.title()
            subtitle = "AI Generated Presentation Deck"
        output_filename = f"deck_{uuid.uuid4().hex[:8]}.pptx"
        output_filepath = os.path.join(OUTPUT_DIR, output_filename)
        self.pptx.create_presentation(
            title=title,
            subtitle=subtitle,
            slides_content=slides_content[:slide_count],
            template_filename=template,
            output_filepath=output_filepath,
        )
        inspection = self.pptx.read_pptx(output_filepath)
        return {
            "success": True,
            "action": INTENT_CREATE,
            "message": f"Презентация '{title}' успешно создана ({len(slides_content)} слайдов, тема: {theme})",
            "output_filepath": output_filepath,
            "output_filename": output_filename,
            "download_url": f"/api/download/{output_filename}",
            "slides": inspection["slides"],
            "nlu_result": {"intent": INTENT_CREATE, "entities": entities},
            "source": source,
            "command_summary": {
                "title": title,
                "subtitle": subtitle,
                "theme": theme,
                "slides": slides_content[:slide_count],
            },
        }
    def _handle_edit(self, entities, existing_filepath):
        """Редактирование существующего слайда."""
        if not existing_filepath or not os.path.exists(existing_filepath):
            return {
                "success": False,
                "action": INTENT_EDIT,
                "message": "Для редактирования необходимо сначала загрузить PPTX-файл.",
                "output_filepath": None,
                "download_url": None,
                "slides": None,
                "nlu_result": {"intent": INTENT_EDIT, "entities": entities},
                "source": "error",
            }
        slide_index = entities.get("slide_index", 1)
        changes = {}
        if entities.get("new_title"):
            changes["new_title"] = entities["new_title"]
        if entities.get("new_text"):
            changes["new_bullets"] = [entities["new_text"]]
        output_filename = f"edited_{uuid.uuid4().hex[:8]}.pptx"
        output_filepath = os.path.join(OUTPUT_DIR, output_filename)
        try:
            self.pptx.modify_slide(existing_filepath, slide_index, changes, output_filepath)
            inspection = self.pptx.read_pptx(output_filepath)
            return {
                "success": True,
                "action": INTENT_EDIT,
                "message": f"Слайд {slide_index} успешно отредактирован.",
                "output_filepath": output_filepath,
                "output_filename": output_filename,
                "download_url": f"/api/download/{output_filename}",
                "slides": inspection["slides"],
                "nlu_result": {"intent": INTENT_EDIT, "entities": entities},
                "source": "edit",
            }
        except IndexError as e:
            return {
                "success": False,
                "action": INTENT_EDIT,
                "message": str(e),
                "output_filepath": None,
                "download_url": None,
                "slides": None,
                "nlu_result": {"intent": INTENT_EDIT, "entities": entities},
                "source": "error",
            }
    def _handle_delete(self, entities, existing_filepath):
        """Удаление слайда."""
        if not existing_filepath or not os.path.exists(existing_filepath):
            return {
                "success": False,
                "action": INTENT_DELETE,
                "message": "Для удаления слайда необходимо сначала загрузить PPTX-файл.",
                "output_filepath": None,
                "download_url": None,
                "slides": None,
                "nlu_result": {"intent": INTENT_DELETE, "entities": entities},
                "source": "error",
            }
        slide_index = entities.get("slide_index", 0)
        if slide_index <= 0:
            return {
                "success": False,
                "action": INTENT_DELETE,
                "message": "Укажите номер слайда для удаления (например: 'удали 3-й слайд').",
                "output_filepath": None,
                "download_url": None,
                "slides": None,
                "nlu_result": {"intent": INTENT_DELETE, "entities": entities},
                "source": "error",
            }
        output_filename = f"edited_{uuid.uuid4().hex[:8]}.pptx"
        output_filepath = os.path.join(OUTPUT_DIR, output_filename)
        try:
            self.pptx.delete_slide(existing_filepath, slide_index, output_filepath)
            inspection = self.pptx.read_pptx(output_filepath)
            return {
                "success": True,
                "action": INTENT_DELETE,
                "message": f"Слайд {slide_index} успешно удалён.",
                "output_filepath": output_filepath,
                "output_filename": output_filename,
                "download_url": f"/api/download/{output_filename}",
                "slides": inspection["slides"],
                "nlu_result": {"intent": INTENT_DELETE, "entities": entities},
                "source": "delete",
            }
        except IndexError as e:
            return {
                "success": False,
                "action": INTENT_DELETE,
                "message": str(e),
                "output_filepath": None,
                "download_url": None,
                "slides": None,
                "nlu_result": {"intent": INTENT_DELETE, "entities": entities},
                "source": "error",
            }
    def _handle_add(self, entities, existing_filepath):
        """Добавление нового слайда."""
        if not existing_filepath or not os.path.exists(existing_filepath):
            return {
                "success": False,
                "action": INTENT_ADD,
                "message": "Для добавления слайда необходимо сначала загрузить PPTX-файл.",
                "output_filepath": None,
                "download_url": None,
                "slides": None,
                "nlu_result": {"intent": INTENT_ADD, "entities": entities},
                "source": "error",
            }
        topic = entities.get("topic", "Новый слайд")
        theme = entities.get("theme", "modern_dark")
        slide_data = {
            "title": topic.title() if topic else "Новый слайд",
            "bullets": [
                f"Key insights about {topic}.",
                "Supporting data and analysis.",
                "Strategic recommendations.",
            ],
        }
        output_filename = f"edited_{uuid.uuid4().hex[:8]}.pptx"
        output_filepath = os.path.join(OUTPUT_DIR, output_filename)
        self.pptx.add_slide(existing_filepath, slide_data, output_filepath, theme)
        inspection = self.pptx.read_pptx(output_filepath)
        return {
            "success": True,
            "action": INTENT_ADD,
            "message": f"Новый слайд '{slide_data['title']}' добавлен.",
            "output_filepath": output_filepath,
            "output_filename": output_filename,
            "download_url": f"/api/download/{output_filename}",
            "slides": inspection["slides"],
            "nlu_result": {"intent": INTENT_ADD, "entities": entities},
            "source": "add",
        }
    def _handle_search(self, entities, prompt, template="random"):
        """Поиск информации и создание презентации на основе найденного."""
        topic = entities.get("topic", "")
        if not topic:
            topic = re.sub(
                r"(?:search|find|google|research|найди|поиск|загугл)\w*",
                "", prompt, flags=re.IGNORECASE
            ).strip()
            topic = topic or "General Overview"
        slide_count = entities.get("slide_count", 0) or 4
        theme = entities.get("theme", "modern_dark")
        slides_content = self.web.format_facts(topic, max_slides=slide_count)
        output_filename = f"research_{uuid.uuid4().hex[:8]}.pptx"
        output_filepath = os.path.join(OUTPUT_DIR, output_filename)
        self.pptx.create_presentation(
            title=f"Research: {topic.title()}",
            subtitle="Generated with Live Web Intelligence",
            slides_content=slides_content,
            template_filename=template,
            output_filepath=output_filepath,
        )
        inspection = self.pptx.read_pptx(output_filepath)
        return {
            "success": True,
            "action": INTENT_SEARCH,
            "message": f"Найдена информация по теме '{topic}' и создана презентация ({len(slides_content)} слайдов).",
            "output_filepath": output_filepath,
            "output_filename": output_filename,
            "download_url": f"/api/download/{output_filename}",
            "slides": inspection["slides"],
            "nlu_result": {"intent": INTENT_SEARCH, "entities": entities},
            "source": "live_web_search",
            "command_summary": {
                "title": f"Research: {topic.title()}",
                "theme": theme,
                "slides": slides_content,
            },
        }
    def _generate_topic_slides(self, topic, count=4):
        """Генерирует структуры слайдов по теме, обращаясь к ИИ с данными из веб-поиска."""
        logging.info(f"Сбор фактов в интернете по теме: {topic}")
        search_results = self.web.search_topic(topic, max_results=5)
        context_text = "\n".join([f"- {r['title']}: {r['snippet']}" for r in search_results])
        logging.info(f"Запрос к локальному ИИ (Ollama) для генерации {count} слайдов на тему: {topic}")
        slides = self.llm.generate_slides(topic, count, context=context_text)
        return slides