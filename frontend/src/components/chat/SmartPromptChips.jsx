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
    <div className="flex flex-wrap items-center justify-center gap-3 max-w-3xl mx-auto mt-6">
      {suggestions.map((suggestion) => (
        <button
          key={suggestion.id}
          onClick={() => onSelect(suggestion.label)}
          className="flex items-center gap-2 px-4 py-2 bg-surface-soft border border-border rounded-full text-sm font-medium text-text-secondary hover:text-text-primary hover:border-border/80 hover:shadow-sm hover:-translate-y-0.5 active:scale-97 transition-all"
        >
          <suggestion.icon size={14} className="text-text-muted" />
          {suggestion.label}
        </button>
      ))}
    </div>
  );
};
