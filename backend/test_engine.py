import os
import sys

# Ensure backend path is in sys.path
sys.path.append(os.path.dirname(__file__))

from pptx_engine import PPTXEngine
from web_researcher import WebResearcher
from ai_processor import AIProcessor

def test_pipeline():
    print("--- 1. Testing PPTX Engine Creation & Inspection ---")
    engine = PPTXEngine()
    test_out = os.path.join(os.path.dirname(__file__), "..", "outputs", "test_deck.pptx")
    
    slides = [
        {"title": "AI Technology Trends", "bullets": ["Neural networks evolution", "Real-time AI agent capabilities", "Automated document generation"]},
        {"title": "Key Adoption Data", "layout": "stat_callout", "stat_num": "+140%", "stat_label": "Enterprise AI Adoption", "bullets": ["Increased productivity", "Cost savings across operations"]}
    ]
    
    file_path = engine.create_presentation("AI & Future Tech", "Automated PowerPoint Generation Test", slides, theme_name="modern_dark", output_filepath=test_out)
    assert os.path.exists(file_path), "Failed to generate PPTX file!"
    print(f"✅ PPTX generated at {file_path}")

    inspection = engine.inspect_pptx(file_path)
    assert inspection["slide_count"] == 3, f"Expected 3 slides (1 title + 2 content), got {inspection['slide_count']}"
    print(f"✅ PPTX inspected successfully. Found {inspection['slide_count']} slides.")

    print("\n--- 2. Testing AI Command Processor ---")
    ai = AIProcessor()
    cmd = ai.parse_user_prompt("Create a pitch deck with 5 slides using vibrant gradient theme")
    assert cmd["action"] == "CREATE_DECK"
    print(f"✅ AI Prompt parsed successfully: Action={cmd['action']}, Theme={cmd['theme']}, Source={cmd['source']}")

    print("\n--- 3. Testing Web Researcher Engine ---")
    researcher = WebResearcher()
    web_slides = researcher.extract_slide_content_from_web("Quantum Computing", max_slides=2)
    assert len(web_slides) > 0, "Failed web research slide extraction"
    print(f"✅ Web research retrieved {len(web_slides)} slides on Quantum Computing!")
    print(f"   Slide 1 Title: {web_slides[0]['title']}")

    print("\n🎉 ALL BACKEND TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_pipeline()
