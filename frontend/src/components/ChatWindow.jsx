import React, { useState, useRef, useEffect } from 'react';
import { api } from '../api';
import { Send, Bot, User, Paperclip, FileText, X } from 'lucide-react';

export default function ChatWindow({ onSlidesUpdate }) {
  const [messages, setMessages] = useState([{ role: 'ai', text: 'Привет! Я ИИ-ассистент. Что мы будем создавать или редактировать сегодня?' }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentFileId, setCurrentFileId] = useState(null);
  const [currentFileName, setCurrentFileName] = useState("");
  const endRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setLoading(true);
    setMessages(prev => [...prev, { role: 'user', text: `📎 Загружен файл: ${file.name}` }]);

    try {
      const res = await api.uploadFile(file);
      setCurrentFileId(res.data.file_id);
      setCurrentFileName(res.data.filename);
      setMessages(prev => [...prev, { 
        role: 'ai', 
        text: `Файл **${res.data.filename}** (Слайдов: ${res.data.slide_count}) успешно прочитан! Что нужно изменить?` 
      }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'ai', text: "❌ Ошибка загрузки: " + (err.response?.data?.error || err.message) }]);
    } finally {
      setLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setLoading(true);

    try {
      if (currentFileId) {
        
        const res = await api.editPresentation(currentFileId, userMsg);
        setMessages(prev => [...prev, { 
          role: 'ai', 
          text: `${res.data.message} <br/><br/> <a href="http://127.0.0.1:5055${res.data.download_url}" class="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition" target="_blank" download>Скачать измененный .pptx</a>` 
        }]);
      } else {
        
        const res = await api.draftPresentation(userMsg);
        setMessages(prev => [...prev, { 
          role: 'ai', 
          text: res.data.message || "Я подготовил структуру! Выберите стиль:",
          isTemplateChoice: true,
          topic: res.data.topic,
          slides_content: res.data.slides_content,
          templates: res.data.templates || ["base_template.pptx"]
        }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'ai', text: "❌ Ошибка: " + (err.response?.data?.error || err.message) }]);
    } finally {
      setLoading(false);
    }
  };

  const handleCompile = async (topic, slides_content, template) => {
    setLoading(true);
    setMessages(prev => [...prev, { role: 'user', text: `Выбран стиль: ${template}` }]);

    try {
      
      const res = await api.compilePresentation(topic, slides_content, template);
      
      setMessages(prev => [...prev, { 
        role: 'ai', 
        text: `${res.data.message} <br/><br/> <a href="http://127.0.0.1:5055${res.data.download_url}" class="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition" target="_blank" download>Скачать .pptx</a>` 
      }]);

      if (onSlidesUpdate) {
        onSlidesUpdate(slides_content);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'ai', text: "❌ Ошибка при сборке: " + (err.response?.data?.error || err.message) }]);
    } finally {
      setLoading(false);
    }
  };

  const clearFile = () => {
    setCurrentFileId(null);
    setCurrentFileName("");
    setMessages(prev => [...prev, { role: 'ai', text: "Файл отключен. Перехожу в режим создания новых презентаций." }]);
  };

  return (
    <div className="flex flex-col bg-white rounded-lg shadow h-[550px]">
      <div className="p-4 border-b bg-gray-50 font-semibold flex items-center justify-between">
        <div className="flex items-center">
          <Bot className="mr-2 h-5 w-5 text-blue-600" /> Чат с ИИ
        </div>
        {currentFileName && (
          <div className="flex items-center text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
            <FileText className="w-3 h-3 mr-1" /> {currentFileName}
            <button onClick={clearFile} className="ml-2 text-blue-500 hover:text-blue-900"><X className="w-3 h-3" /></button>
          </div>
        )}
      </div>
      
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-lg p-3 ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-br-none' : 'bg-gray-100 text-gray-800 rounded-bl-none'}`}>
              <div className="flex items-center mb-2 space-x-2 text-xs opacity-70">
                {msg.role === 'user' ? <><User className="h-3 w-3"/><span>Вы</span></> : <><Bot className="h-3 w-3"/><span>AI</span></>}
              </div>
              <div className="text-sm" dangerouslySetInnerHTML={{ __html: msg.text }} />
              
              {msg.isTemplateChoice && msg.templates && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {msg.templates.map(tpl => (
                    <button
                      key={tpl}
                      onClick={() => handleCompile(msg.topic, msg.slides_content, tpl)}
                      disabled={loading}
                      className="px-3 py-1 bg-white border border-gray-300 rounded hover:bg-blue-50 text-blue-600 text-xs transition disabled:opacity-50"
                    >
                      🎨 {tpl.replace('.pptx', '')}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg rounded-bl-none p-3 text-sm text-gray-500 flex items-center space-x-2">
              <Bot className="h-4 w-4 animate-pulse" />
              <span>Обработка...</span>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <form onSubmit={handleSend} className="p-3 border-t bg-gray-50 flex items-center">
        <input 
          type="file" 
          accept=".pptx" 
          hidden 
          ref={fileInputRef} 
          onChange={handleFileUpload}
        />
        <button 
          type="button" 
          onClick={() => fileInputRef.current.click()}
          className="p-2 text-gray-500 hover:text-blue-600 transition mr-2"
          title="Прикрепить .pptx для редактирования"
        >
          <Paperclip className="h-5 w-5" />
        </button>
        <input 
          type="text" 
          className="flex-1 p-2 border rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
          placeholder={currentFileId ? "Что нужно изменить в презентации?" : "Напишите идею для новой презентации..."}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()} className="bg-blue-600 hover:bg-blue-700 text-white p-2 px-4 rounded-r-md transition disabled:bg-gray-400">
          <Send className="h-5 w-5" />
        </button>
      </form>
    </div>
  );
}
