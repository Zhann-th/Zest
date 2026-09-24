"""
test_pipeline.py — Тесты end-to-end для всех модулей.
Тестирует:
    1. pptx_io: чтение, создание, модификация, удаление слайдов
    2. nlu_engine: распознавание интентов (рус + англ)
    3. web_search: поиск и форматирование фактов
    4. trainer: правила и шаблоны
    5. pipeline: полный пайплайн промпт → PPTX
"""
import os
import sys
import json
import time
sys.path.insert(0, os.path.dirname(__file__))
from pptx_io import PptxIO
from nlu_engine import NLUEngine, INTENT_CREATE, INTENT_EDIT, INTENT_DELETE, INTENT_ADD, INTENT_SEARCH
from web_search import WebSearch
from trainer import Trainer
from pipeline import Pipeline
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)
passed = 0
failed = 0
def test(name, condition):
    """Простой assert-like тест."""
    global passed, failed
    if condition:
        print(f"  ✅ {name}")
        passed += 1
    else:
        print(f"  ❌ {name}")
        failed += 1
def test_pptx_io():
    """Тесты модуля pptx_io."""
    print("\n═══ 1. pptx_io ═══")
    io = PptxIO()
    path = os.path.join(OUTPUT_DIR, "test_create.pptx")
    result = io.create_presentation(
        title="Test Presentation",
        subtitle="Unit Test",
        slides_content=[
            {"title": "Slide 1", "bullets": ["Bullet A", "Bullet B"]},
            {"title": "Slide 2", "bullets": ["Bullet C", "Bullet D"], "layout": "stat_callout", "stat_num": "42%", "stat_label": "Growth"},
            {"title": "Slide 3", "bullets": ["Col1-A", "Col1-B", "Col2-A", "Col2-B"], "layout": "two_column"},
        ],
        theme_name="modern_dark",
        output_filepath=path,
    )
    test("create_presentation returns path", result == path)
    test("create_presentation file exists", os.path.exists(path))
    data = io.read_pptx(path)
    test("read_pptx slide_count == 4 (title + 3)", data["slide_count"] == 4)
    test("read_pptx has slides data", len(data["slides"]) == 4)
    test("read_pptx title slide detected", "Test Presentation" in data["slides"][0]["title"])
    add_path = os.path.join(OUTPUT_DIR, "test_add.pptx")
    io.add_slide(path, {"title": "Added Slide", "bullets": ["New bullet"]}, add_path)
    add_data = io.read_pptx(add_path)
    test("add_slide increases count", add_data["slide_count"] == 5)
    del_path = os.path.join(OUTPUT_DIR, "test_delete.pptx")
    io.delete_slide(add_path, 5, del_path)
    del_data = io.read_pptx(del_path)
    test("delete_slide decreases count", del_data["slide_count"] == 4)
    mod_path = os.path.join(OUTPUT_DIR, "test_modify.pptx")
    io.modify_slide(path, 1, {"new_title": "Modified Title"}, mod_path)
    mod_data = io.read_pptx(mod_path)
    test("modify_slide file created", os.path.exists(mod_path))
def test_nlu_engine():
    """Тесты модуля nlu_engine."""
    print("\n═══ 2. nlu_engine ═══")
    nlu = NLUEngine()
    r = nlu.parse_intent("Create a 5-slide presentation about Artificial Intelligence")
    test("EN create intent", r["intent"] == INTENT_CREATE)
    test("EN slide_count == 5", r["entities"]["slide_count"] == 5)
    test("EN topic extracted", len(r["entities"]["topic"]) > 0)
    r = nlu.parse_intent("Создай презентацию на 3 слайда про космос")
    test("RU create intent", r["intent"] == INTENT_CREATE)
    test("RU slide_count == 3", r["entities"]["slide_count"] == 3)
    r = nlu.parse_intent("Замени заголовок 2-го слайда на «Новый заголовок»")
    test("RU edit intent", r["intent"] == INTENT_EDIT)
    test("RU slide_index == 2", r["entities"]["slide_index"] == 2)
    test("RU new_title extracted", "Новый заголовок" in r["entities"]["new_title"])
    r = nlu.parse_intent("Delete slide 3")
    test("EN delete intent", r["intent"] == INTENT_DELETE)
    test("EN slide_index == 3", r["entities"]["slide_index"] == 3)
    r = nlu.parse_intent("Добавь слайд про машинное обучение")
    test("RU add intent", r["intent"] == INTENT_ADD)
    r = nlu.parse_intent("Search the web for AI trends and create a deck")
    test("EN search triggers web", r["entities"]["needs_web_search"])
    r = nlu.parse_intent("Create deck with corporate theme")
    test("Theme detection corporate", r["entities"]["theme"] == "corporate_navy")
    r = nlu.parse_intent("Сделай яркую презентацию")
    test("Theme detection vibrant (RU)", r["entities"]["theme"] == "vibrant_gradient")
def test_web_search():
    """Тесты модуля web_search."""
    print("\n═══ 3. web_search ═══")
    ws = WebSearch()
    results = ws.search_topic("Artificial Intelligence", max_results=3)
    test("search_topic returns results", len(results) >= 1)
    test("search_topic has title", "title" in results[0])
    test("search_topic has snippet", "snippet" in results[0])
    slides = ws.format_facts("Electric Vehicles", max_slides=3)
    test("format_facts returns slides", len(slides) >= 1)
    test("format_facts has title", "title" in slides[0])
    test("format_facts has bullets", "bullets" in slides[0])
def test_trainer():
    """Тесты модуля trainer."""
    print("\n═══ 4. trainer ═══")
    t = Trainer()
    added = t.add_rule("Test rule: always use 3 bullets per slide.")
    test("add_rule returns True", added)
    duplicate = t.add_rule("Test rule: always use 3 bullets per slide.")
    test("add_rule duplicate returns False", not duplicate)
    rules = t.get_rules()
    test("get_rules contains new rule", "Test rule: always use 3 bullets per slide." in rules)
    t.add_template("test_keyword", "clean_light", [
        {"title": "Test Slide", "bullets": ["A", "B"]},
    ])
    matched = t.match_template("Please create a test_keyword presentation")
    test("match_template finds template", matched is not None)
    test("match_template correct theme", matched["theme"] == "clean_light")
    summary = t.get_summary()
    test("get_summary has templates count", summary["trained_templates_count"] > 0)
    test("get_summary has rules count", summary["custom_rules_count"] > 0)
    t.remove_template("test_keyword")
    t.remove_rule(len(t.get_rules()) - 1)
def test_pipeline():
    """Тесты полного пайплайна."""
    print("\n═══ 5. pipeline (end-to-end) ═══")
    pipe = Pipeline()
    t0 = time.time()
    result = pipe.process_prompt("Create a 3 slide presentation about Space Exploration")
    elapsed = time.time() - t0
    test("pipeline success", result["success"])
    test("pipeline action == CREATE_DECK", result["action"] == INTENT_CREATE)
    test("pipeline has output_filepath", result.get("output_filepath") is not None)
    test("pipeline file exists", os.path.exists(result["output_filepath"]))
    test("pipeline has slides", result.get("slides") is not None and len(result["slides"]) > 0)
    test(f"pipeline latency < 5s ({elapsed:.1f}s)", elapsed < 5)
    result_ru = pipe.process_prompt("Сделай презентацию про искусственный интеллект на 4 слайда")
    test("RU pipeline success", result_ru["success"])
    test("RU pipeline has slides", len(result_ru.get("slides", [])) > 0)
    result_tmpl = pipe.process_prompt("Create a pitch deck for my startup")
    test("Trained template matched", result_tmpl.get("source") == "trained_template")
    result_unk = pipe.process_prompt("xyz abc 123")
    test("Unknown command handled", result_unk is not None)
if __name__ == "__main__":
    print("🧪 Zest v2.0 — Test Suite")
    print("=" * 50)
    test_pptx_io()
    test_nlu_engine()
    test_web_search()
    test_trainer()
    test_pipeline()
    print("\n" + "=" * 50)
    total = passed + failed
    print(f"📊 Results: {passed}/{total} passed, {failed} failed")
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {failed} test(s) failed.")
    sys.exit(0 if failed == 0 else 1)