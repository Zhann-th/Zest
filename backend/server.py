"""
server.py — Flask REST API сервер.

Эндпоинты:
    GET  /api/status           — статус + память
    POST /api/upload-pptx      — загрузка и парсинг PPTX
    POST /api/process-prompt   — полный пайплайн (NLU → действие → PPTX)
    POST /api/web-search       — только веб-поиск
    POST /api/train            — обучение правил / шаблонов
    GET  /api/download/<file>  — скачивание результата
"""

import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from pipeline import Pipeline
from pptx_io import PptxIO
from web_search import WebSearch
from trainer import Trainer


app = Flask(__name__, static_folder="../frontend", static_url_path="/")
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "..", "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "..", "outputs")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Инициализация модулей
pipe = Pipeline()
pptx_io = PptxIO()
web = WebSearch()
trainer = Trainer()


# ═══════════════════════════════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════════════════════════════

@app.route("/api/status", methods=["GET"])
def get_status():
    """Возвращает статус сервера и сводку обученной памяти."""
    return jsonify({
        "status": "online",
        "engine": "Zest v2.0 — Modular Architecture",
        "modules": ["pptx_io", "nlu_engine", "web_search", "trainer", "pipeline"],
        "training": trainer.get_summary(),
    })


@app.route("/api/templates", methods=["GET"])
def get_templates():
    """Возвращает список доступных .pptx шаблонов."""
    templates_dir = os.path.join(BASE_DIR, "templates")
    os.makedirs(templates_dir, exist_ok=True)
    templates = [f for f in os.listdir(templates_dir) if f.endswith(".pptx")]
    if not templates:
        # Убедимся, что хотя бы base_template существует
        from pptx import Presentation
        prs = Presentation()
        prs.save(os.path.join(templates_dir, "base_template.pptx"))
        templates = ["base_template.pptx"]
    return jsonify({"templates": templates})


@app.route("/api/upload-pptx", methods=["POST"])
def upload_pptx():
    """Загружает PPTX и возвращает структуру слайдов."""
    if "file" not in request.files:
        return jsonify({"error": "Файл не загружен"}), 400

    file = request.files["file"]
    if not file.filename.endswith(".pptx"):
        return jsonify({"error": "Файл должен быть в формате .pptx"}), 400

    file_id = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, file_id)
    file.save(filepath)

    try:
        inspection = pptx_io.read_pptx(filepath)
        return jsonify({
            "file_id": file_id,
            "filename": file.filename,
            "slide_count": inspection["slide_count"],
            "slides": inspection["slides"],
        })
    except Exception as e:
        return jsonify({"error": f"Ошибка парсинга PPTX: {str(e)}"}), 500


@app.route("/api/process-prompt", methods=["POST"])
def process_prompt():
    """
    Полный AI-пайплайн: промпт → NLU → действие → PPTX.
    
    Body JSON:
        prompt: str — команда пользователя
        file_id: str (optional) — ID загруженного файла для редактирования
        template: str (optional) — Имя выбранного шаблона
    """
    data = request.json or {}
    prompt = data.get("prompt", "").strip()
    file_id = data.get("file_id")
    template = data.get("template", "random")

    if not prompt:
        return jsonify({"error": "Промпт обязателен"}), 400

    # Определяем путь к существующему файлу (если загружен)
    existing_filepath = None
    if file_id:
        fp = os.path.join(UPLOAD_FOLDER, file_id)
        if os.path.exists(fp):
            existing_filepath = fp

    # Запускаем пайплайн
    result = pipe.process_prompt(prompt, existing_filepath=existing_filepath, template=template)

    status_code = 200 if result["success"] else 400
    return jsonify(result), status_code


@app.route("/api/draft-presentation", methods=["POST"])
def draft_presentation():
    """ШАГ 1: Поиск и генерация структуры без создания файла."""
    data = request.json or {}
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Промпт обязателен"}), 400

    nlu_result = pipe.nlu.parse_intent(prompt)
    topic = nlu_result["entities"].get("topic", "")
    if not topic:
        import re
        topic = re.sub(r"(?:search|find|google|research|найди|поиск|загугл)\w*", "", prompt, flags=re.IGNORECASE).strip()
        topic = topic or "General Overview"
    
    slide_count = nlu_result["entities"].get("slide_count", 4)
    
    # 1. Гуглим
    slides_content = pipe.web.format_facts(topic, max_slides=slide_count)
    # Здесь можно было бы еще прогнать через LLMClient, если бы он был отделен. 
    # В текущей реализации web.format_facts возвращает готовый контент (он не вызывает LLM, LLM вызывает pptx_io... стоп, LLM вызывает _generate_topic_slides)
    
    # Чтобы сделать всё правильно, вызовем pipe._generate_topic_slides если нужно, но пока используем format_facts как в поиске.
    if not slides_content:
        slides_content = pipe._generate_topic_slides(topic, slide_count)

    # 2. Получаем шаблоны
    templates_dir = os.path.join(BASE_DIR, "templates")
    os.makedirs(templates_dir, exist_ok=True)
    templates = [f for f in os.listdir(templates_dir) if f.endswith(".pptx")]

    return jsonify({
        "success": True,
        "message": "Я подготовил структуру! Выберите стиль:",
        "topic": topic,
        "slides_content": slides_content,
        "templates": templates
    })


@app.route("/api/compile-presentation", methods=["POST"])
def compile_presentation():
    """ШАГ 2: Создание PPTX из готовой структуры и шаблона."""
    data = request.json or {}
    topic = data.get("topic", "Presentation")
    slides_content = data.get("slides_content", [])
    template = data.get("template", "random")

    if not slides_content:
        return jsonify({"error": "Нет структуры слайдов"}), 400

    output_filename = f"presentation_{uuid.uuid4().hex[:8]}.pptx"
    output_filepath = os.path.join(OUTPUT_FOLDER, output_filename)

    pipe.pptx.create_presentation(
        title=topic.title(),
        subtitle="Generated with AI",
        slides_content=slides_content,
        template_filename=template,
        output_filepath=output_filepath,
    )

    return jsonify({
        "success": True,
        "message": "Презентация готова!",
        "download_url": f"/api/download/{output_filename}"
    })


@app.route("/api/edit-presentation", methods=["POST"])
def edit_presentation():
    """ШАГ 3: Точечное редактирование загруженного файла."""
    data = request.json or {}
    prompt = data.get("prompt", "").strip()
    file_id = data.get("file_id")
    
    if not prompt or not file_id:
        return jsonify({"error": "Промпт и file_id обязательны"}), 400
        
    filepath = os.path.join(UPLOAD_FOLDER, file_id)
    if not os.path.exists(filepath):
        return jsonify({"error": "Файл не найден на сервере"}), 404
        
    # Читаем текущую структуру
    structure = pptx_io.read_pptx(filepath)
    
    # Спрашиваем ИИ (эмуляция простого NLU для демо, или вызов LLM)
    # В идеале здесь LLM получает структуру и возвращает JSON.
    # Так как мы делаем быстрый MVP, попросим ИИ сгенерировать JSON.
    sys_prompt = (
        "Ты ИИ-редактор презентаций. Пользователь хочет изменить текст.\n"
        f"Текущая структура:\n{structure['slides']}\n"
        "Определи slide_index (номер слайда) и shape_index (индекс фигуры) для изменения.\n"
        "Напиши новый текст на основе запроса пользователя.\n"
        "Ответь СТРОГО валидным JSON: {\"slide_index\": int, \"shape_index\": int, \"new_text\": \"...\"}"
    )
    
    # Для MVP используем заглушку, если LLM сломается
    try:
        from llm_client import LLMClient
        llm = LLMClient()
        ai_response = llm.generate_content(f"{sys_prompt}\nЗапрос: {prompt}")
        import json, re
        match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if match:
            edit_cmd = json.loads(match.group(0))
            s_idx = int(edit_cmd.get("slide_index", 1))
            sh_idx = int(edit_cmd.get("shape_index", 0))
            new_text = str(edit_cmd.get("new_text", "Updated Text"))
            
            output_filename = f"edited_{uuid.uuid4().hex[:8]}.pptx"
            output_filepath = os.path.join(OUTPUT_FOLDER, output_filename)
            
            pptx_io.update_shape_text(filepath, s_idx, sh_idx, new_text, output_filepath)
            
            return jsonify({
                "success": True,
                "message": "Презентация обновлена!",
                "download_url": f"/api/download/{output_filename}"
            })
    except Exception as e:
        return jsonify({"error": f"Ошибка AI или редактирования: {str(e)}"}), 500
        
    return jsonify({"error": "Не удалось распознать команду"}), 400


@app.route("/api/web-search", methods=["POST"])
def web_search():
    """Только веб-поиск (без создания PPTX)."""
    data = request.json or {}
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"error": "Поисковый запрос обязателен"}), 400

    raw_results = pipe.web.search_topic(query, max_results=5)
    formatted_slides = pipe.web.format_facts(query, max_slides=3)

    return jsonify({
        "query": query,
        "web_results": raw_results,
        "suggested_slides": formatted_slides,
    })


@app.route("/api/train", methods=["POST"])
def train_ai():
    """
    Обучение AI памяти.

    Body JSON:
        mode: "rule" | "template"
        rule: str (для mode=rule)
        keyword: str (для mode=template)
        theme: str (для mode=template)
        structure: list[dict] (для mode=template)
    """
    data = request.json or {}
    mode = data.get("mode", "rule")

    if mode == "rule":
        rule_text = data.get("rule", "").strip()
        if not rule_text:
            return jsonify({"error": "Текст правила обязателен"}), 400

        success = trainer.add_rule(rule_text)
        return jsonify({
            "message": "Правило добавлено в память AI" if success else "Правило уже существует",
            "training": trainer.get_summary(),
        })

    elif mode == "template":
        keyword = data.get("keyword", "").strip()
        theme = data.get("theme", "modern_dark")
        structure = data.get("structure", [])

        if not keyword or not structure:
            return jsonify({"error": "Ключевое слово и структура обязательны"}), 400

        trainer.add_template(keyword, theme, structure)
        return jsonify({
            "message": f"Шаблон '{keyword}' успешно обучен",
            "training": trainer.get_summary(),
        })

    return jsonify({"error": "Неверный режим обучения (используйте 'rule' или 'template')"}), 400


@app.route("/api/download/<filename>", methods=["GET"])
def download_file(filename):
    """Скачивание сгенерированного PPTX."""
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)


@app.route("/")
def serve_index():
    """Раздача главного файла фронтенда."""
    return app.send_static_file("index.html")


# ═══════════════════════════════════════════════════════════════
# Запуск
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5055))
    print(f"🚀 Zest v2.0 — сервер запущен на http://127.0.0.1:{port}")
    print(f"   Модули: pptx_io, nlu_engine, web_search, trainer, pipeline")
    print(f"   Обученных шаблонов: {trainer.get_summary()['trained_templates_count']}")
    app.run(host="0.0.0.0", port=port, debug=True)
