import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import SlideViewer from './components/SlideViewer';
import ChatWindow from './components/ChatWindow';
import FactSearch from './components/FactSearch';
import History from './components/History';
import Settings from './components/Settings';
import { Presentation } from 'lucide-react';

function App() {
  const [slides, setSlides] = useState([]);
  const [activeSlideIndex, setActiveSlideIndex] = useState(null);

  const handleUploadSuccess = (data) => {
    setSlides(data.slides || []);
    setActiveSlideIndex(0);
  };

  const handleSlidesUpdate = (newSlides) => {
    setSlides(newSlides);
  };

  return (
    <div className="min-h-screen bg-gray-100 text-gray-900 font-sans">
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center">
          <Presentation className="h-8 w-8 text-blue-600 mr-3" />
          <h1 className="text-2xl font-bold text-gray-800">PPTX AI Assistant</h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left Column: Upload, Settings, History */}
          <div className="space-y-6">
            <FileUpload onUploadSuccess={handleUploadSuccess} />
            <Settings />
            <History onRestore={handleSlidesUpdate} />
          </div>

          {/* Middle Column: Slide Viewer & Chat */}
          <div className="lg:col-span-2 space-y-6">
            <SlideViewer slides={slides} onSlideUpdated={handleSlidesUpdate} />
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <ChatWindow onSlidesUpdate={handleSlidesUpdate} />
              <FactSearch activeSlideIndex={activeSlideIndex} onSlideUpdated={handleSlidesUpdate} />
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}

export default App;
