import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileText,
  Loader2,
  CheckCircle2,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  RotateCw,
  X,
  Sparkles,
  HelpCircle,
  ListFilter,
  BookOpen,
} from "lucide-react";

export const DocumentAttachmentCard = ({
  document,
  onRetry,
  onDetach,
  onPromptClick,
  isGenerating,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!document) return null;

  const {
    original_filename,
    file_size,
    processing_status = "uploaded",
    processing_error,
    extracted_text,
  } = document;

  const formatFileSize = (bytes) => {
    if (!bytes && bytes !== 0) return "";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const isProcessing =
    processing_status === "uploaded" || processing_status === "processing";
  const isReady = processing_status === "ready";
  const isFailed = processing_status === "failed";

  const promptSuggestions = [
    { label: "Summarize this PDF", icon: BookOpen },
    { label: "Explain in simple English", icon: HelpCircle },
    { label: "Find the important points", icon: ListFilter },
    { label: "Explain chapter 2", icon: Sparkles },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.96 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="w-full max-w-3xl mx-auto mb-6 bg-surface rounded-2xl border border-border shadow-soft overflow-hidden transition-all"
    >
      {/* Top Header Card */}
      <div className="p-4 sm:p-5 flex items-start justify-between gap-3 bg-gradient-to-r from-surface to-surface-soft/40 border-b border-border/40">
        <div className="flex items-start gap-3.5 min-w-0">
          <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-red-500 to-rose-600 flex items-center justify-center text-white font-bold text-xs shadow-sm shrink-0">
            PDF
          </div>

          <div className="flex flex-col min-w-0">
            <h3
              className="text-sm sm:text-base font-semibold text-text-primary truncate"
              title={original_filename}
            >
              {original_filename}
            </h3>

            <div className="flex flex-wrap items-center gap-2 mt-1">
              <span className="text-xs text-text-muted">
                {formatFileSize(file_size)}
              </span>

              <span className="text-text-muted/40 text-xs">•</span>

              {isProcessing && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-700 border border-amber-500/20">
                  <Loader2 size={12} className="animate-spin text-amber-600" />
                  <span>Processing document...</span>
                </span>
              )}

              {isReady && (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-700 border border-emerald-500/20">
                  <CheckCircle2 size={12} className="text-emerald-600" />
                  <span>Ready for analysis</span>
                </span>
              )}

              {isFailed && (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-700 border border-rose-500/20">
                  <AlertCircle size={12} className="text-rose-600" />
                  <span>Processing failed</span>
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          {isFailed && onRetry && (
            <button
              onClick={onRetry}
              className="p-1.5 text-text-secondary hover:text-accent-primary hover:bg-surface-soft rounded-lg transition-colors flex items-center gap-1 text-xs font-medium border border-border"
              title="Retry Processing"
            >
              <RotateCw size={14} />
              <span className="hidden sm:inline">Retry</span>
            </button>
          )}

          {onDetach && (
            <button
              onClick={onDetach}
              className="p-1.5 text-text-muted hover:text-text-primary hover:bg-surface-soft rounded-lg transition-colors"
              title="Remove attachment"
            >
              <X size={16} />
            </button>
          )}
        </div>
      </div>

      {/* Processing State Bar */}
      {isProcessing && (
        <div className="px-4 py-3 sm:px-5 bg-amber-50/50 border-b border-amber-100 flex items-center gap-2.5 text-xs text-amber-800">
          <Loader2 size={14} className="animate-spin text-amber-600 shrink-0" />
          <span>
            Extracting text and indexing with pgvector RAG pipeline. This will
            only take a moment...
          </span>
        </div>
      )}

      {/* Error Callout */}
      {isFailed && (
        <div className="px-4 py-3 sm:px-5 bg-rose-50/80 border-b border-rose-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 text-xs text-rose-800">
          <div className="flex items-start gap-2">
            <AlertCircle size={16} className="text-rose-600 shrink-0 mt-0.5" />
            <span>
              {processing_error ||
                "Failed to extract readable text. The PDF might be image-only, password-protected, or corrupted."}
            </span>
          </div>
          {onRetry && (
            <button
              onClick={onRetry}
              className="self-start sm:self-auto px-3 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-medium transition-colors shrink-0 flex items-center gap-1"
            >
              <RotateCw size={12} />
              <span>Retry Extraction</span>
            </button>
          )}
        </div>
      )}

      {/* Extracted Text Preview Section */}
      {isReady && extracted_text && (
        <div className="p-4 sm:p-5 border-b border-border/40">
          <div className="flex items-center justify-between gap-2 mb-2">
            <div className="flex items-center gap-2">
              <FileText size={15} className="text-accent-primary" />
              <span className="text-xs font-semibold text-text-primary uppercase tracking-wider">
                Extracted Text Preview
              </span>
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-surface-soft text-text-muted font-medium">
                {extracted_text.length.toLocaleString()} characters
              </span>
            </div>

            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="inline-flex items-center gap-1 text-xs font-medium text-accent-primary hover:text-accent-hover transition-colors py-1 px-2 rounded-md hover:bg-accent-soft/30"
            >
              <span>{isExpanded ? "Collapse preview" : "Expand preview"}</span>
              {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>
          </div>

          <AnimatePresence initial={false}>
            {isExpanded ? (
              <motion.div
                key="expanded"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.25 }}
                className="overflow-hidden"
              >
                <div className="mt-2 p-3.5 bg-surface-soft/60 rounded-xl border border-border/50 max-h-60 sm:max-h-72 overflow-y-auto text-xs sm:text-sm text-text-secondary font-mono leading-relaxed whitespace-pre-wrap select-text">
                  {extracted_text}
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="collapsed"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="mt-2 text-xs text-text-secondary leading-relaxed bg-surface-soft/30 p-2.5 rounded-xl border border-border/30 line-clamp-2 select-text"
              >
                {extracted_text.slice(0, 240)}
                {extracted_text.length > 240 ? "..." : ""}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Suggested Conversational Questions */}
      {isReady && onPromptClick && (
        <div className="px-4 py-3 sm:px-5 bg-surface-soft/20 flex flex-col gap-2">
          <div className="flex items-center gap-1.5 text-[11px] font-medium text-text-muted uppercase tracking-wider">
            <Sparkles size={13} className="text-accent-primary" />
            <span>Suggested Questions</span>
          </div>

          <div className="flex flex-wrap gap-2">
            {promptSuggestions.map((item, idx) => {
              const Icon = item.icon;
              return (
                <button
                  key={idx}
                  disabled={isGenerating}
                  onClick={() => onPromptClick(item.label)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-surface hover:bg-surface-soft text-text-primary border border-border/70 hover:border-accent-primary/40 shadow-xs transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none group"
                >
                  <Icon
                    size={13}
                    className="text-text-muted group-hover:text-accent-primary transition-colors"
                  />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </motion.div>
  );
};
