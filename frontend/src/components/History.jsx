import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { History as HistoryIcon, RotateCcw } from 'lucide-react';

export default function History({ onRestore }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadHistory = async () => {
    try {
      const res = await api.getHistory();
      setHistory(res.data.history || []);
    } catch (err) {
      console.error("Ошибка загрузки истории:", err);
    }
  };

  useEffect(() => {
    loadHistory();
    // Simple polling for history updates
    const interval = setInterval(loadHistory, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleRestore = async (versionId) => {
    setLoading(true);
    try {
      const res = await api.restoreHistory(versionId);
      if (res.data.slides && onRestore) {
        onRestore(res.data.slides);
        alert("Версия успешно восстановлена!");
      }
    } catch (err) {
      alert("Ошибка при откате версии: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="font-bold mb-4 flex items-center"><HistoryIcon className="mr-2 h-5 w-5 text-purple-600"/> История изменений</h3>
      
      <div className="space-y-2 max-h-[300px] overflow-y-auto">
        {history.length === 0 ? (
          <p className="text-gray-500 text-sm italic">История пока пуста.</p>
        ) : (
          history.map((item, i) => (
            <div key={i} className="flex justify-between items-center p-2 border-b hover:bg-gray-50 transition">
              <div>
                <p className="text-sm font-semibold">{item.action || "Обновление"}</p>
                <p className="text-xs text-gray-500">{new Date(item.timestamp).toLocaleString()}</p>
              </div>
              <button 
                onClick={() => handleRestore(item.id)}
                disabled={loading}
                className="text-purple-600 hover:bg-purple-100 p-2 rounded-full transition disabled:opacity-50"
                title="Откатить до этой версии"
              >
                <RotateCcw className="h-4 w-4" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
