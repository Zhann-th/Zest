import React, { useState } from 'react';
import { api } from '../api';
import { Search, PlusCircle } from 'lucide-react';

export default function FactSearch({ activeSlideIndex, onSlideUpdated }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const res = await api.searchFacts(query);
      setResults(res.data.results || []);
    } catch (err) {
      alert("Ошибка поиска: " + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleInsert = async (fact) => {
    if (activeSlideIndex === null || activeSlideIndex === undefined) {
      alert("Сначала выберите слайд для вставки!");
      return;
    }
    
    try {
      const res = await api.insertFact(activeSlideIndex, fact);
      if (res.data.slides && onSlideUpdated) {
        onSlideUpdated(res.data.slides);
      }
      alert("Факт успешно добавлен на слайд!");
    } catch (err) {
      alert("Ошибка при вставке: " + err.message);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="font-bold mb-4 flex items-center"><Search className="mr-2 h-5 w-5 text-indigo-600"/> Поиск фактов (DDG/Wiki)</h3>
      
      <form onSubmit={handleSearch} className="flex mb-4">
        <input 
          type="text" 
          placeholder="Что ищем?" 
          className="flex-1 border p-2 rounded-l-md focus:outline-none focus:border-indigo-500"
          value={query}
          onChange={e => setQuery(e.target.value)}
        />
        <button type="submit" disabled={loading} className="bg-indigo-600 text-white px-4 rounded-r-md hover:bg-indigo-700 disabled:bg-gray-400 transition">
          {loading ? "Ищем..." : "Найти"}
        </button>
      </form>

      <div className="space-y-3 max-h-[300px] overflow-y-auto">
        {results.length === 0 && !loading && (
          <p className="text-gray-500 text-sm italic">Результаты появятся здесь.</p>
        )}
        {results.map((r, i) => (
          <div key={i} className="p-3 border rounded-md hover:bg-gray-50 transition group">
            <h4 className="font-semibold text-sm mb-1">{r.title}</h4>
            <p className="text-xs text-gray-600 mb-2 line-clamp-3">{r.snippet}</p>
            <button 
              onClick={() => handleInsert(r)}
              className="text-xs bg-gray-200 hover:bg-indigo-100 hover:text-indigo-700 py-1 px-3 rounded flex items-center opacity-0 group-hover:opacity-100 transition"
            >
              <PlusCircle className="h-3 w-3 mr-1" /> Вставить в текущий слайд
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
