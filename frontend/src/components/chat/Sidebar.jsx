import { motion, AnimatePresence } from "framer-motion";
import { X, MessageSquare, Plus, Trash2, Edit2, FileText, UploadCloud, Loader2 } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { useChatStore } from "../../store/chatStore";
import { useDocumentStore } from "../../store/documentStore";

export const Sidebar = ({ 
  isOpen, 
  onClose, 
  conversations, 
  activeConversation, 
  onSelect, 
  onNewChat, 
  onDelete 
}) => {
  const [deleteId, setDeleteId] = useState(null);
  const [renameId, setRenameId] = useState(null);
  const [renameValue, setRenameValue] = useState("");
  const renameConversation = useChatStore(state => state.renameConversation);

  const { documents, isLoadingDocuments, isUploading, fetchDocuments, uploadDocument, deleteDocument } = useDocumentStore();
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      fetchDocuments();
    }
  }, [isOpen, fetchDocuments]);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await uploadDocument(file);
    } catch (err) {
      alert(err.message);
    }
    e.target.value = '';
  };

  const handleRenameSubmit = async (e, id) => {
    e.preventDefault();
    e.stopPropagation();
    if (!renameValue.trim()) {
      setRenameId(null);
      return;
    }
    try {
      await renameConversation(id, renameValue.trim());
    } catch (err) {
      console.error("Rename failed", err);
    }
    setRenameId(null);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop (mobile only) */}
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
          />
          
          {/* Sidebar */}
          <motion.div 
            initial={{ marginLeft: -320 }}
            animate={{ marginLeft: 0 }}
            exit={{ marginLeft: -320 }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed lg:relative inset-y-0 left-0 z-50 w-80 bg-surface border-r border-border/50 flex flex-col shadow-2xl lg:shadow-none shrink-0 overflow-hidden"
          >
            {/* Inner fixed width container to prevent squeezing during animation */}
            <div className="w-80 h-full flex flex-col min-w-[320px]">
              <div className="h-16 flex items-center justify-between px-4 border-b border-border/50 shrink-0">
                <h2 className="font-medium text-text-primary text-sm uppercase tracking-wider">History</h2>
                <button onClick={onClose} className="p-2 hover:bg-surface-soft rounded-full text-text-secondary hover:text-text-primary transition-colors lg:hidden">
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
                    onClick={() => { 
                      if (renameId === conv.id || deleteId === conv.id) return;
                      onSelect(conv); 
                      onClose(); 
                    }}
                  >
                    {deleteId === conv.id ? (
                      <div className="flex-1 flex items-center justify-between gap-2 overflow-hidden">
                        <span className="text-sm font-medium text-red-500 truncate">Delete chat?</span>
                        <div className="flex gap-1 shrink-0">
                          <button 
                            onClick={(e) => { e.stopPropagation(); onDelete(conv.id); setDeleteId(null); }}
                            className="text-xs bg-red-500 text-white px-2 py-1 rounded hover:bg-red-600 transition-colors"
                          >
                            Yes
                          </button>
                          <button 
                            onClick={(e) => { e.stopPropagation(); setDeleteId(null); }}
                            className="text-xs bg-surface-soft text-text-secondary px-2 py-1 rounded hover:bg-surface hover:text-text-primary border transition-colors"
                          >
                            No
                          </button>
                        </div>
                      </div>
                    ) : renameId === conv.id ? (
                      <form 
                        className="flex-1 flex items-center gap-2 overflow-hidden"
                        onSubmit={(e) => handleRenameSubmit(e, conv.id)}
                      >
                        <MessageSquare size={16} className="text-accent-primary shrink-0" />
                        <input
                          autoFocus
                          type="text"
                          value={renameValue}
                          onChange={(e) => setRenameValue(e.target.value)}
                          onClick={(e) => e.stopPropagation()}
                          onBlur={(e) => handleRenameSubmit(e, conv.id)}
                          className="flex-1 text-sm bg-surface px-2 py-0.5 rounded border border-accent-primary/50 outline-none text-text-primary min-w-0"
                        />
                      </form>
                    ) : (
                      <>
                        <div className="flex-1 flex items-center gap-3 overflow-hidden">
                          <MessageSquare size={16} className={activeConversation?.id === conv.id ? "text-accent-primary" : "text-text-secondary"} shrink-0 />
                          <div className="flex flex-col overflow-hidden w-full">
                            <span className={`text-sm truncate ${activeConversation?.id === conv.id ? "text-text-primary font-medium" : "text-text-secondary"}`}>
                              {conv.title || "New Chat"}
                            </span>
                            <span className="text-[10px] text-text-secondary/60 mt-0.5 truncate">
                              {new Date(conv.updated_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                        <div className="opacity-0 group-hover:opacity-100 flex items-center gap-1 transition-opacity shrink-0">
                          <button 
                            onClick={(e) => { 
                              e.stopPropagation(); 
                              setRenameValue(conv.title || "New Chat");
                              setRenameId(conv.id);
                            }}
                            className="p-1.5 hover:bg-surface text-text-muted hover:text-text-primary rounded transition-all"
                            title="Rename"
                          >
                            <Edit2 size={14} />
                          </button>
                          <button 
                            onClick={(e) => { e.stopPropagation(); setDeleteId(conv.id); }}
                            className="p-1.5 hover:bg-red-500/10 text-text-muted hover:text-red-500 rounded transition-all"
                            title="Delete"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                ))
              )}
            </div>

            {/* My Documents Section */}
            <div className="h-12 flex items-center justify-between px-4 border-t border-b border-border/50 bg-surface-soft/20 mt-2">
              <h2 className="font-medium text-text-primary text-sm uppercase tracking-wider">My Documents</h2>
              <button 
                onClick={handleUploadClick}
                disabled={isUploading}
                className="p-1.5 hover:bg-surface rounded-full text-accent-primary transition-colors disabled:opacity-50"
                title="Upload Document"
              >
                {isUploading ? <Loader2 size={16} className="animate-spin" /> : <UploadCloud size={16} />}
              </button>
              <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handleFileChange} 
                className="hidden" 
                accept=".pdf,.docx,.txt"
              />
            </div>

            <div className="flex-1 overflow-y-auto px-2 py-4 space-y-1 hide-scrollbar max-h-[40%]">
              {isLoadingDocuments ? (
                <div className="flex justify-center items-center py-4">
                  <Loader2 size={20} className="animate-spin text-accent-primary" />
                </div>
              ) : documents.length === 0 ? (
                <div className="text-center text-text-secondary text-sm p-4 opacity-60">
                  No documents uploaded
                </div>
              ) : (
                documents.map(doc => (
                  <div key={doc.id} className="group flex items-center justify-between px-3 py-3 rounded-lg hover:bg-surface-soft/40 border border-transparent transition-colors">
                    <div className="flex-1 flex items-center gap-3 overflow-hidden">
                      <FileText size={16} className="text-text-secondary shrink-0" />
                      <div className="flex flex-col overflow-hidden w-full">
                        <span className="text-sm truncate text-text-primary" title={doc.original_filename}>
                          {doc.original_filename}
                        </span>
                        <span className="text-[10px] text-text-secondary/60 mt-0.5 truncate uppercase">
                          {doc.file_type} • {(doc.file_size / 1024 / 1024).toFixed(2)} MB
                        </span>
                      </div>
                    </div>
                    <div className="opacity-0 group-hover:opacity-100 flex items-center gap-1 transition-opacity shrink-0">
                      <button 
                        onClick={(e) => { e.stopPropagation(); deleteDocument(doc.id); }}
                        className="p-1.5 hover:bg-red-500/10 text-text-muted hover:text-red-500 rounded transition-all"
                        title="Delete Document"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
