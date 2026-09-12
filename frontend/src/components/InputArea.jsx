import { useState, useRef, useEffect } from 'react';
import { useChatStore } from '../store/chatStore';
import { Send, Plus, Search } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function InputArea() {
  const [input, setInput] = useState('');
  const { sendMessage, isTyping, messages } = useChatStore();
  const textareaRef = useRef(null);
  
  const isInitial = messages.length === 0;

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isTyping) return;
    
    sendMessage(input.trim());
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <motion.div 
      layout
      initial={false}
      animate={{ 
        y: isInitial ? 0 : 0, 
        scale: isInitial ? 1 : 1,
      }}
      className={`w-full max-w-3xl mx-auto transition-all duration-700 ease-in-out ${isInitial ? 'mt-[30vh]' : 'mt-8 mb-4 sticky top-6 z-50'}`}
    >
      {isInitial && (
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-center mb-8"
        >
          <h1 className="text-5xl font-display text-slate mb-3">Good Morning.</h1>
          <p className="text-xl text-muted font-light">What shall we explore today?</p>
        </motion.div>
      )}

      <motion.form 
        layout
        onSubmit={handleSubmit}
        className="relative group w-full"
      >
        <div className="absolute inset-0 bg-white rounded-2xl shadow-float opacity-70 group-hover:opacity-100 transition-opacity duration-500"></div>
        <div className="relative flex items-end gap-2 bg-surface/80 backdrop-blur-xl border border-white/60 p-2 pl-4 rounded-2xl shadow-soft">
          
          <button type="button" className="p-2 text-muted hover:text-slate transition-colors rounded-full hover:bg-slate-50 mb-1">
            <Plus size={20} />
          </button>

          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything..."
            className="w-full max-h-[200px] bg-transparent border-none focus:outline-none resize-none py-3 px-2 text-slate placeholder:text-muted/60 hide-scrollbar"
            rows={1}
            disabled={isTyping}
          />
          
          <button 
            type="submit" 
            disabled={!input.trim() || isTyping}
            className={`p-3 mb-1 rounded-xl flex items-center justify-center transition-all duration-300 ${
              input.trim() && !isTyping 
                ? 'bg-slate text-white shadow-md hover:bg-slate-800 hover:shadow-lg transform hover:-translate-y-0.5' 
                : 'bg-canvas text-muted cursor-not-allowed'
            }`}
          >
            {isInitial ? <Search size={18} /> : <Send size={18} />}
          </button>
        </div>
      </motion.form>
    </motion.div>
  );
}
