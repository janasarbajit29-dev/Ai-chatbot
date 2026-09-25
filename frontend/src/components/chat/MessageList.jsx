import { motion, AnimatePresence } from "framer-motion";
import { Copy, ThumbsUp, ThumbsDown, RotateCcw, MoreHorizontal } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { AIOrb } from "../core/AIOrb";
import { useChatStore } from "../../store/chatStore";

export const MessageList = ({ messages, isGenerating }) => {
  const sendMessage = useChatStore((state) => state.sendMessage);

  return (
    <div className="w-full max-w-4xl mx-auto pb-32 pt-24 px-4 flex flex-col gap-8">
      <AnimatePresence initial={false}>
        {messages.map((msg, index) => (
          <MessageBubble
            key={msg.id || index}
            message={msg}
            isLast={index === messages.length - 1}
            onRegenerate={(id) => sendMessage(null, id)}
          />
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

const MessageBubble = ({ message, isLast, onRegenerate }) => {
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
        className={`relative group ${isUser
            ? "bg-surface border border-border px-5 py-3.5 rounded-2xl rounded-tr-sm shadow-soft text-text-primary max-w-[85%]"
            : "text-text-primary leading-relaxed text-[16px] w-full pl-11"
          }`}
      >
        <div className="prose prose-slate max-w-none prose-p:leading-relaxed prose-pre:p-0 prose-pre:bg-transparent">
          {isUser ? (
            <div className="whitespace-pre-wrap">{message.content}</div>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                pre: ({ node, children, ...props }) => (
                  <div className="not-prose relative rounded-xl overflow-hidden my-4 border border-border bg-[#1E293B] shadow-sm">
                    <div className="flex items-center justify-between px-4 py-2 bg-slate-800/50 border-b border-slate-700">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
                        <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
                        <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
                      </div>
                      <span className="text-xs font-medium text-slate-400">Code</span>
                    </div>
                    <div className="p-4 overflow-x-auto text-sm font-mono text-slate-50">
                      <pre {...props}>{children}</pre>
                    </div>
                  </div>
                ),
                code: ({ node, className, children, ...props }) => {
                  const match = /language-(\w+)/.exec(className || "");
                  if (match) {
                    return (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  }
                  return (
                    <code
                      className="bg-accent-soft px-1.5 py-0.5 rounded-md text-[13px] font-mono border border-accent-primary/20 text-accent-primary"
                      {...props}
                    >
                      {children}
                    </code>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {message.isError && !isUser && (
          <div className="mt-3 flex items-center gap-3 text-red-500 bg-red-50 px-3 py-2 rounded-lg text-sm border border-red-100">
            <span>Generation failed.</span>
            <button
              onClick={() => onRegenerate(message.id)}
              className="font-medium hover:underline text-red-600"
            >
              Retry
            </button>
          </div>
        )}

        {message.sources && message.sources.length > 0 && (
          <div className="mt-4 pt-3 border-t border-border/50">
            <div className="text-[11px] font-semibold text-text-muted uppercase tracking-wider mb-2">Sources</div>
            <div className="flex flex-wrap gap-2">
              {message.sources.map((src, i) => (
                <div key={i} className="flex items-center gap-1.5 px-2 py-1 bg-surface-hover rounded border border-border/60 text-xs text-text-secondary">
                  <span className="text-[10px]">📄</span>
                  <span className="truncate max-w-[200px]">{src.filename}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {!isUser && !message.isError && (
          <div className="absolute -left-2 -bottom-10 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center gap-1 pl-12 pt-2">
            <ActionButton
              icon={<Copy size={16} />}
              onClick={() => navigator.clipboard.writeText(message.content)}
              title="Copy response"
            />
            {isLast && (
              <ActionButton
                icon={<RotateCcw size={16} />}
                onClick={() => onRegenerate(message.id)}
                title="Regenerate response"
              />
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
};

const ActionButton = ({ icon, onClick, title }) => (
  <button
    onClick={onClick}
    title={title}
    className="p-1.5 text-text-muted hover:text-text-primary hover:bg-surface rounded-md transition-colors"
  >
    {icon}
  </button>
);
