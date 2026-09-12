import { motion } from 'framer-motion';
import { Bot, User, Copy, Check, Sparkles } from 'lucide-react';
import { useState } from 'react';

export default function MessageCard({ message }) {
  const isAI = message.role === 'assistant';
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!isAI) {
    return (
      <motion.div 
        initial={{ opacity: 0, y: 10, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="w-full max-w-3xl mx-auto my-6 px-4"
      >
        <div className="flex items-center gap-3 mb-2 text-muted px-2">
          <div className="bg-canvas p-1.5 rounded-full border border-black/5">
            <User size={14} />
          </div>
          <span className="text-sm font-medium tracking-wide">You</span>
        </div>
        <div className="text-lg text-slate font-medium px-2 leading-relaxed">
          {message.content}
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className="w-full max-w-3xl mx-auto mb-12 group relative"
    >
      <div className="absolute inset-0 bg-white rounded-3xl shadow-soft opacity-60"></div>
      
      <div className="relative bg-surface/90 backdrop-blur-xl border border-white/60 p-6 sm:p-8 rounded-3xl">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="bg-powder/30 text-slate p-2 rounded-xl">
              <Sparkles size={18} className="text-blue-500" />
            </div>
            <span className="font-display font-medium text-slate">Aura</span>
          </div>
          
          <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <button onClick={handleCopy} className="p-2 text-muted hover:text-slate hover:bg-canvas rounded-lg transition-colors">
              {copied ? <Check size={16} /> : <Copy size={16} />}
            </button>
          </div>
        </div>
        
        <div className="prose prose-slate max-w-none text-slate/90 leading-relaxed font-light">
          {message.content.split('\n').map((paragraph, i) => (
            <p key={i} className="mb-4 last:mb-0">
              {paragraph}
            </p>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
