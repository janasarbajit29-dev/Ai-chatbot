import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { Plus, Mic, Sparkles, Loader2 } from "lucide-react";
import { SendButton } from "./SendButton";
import { useDocumentStore } from "../../store/documentStore";

export const MainComposer = ({ onSend, isGenerating, onStop }) => {
  const [isFocused, setIsFocused] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [isSmallScreen, setIsSmallScreen] = useState(() =>
    window.matchMedia("(max-width: 639px)").matches
  );
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const recognitionRef = useRef(null);
  
  const [isRecording, setIsRecording] = useState(false);
  const { uploadDocument, isUploading } = useDocumentStore();

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [inputValue]);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(max-width: 639px)");
    const updateScreenSize = (event) => setIsSmallScreen(event.matches);
    mediaQuery.addEventListener("change", updateScreenSize);
    return () => mediaQuery.removeEventListener("change", updateScreenSize);
  }, []);

  const handleSend = () => {
    if (inputValue.trim()) {
      onSend(inputValue);
      setInputValue("");
    }
  };

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      
      recognition.onstart = () => setIsRecording(true);
      
      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInputValue(transcript);
        
        // Brief timeout to show the text in the input before sending
        setTimeout(() => {
          onSend(transcript);
          setInputValue("");
        }, 300);
      };
      
      recognition.onerror = (event) => {
        console.error("Speech recognition error", event.error);
        setIsRecording(false);
        if (event.error === 'not-allowed') {
          alert("Microphone access was denied. Please allow microphone permissions.");
        } else {
          alert(`Microphone error: ${event.error}`);
        }
      };
      
      recognition.onend = () => setIsRecording(false);
      
      recognitionRef.current = recognition;
    }
  }, [onSend]);

  const handleMicClick = () => {
    if (!recognitionRef.current) {
      alert("Your browser does not support speech recognition.");
      return;
    }
    
    if (isRecording) {
      recognitionRef.current.stop();
    } else {
      try {
        recognitionRef.current.start();
      } catch (err) {
        console.error(err);
      }
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await uploadDocument(file);
    } catch (err) {
      alert(err.message || "Failed to upload document");
    }
    e.target.value = '';
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
      className="relative w-full max-w-3xl mx-auto bg-surface rounded-[24px] border p-2 flex items-center gap-1 shadow-composer transition-colors sm:items-end sm:gap-2"
    >
      <div className="flex flex-col justify-end pb-0 pl-1 sm:pb-1">
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleFileChange} 
          className="hidden" 
          accept=".pdf,.docx,.txt"
        />
        <button 
          onClick={handleUploadClick}
          disabled={isUploading || isGenerating}
          className="p-2.5 text-text-muted hover:text-text-primary hover:bg-surface-soft rounded-full transition-all active:scale-95 disabled:opacity-50"
          title="Upload Document"
        >
          {isUploading ? <Loader2 size={22} strokeWidth={2} className="animate-spin text-accent-primary" /> : <Plus size={22} strokeWidth={2} />}
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
        placeholder={isSmallScreen ? "Ask anything" : "Ask anything, upload a file, or start a thought..."}
        className={`w-full min-w-0 flex-1 sm:flex-initial whitespace-nowrap bg-transparent resize-none outline-none text-text-primary placeholder:text-text-muted py-3.5 px-0 sm:px-2 min-h-[52px] max-h-[200px] text-sm sm:text-[16px] leading-relaxed hide-scrollbar ${isGenerating ? 'opacity-50 cursor-not-allowed' : ''}`}
        rows={1}
      />

      <div className="flex items-center gap-1 pb-0 pr-1 sm:pb-1">
        <button className="p-2 text-text-muted hover:text-accent-primary hover:bg-accent-soft rounded-full transition-all active:scale-95 group">
          <Sparkles size={20} className="group-hover:rotate-12 transition-transform duration-300" />
        </button>
        <button 
          onClick={handleMicClick}
          disabled={isGenerating}
          className={`p-2 rounded-full transition-all active:scale-95 ${
            isRecording 
              ? "text-red-500 bg-red-500/10 hover:bg-red-500/20 animate-pulse" 
              : "text-text-muted hover:text-text-primary hover:bg-surface-soft"
          }`}
          title="Voice input"
        >
          <Mic size={20} />
        </button>
        <SendButton 
          onClick={isGenerating ? onStop : handleSend} 
          isGenerating={isGenerating} 
          hasInput={inputValue.trim().length > 0}
          idleFloat={!isSmallScreen}
        />
      </div>
    </motion.div>
  );
};
