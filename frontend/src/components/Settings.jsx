import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Settings as SettingsIcon, Save } from 'lucide-react';

export default function Settings() {
  const [model, setModel] = useState('llama3.1');
  const [temperature, setTemperature] = useState(0.7);
  const [loading, setLoading] = useState(false);

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.saveSettings({ model, temperature: parseFloat(temperature) });
      alert("Настройки успешно сохранены!");
    } catch (err) {
      alert("Ошибка сохранения: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-4 h-full">
      <h3 className="font-bold mb-4 flex items-center"><SettingsIcon className="mr-2 h-5 w-5 text-gray-600"/> Настройки модели</h3>
      
      <form onSubmit={handleSave} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Выбор модели Ollama</label>
          <select 
            value={model} 
            onChange={e => setModel(e.target.value)}
            className="w-full border p-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="llama3.1">LLaMA 3.1 (Recommended)</option>
            <option value="qwen2">Qwen 2</option>
            <option value="mistral">Mistral</option>
            <option value="gemma2">Gemma 2</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Креативность (Temperature): {temperature}</label>
          <input 
            type="range" 
            min="0" max="2" step="0.1" 
            value={temperature}
            onChange={e => setTemperature(e.target.value)}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Точный</span>
            <span>Креативный</span>
          </div>
        </div>

        <button 
          type="submit" 
          disabled={loading}
          className="w-full bg-gray-800 hover:bg-gray-900 text-white p-2 rounded flex justify-center items-center transition disabled:bg-gray-400"
        >
          <Save className="h-4 w-4 mr-2" />
          {loading ? "Сохранение..." : "Сохранить параметры"}
        </button>
      </form>
    </div>
  );
}
