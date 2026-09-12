import { motion, AnimatePresence } from "framer-motion";
import { Copy, ThumbsUp, ThumbsDown, RotateCcw, MoreHorizontal } from "lucide-react";
import { AIOrb } from "../core/AIOrb";

export const MessageList = ({ messages, isGenerating }) => {
  return (
    <div className="w-full max-w-4xl mx-auto pb-32 pt-24 px-4 flex flex-col gap-8">
      <AnimatePresence initial={false}>
        {messages.map((msg, index) => (
          <MessageBubble key={msg.id || index} message={msg} />
        ))}
        {isGenerating && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="flex flex-col items-start w-full max-w-3xl"
          >
            <div className="flex items-center gap-3 mb-2">
              <AIOrb size="small" state="thinking" />
              <span className="text-sm font-medium text-text-secondary animate-pulse">Thinking...</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

const MessageBubble = ({ message }) => {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className={`flex flex-col w-full ${isUser ? "items-end" : "items-start max-w-3xl"}`}
    >
      {!isUser && (
        <div className="flex items-center gap-3 mb-3 pl-1">
          <AIOrb size="small" state="idle" />
          <span className="text-sm font-medium text-text-primary">Aura</span>
        </div>
      )}
      
      <div 
        className={`relative group ${
          isUser 
            ? "bg-surface border border-border px-5 py-3.5 rounded-2xl rounded-tr-sm shadow-soft text-text-primary max-w-[85%]" 
            : "text-text-primary leading-relaxed text-[16px] w-full pl-11"
        }`}
      >
        <div className="prose prose-slate max-w-none">
          {message.content}
        </div>
        
        {!isUser && (
          <div className="absolute -left-2 -bottom-10 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center gap-1 pl-12 pt-2">
            <ActionButton icon={<Copy size={16} />} />
            <ActionButton icon={<ThumbsUp size={16} />} />
            <ActionButton icon={<ThumbsDown size={16} />} />
            <ActionButton icon={<RotateCcw size={16} />} />
            <ActionButton icon={<MoreHorizontal size={16} />} />
          </div>
        )}
      </div>
    </motion.div>
  );
};

const ActionButton = ({ icon }) => (
  <button className="p-1.5 text-text-muted hover:text-text-primary hover:bg-surface rounded-md transition-colors">
    {icon}
  </button>
);
