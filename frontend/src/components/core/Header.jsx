import { motion } from "framer-motion";
import { Menu, User } from "lucide-react";
import { AIOrb } from "./AIOrb";
import { useNavigate } from "react-router-dom";

export const Header = ({ onToggleSidebar, isOpen }) => {
  const navigate = useNavigate();

  return (
    <motion.header 
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="absolute top-0 inset-x-0 h-16 z-40 bg-[#252A5A] border-b border-[#3A4075] px-4 md:px-8 flex items-center justify-between"
    >
      {/* Left: Hamburger & Logo */}
      <div className="flex items-center gap-3">
        <button 
          onClick={onToggleSidebar}
          aria-label={isOpen ? "Close sidebar" : "Open sidebar"}
          className="p-2 -ml-2 text-[#DCE3FF] hover:text-[#F8FAFC] hover:bg-white/10 rounded-full transition-colors active:scale-95"
        >
          <Menu size={20} />
        </button>
        <AIOrb size="small" state="idle" />
        <span className="font-medium text-[#F8FAFC] tracking-widest text-sm uppercase">Aura</span>
      </div>

      {/* Center: Workspace Indicator */}
      <div className="hidden md:flex items-center gap-2 bg-white/5 rounded-full px-3 py-1 border border-white/10">
        <div className="w-1.5 h-1.5 rounded-full bg-[#DCE3FF] animate-pulse"></div>
        <span className="text-xs font-medium text-[#F8FAFC]">Personal Workspace</span>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-1 md:gap-2">
        <HeaderButton icon={<User size={18} />} onClick={() => navigate("/profile")} />
      </div>
    </motion.header>
  );
};

const HeaderButton = ({ icon, onClick }) => (
  <button 
    onClick={onClick}
    className="p-2.5 text-[#DCE3FF] hover:text-[#F8FAFC] hover:bg-white/10 rounded-full transition-all duration-200 hover:shadow-sm hover:-translate-y-0.5 active:scale-95"
  >
    {icon}
  </button>
);
