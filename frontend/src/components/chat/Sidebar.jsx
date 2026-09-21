import { motion, AnimatePresence } from "framer-motion";
import { X, MessageSquare, Plus, Trash2 } from "lucide-react";

export const Sidebar = ({ 
  isOpen, 
  onClose, 
  conversations, 
  activeConversation, 
  onSelect, 
  onNewChat, 
  onDelete 
}) => {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
          />
          
          {/* Sidebar */}
          <motion.div 
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed inset-y-0 left-0 z-50 w-80 bg-surface border-r border-border/50 flex flex-col shadow-2xl"
          >
            <div className="h-16 flex items-center justify-between px-4 border-b border-border/50">
              <h2 className="font-medium text-text-primary text-sm uppercase tracking-wider">History</h2>
              <button onClick={onClose} className="p-2 hover:bg-surface-soft rounded-full text-text-secondary hover:text-text-primary transition-colors">
                <X size={18} />
              </button>
            </div>
            
            <div className="p-4">
              <button 
                onClick={() => { onNewChat(); onClose(); }}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-accent-primary/10 hover:bg-accent-primary/20 text-accent-primary rounded-lg font-medium transition-colors border border-accent-primary/20"
              >
                <Plus size={18} />
                <span>New Conversation</span>
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-1 hide-scrollbar">
              {conversations.length === 0 ? (
                <div className="text-center text-text-secondary text-sm p-4 mt-10 opacity-60">
                  No previous conversations
                </div>
              ) : (
                conversations.map((conv) => (
                  <div 
                    key={conv.id}
                    className={`group flex items-center justify-between px-3 py-3 rounded-lg cursor-pointer transition-colors ${
                      activeConversation?.id === conv.id 
                        ? "bg-surface-soft/80 border border-border/50" 
                        : "hover:bg-surface-soft/40 border border-transparent"
                    }`}
                  >
                    <div 
                      className="flex-1 flex items-center gap-3 overflow-hidden"
                      onClick={() => { onSelect(conv); onClose(); }}
                    >
                      <MessageSquare size={16} className={activeConversation?.id === conv.id ? "text-accent-primary" : "text-text-secondary"} />
                      <div className="flex flex-col overflow-hidden">
                        <span className={`text-sm truncate ${activeConversation?.id === conv.id ? "text-text-primary font-medium" : "text-text-secondary"}`}>
                          {conv.title || "New Chat"}
                        </span>
                        <span className="text-[10px] text-text-secondary/60 mt-0.5">
                          {new Date(conv.updated_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <button 
                      onClick={(e) => { e.stopPropagation(); onDelete(conv.id); }}
                      className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-500/10 text-red-400 rounded transition-all"
                      title="Delete"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
