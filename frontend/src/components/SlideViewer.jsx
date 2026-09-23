import React, { useState } from 'react';
import { api } from '../api';

export default function SlideViewer({ slides, onSlideUpdated }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [editing, setEditing] = useState(false);
  const [editContent, setEditContent] = useState("");

  const activeSlide = slides[activeIndex];

  if (!slides || slides.length === 0) {
    return <div className="p-8 text-center text-gray-500 bg-white rounded-lg shadow">Загрузите презентацию для просмотра слайдов</div>;
  }

  const handleEditToggle = () => {
    if (!editing) {
      setEditContent(JSON.stringify(activeSlide, null, 2));
    }
    setEditing(!editing);
  };

  const handleSave = async () => {
    try {
      const parsed = JSON.parse(editContent);
      const res = await api.updateSlide(activeIndex, parsed);
      onSlideUpdated(res.data.slides);
      setEditing(false);
    } catch (e) {
      alert("Ошибка при сохранении: " + e.message);
    }
  };

  return (
    <div className="flex bg-white rounded-lg shadow h-[500px] overflow-hidden">
      {}
      <div className="w-1/4 border-r overflow-y-auto bg-gray-50 p-2">
        {slides.map((slide, idx) => (
          <div 
            key={idx} 
            onClick={() => { setActiveIndex(idx); setEditing(false); }}
            className={`p-3 mb-2 rounded cursor-pointer border-2 transition ${activeIndex === idx ? 'border-blue-500 bg-blue-50' : 'border-transparent hover:bg-gray-200'}`}
          >
            <div className="text-xs font-bold text-gray-500 mb-1">Слайд {idx + 1}</div>
            <div className="text-sm font-semibold truncate">{slide.title || "Без заголовка"}</div>
          </div>
        ))}
      </div>

      {}
      <div className="w-3/4 p-6 flex flex-col">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Слайд {activeIndex + 1}</h2>
          <div>
            {editing ? (
              <>
                <button onClick={() => setEditing(false)} className="text-gray-500 mr-3">Отмена</button>
                <button onClick={handleSave} className="bg-green-600 text-white px-4 py-2 rounded">Сохранить</button>
              </>
            ) : (
              <button onClick={handleEditToggle} className="bg-blue-600 text-white px-4 py-2 rounded">Редактировать</button>
            )}
          </div>
        </div>

        <div className="flex-1 bg-gray-100 p-6 rounded border overflow-y-auto">
          {editing ? (
            <textarea 
              className="w-full h-full p-4 font-mono text-sm border rounded"
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
            />
          ) : (
            <div>
              <h1 className="text-3xl font-bold mb-6 text-center">{activeSlide.title}</h1>
              <ul className="list-disc pl-8 space-y-2 text-lg">
                {(activeSlide.bullets || []).map((bullet, i) => (
                  <li key={i}>{bullet}</li>
                ))}
              </ul>
              {activeSlide.stat_num && (
                <div className="mt-8 p-4 bg-blue-100 rounded text-center">
                  <div className="text-4xl font-black text-blue-800">{activeSlide.stat_num}</div>
                  <div className="text-gray-600 mt-1">{activeSlide.stat_label}</div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
