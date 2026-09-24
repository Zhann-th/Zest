"""
llm_client.py — Модуль для связи с настоящей нейросетью через Ollama.
Отправляет промпты локальной модели, просит вернуть JSON-структуру
и очищает ответ от маркдауна для дальнейшей генерации слайдов.
"""
import json
import re
import requests
class LLMClient:
    def __init__(self, model_name="llama3.1", host="http://127.0.0.1:11434"):
        self.model_name = model_name
        self.api_url = f"{host}/api/generate"
    def generate_slides(self, topic: str, count: int, context: str = "") -> list:
        """Обращается к ИИ для генерации уникального контента презентации."""
        context_prompt = f"\nИспользуй следующие реальные факты из интернета для создания структуры:\n{context}\n" if context else ""
        prompt = f"""
        Ты — эксперт по созданию крутых и информативных презентаций.
        Твоя задача — сгенерировать контент для презентации на тему: "{topic}".
        Количество слайдов, которое тебе нужно сделать: ровно {count}.
        {context_prompt}
        ВАЖНЫЕ ПРАВИЛА:
        1. Каждый слайд должен быть уникальным и содержательным. Опирайся на предоставленные факты, если они есть.
        2. Верни ответ СТРОГО в формате валидного JSON-массива. Никакого лишнего текста до или после JSON.
        3. Если тема запрошена на русском, пиши на русском. Если на английском — на английском.
        Пример требуемого формата JSON:
        [
            {{
                "title": "Введение в тему",
                "layout": "title_and_content",
                "bullets": ["Первый важный факт", "Второй тезис", "Третья деталь"]
            }},
            {{
                "title": "Ключевая статистика",
                "layout": "stat_callout",
                "stat_num": "45%",
                "stat_label": "Рост рынка в 2023",
                "bullets": ["Анализ показателей", "Выводы"]
            }}
        ]
        Не добавляй комментарии. Начинай сразу с [ и заканчивай ].
        Сгенерируй {count} уникальных слайдов по теме "{topic}":
        """
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7
                }
            }
            response = requests.post(self.api_url, json=payload, timeout=60)
            response.raise_for_status()
            result_data = response.json()
            raw_text = result_data.get("response", "").strip()
            return self._parse_json(raw_text, count, topic)
        except requests.exceptions.ConnectionError:
            print("❌ ОШИБКА: Ollama не запущена на http://127.0.0.1:11434")
            return self._fallback_slides(topic, count, "ОШИБКА: Запустите Ollama!")
        except Exception as e:
            print(f"❌ ОШИБКА LLM: {str(e)}")
            return self._fallback_slides(topic, count, f"Ошибка ИИ: {str(e)}")
    def _parse_json(self, text: str, count: int, topic: str) -> list:
        """Очищает ответ от маркдауна (```json ... ```) и парсит JSON."""
        clean_text = re.sub(r"^```(?:json)?", "", text, flags=re.MULTILINE)
        clean_text = re.sub(r"```$", "", clean_text, flags=re.MULTILINE).strip()
        start_idx = clean_text.find('[')
        end_idx = clean_text.rfind(']')
        if start_idx != -1 and end_idx != -1:
            clean_text = clean_text[start_idx:end_idx+1]
        try:
            slides = json.loads(clean_text)
            if not isinstance(slides, list):
                slides = [slides]
            while len(slides) < count:
                slides.append({
                    "title": f"Дополнительный слайд {len(slides)+1}",
                    "bullets": ["Подробности можно обсудить устно.", "Тут должно было быть продолжение."]
                })
            return slides[:count]
        except json.JSONDecodeError as e:
            print(f"❌ ОШИБКА ПАРСИНГА JSON от ИИ: {e}\nСырой текст:\n{text}")
            return self._fallback_slides(topic, count, "Ошибка: ИИ вернул неверный формат")
    def _fallback_slides(self, topic: str, count: int, error_msg: str) -> list:
        """Возвращает слайды с ошибкой, если Ollama недоступна или сломалась."""
        slides = [
            {
                "title": f"Не удалось сгенерировать: {topic}",
                "bullets": [error_msg, "Убедитесь, что Ollama установлена и модель скачана (ollama run llama3.1)."]
            }
        ]
        while len(slides) < count:
            slides.append({"title": f"Пустой слайд {len(slides)+1}", "bullets": ["-"]})
        return slides[:count]
if __name__ == "__main__":
    client = LLMClient()
    print(client.generate_slides("Space Exploration", 2))