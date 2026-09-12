import { motion } from "framer-motion";
import { FileText, Code, PenTool, LayoutTemplate, BrainCircuit, Globe } from "lucide-react";

const suggestions = [
  { id: 1, label: "Analyze a document", icon: FileText },
  { id: 2, label: "Build a project", icon: LayoutTemplate },
  { id: 3, label: "Explain something", icon: BrainCircuit },
  { id: 4, label: "Write code", icon: Code },
  { id: 5, label: "Research a topic", icon: Globe },
  { id: 6, label: "Create a plan", icon: PenTool }
];

export const SmartPromptChips = ({ onSelect }) => {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2, duration: 0.5 }}
      className="flex flex-wrap items-center justify-center gap-3 max-w-3xl mx-auto mt-6"
    >
      {suggestions.map((suggestion, idx) => (
        <motion.button
          key={suggestion.id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 + (idx * 0.05), duration: 0.4 }}
          whileHover={{ y: -2, backgroundColor: "#FFFFFF" }}
          whileTap={{ scale: 0.97 }}
          onClick={() => onSelect(suggestion.label)}
          className="flex items-center gap-2 px-4 py-2 bg-surface-soft border border-border rounded-full text-sm font-medium text-text-secondary hover:text-text-primary hover:border-border/80 hover:shadow-sm transition-colors"
        >
          <suggestion.icon size={14} className="text-text-muted" />
          {suggestion.label}
        </motion.button>
      ))}
    </motion.div>
  );
};
