import { motion } from "framer-motion";
import { ArrowUp, Square } from "lucide-react";

export const SendButton = ({ onClick, isGenerating, hasInput }) => {
  return (
    <motion.button
      onClick={onClick}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      initial={false}
      animate={{
        backgroundColor: isGenerating ? "#F3F5F8" : (hasInput ? "#172033" : "#F3F5F8"),
        color: isGenerating ? "#172033" : (hasInput ? "#FFFFFF" : "#98A2B3"),
        y: isGenerating ? 0 : [0, -2, 0] // floating idle if not generating
      }}
      transition={{
        y: { duration: 3, repeat: Infinity, ease: "easeInOut" },
        backgroundColor: { duration: 0.2 },
        color: { duration: 0.2 }
      }}
      className="relative p-2.5 rounded-full ml-1 overflow-hidden"
    >
      <motion.div
        initial={false}
        animate={{
          scale: isGenerating ? 0 : 1,
          opacity: isGenerating ? 0 : 1
        }}
        transition={{ duration: 0.2 }}
        className="absolute inset-0 flex items-center justify-center"
      >
        <ArrowUp size={18} strokeWidth={2.5} />
      </motion.div>

      <motion.div
        initial={false}
        animate={{
          scale: isGenerating ? 1 : 0,
          opacity: isGenerating ? 1 : 0
        }}
        transition={{ duration: 0.2 }}
        className="absolute inset-0 flex items-center justify-center"
      >
        <Square size={14} fill="currentColor" strokeWidth={0} />
      </motion.div>
      
      {/* Invisible placeholder to maintain size */}
      <div className="w-[18px] h-[18px] opacity-0" />
    </motion.button>
  );
};
