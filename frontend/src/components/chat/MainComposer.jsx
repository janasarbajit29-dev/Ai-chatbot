import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { Plus, Mic, Sparkles } from "lucide-react";
import { SendButton } from "./SendButton";

export const MainComposer = ({ onSend, isGenerating, onStop }) => {
  const [isFocused, setIsFocused] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [inputValue]);

  const handleSend = () => {
    if (inputValue.trim()) {
      onSend(inputValue);
      setInputValue("");
    }
  };

  return (
    <motion.div
      animate={{
        scale: isFocused ? 1.01 : 1,
        boxShadow: isFocused 
          ? "0 12px 40px rgba(109, 99, 246, 0.08)" 
          : "0 12px 32px rgba(0, 0, 0, 0.03)",
        borderColor: isFocused ? "#E0DDFF" : "#E6EAF0"
      }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="relative w-full max-w-3xl mx-auto bg-surface rounded-[24px] border p-2 flex items-end gap-2 shadow-composer transition-colors"
    >
      <div className="flex flex-col justify-end pb-1 pl-1">
        <button className="p-2.5 text-text-muted hover:text-text-primary hover:bg-surface-soft rounded-full transition-all active:scale-95">
          <Plus size={22} strokeWidth={2} />
        </button>
      </div>

      <textarea
        ref={textareaRef}
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        }}
        disabled={isGenerating}
        placeholder="Ask anything, upload a file, or start a thought..."
        className={`w-full bg-transparent resize-none outline-none text-text-primary placeholder:text-text-muted py-3.5 px-2 min-h-[52px] max-h-[200px] text-[16px] leading-relaxed hide-scrollbar ${isGenerating ? 'opacity-50 cursor-not-allowed' : ''}`}
        rows={1}
      />

      <div className="flex items-center gap-1 pb-1 pr-1">
        <button className="p-2 text-text-muted hover:text-accent-primary hover:bg-accent-soft rounded-full transition-all active:scale-95 group">
          <Sparkles size={20} className="group-hover:rotate-12 transition-transform duration-300" />
        </button>
        <button className="p-2 text-text-muted hover:text-text-primary hover:bg-surface-soft rounded-full transition-all active:scale-95">
          <Mic size={20} />
        </button>
        <SendButton 
          onClick={isGenerating ? onStop : handleSend} 
          isGenerating={isGenerating} 
          hasInput={inputValue.trim().length > 0}
        />
      </div>
    </motion.div>
  );
};
