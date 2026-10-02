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
    <div className="grid w-full grid-cols-2 items-center justify-center gap-x-2 gap-y-1.5 max-w-3xl mx-auto mt-2 sm:mt-6 sm:flex sm:flex-wrap sm:gap-3">
      {suggestions.map((suggestion) => (
        <button
          key={suggestion.id}
          onClick={() => onSelect(suggestion.label)}
          className="flex min-w-0 w-full items-center justify-center gap-1.5 px-1 py-1.5 bg-surface-soft border border-border rounded-full text-xs font-medium text-text-secondary hover:text-text-primary hover:border-border/80 hover:shadow-sm hover:-translate-y-0.5 active:scale-97 transition-all sm:w-auto sm:gap-2 sm:px-4 sm:py-2 sm:text-sm"
        >
          <suggestion.icon size={14} className="text-text-muted" />
          {suggestion.label}
        </button>
      ))}
    </div>
  );
};
