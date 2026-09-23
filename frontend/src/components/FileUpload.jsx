import React, { useState } from 'react';
import { UploadCloud } from 'lucide-react';
import { api } from '../api';

export default function FileUpload({ onUploadSuccess }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.pptx')) {
      setError("Только .pptx файлы поддерживаются");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await api.uploadFile(file);
      onUploadSuccess(response.data);
    } catch (err) {
      setError(err.response?.data?.message || "Ошибка загрузки файла");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 border-2 border-dashed border-gray-300 rounded-lg text-center bg-gray-50 hover:bg-gray-100 transition">
      <UploadCloud className="mx-auto h-12 w-12 text-blue-500 mb-4" />
      <h3 className="text-lg font-medium text-gray-900">Загрузить презентацию</h3>
      <p className="text-sm text-gray-500 mt-1">Перетащите PPTX файл сюда или кликните для выбора</p>
      
      <div className="mt-4">
        <label className="cursor-pointer bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md">
          <span>{loading ? "Загрузка..." : "Выбрать файл"}</span>
          <input type="file" className="hidden" accept=".pptx" onChange={handleFileChange} disabled={loading} />
        </label>
      </div>
      
      {error && <p className="text-red-500 text-sm mt-3">{error}</p>}
    </div>
  );
}
