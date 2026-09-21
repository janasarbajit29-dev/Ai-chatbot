import { motion } from "framer-motion";
import { History, Search, Settings, User, LogOut } from "lucide-react";
import { AIOrb } from "./AIOrb";
import { useAuthStore } from "../../store/authStore";
import { useNavigate } from "react-router-dom";

export const Header = () => {
  const logout = useAuthStore((state) => state.logout);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/auth");
  };

  return (
    <motion.header 
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="fixed top-0 inset-x-0 h-16 z-50 bg-canvas/60 backdrop-blur-xl border-b border-white/40 px-4 md:px-8 flex items-center justify-between"
    >
      {/* Left: Logo */}
      <div className="flex items-center gap-3">
        <AIOrb size="small" state="idle" />
        <span className="font-medium text-text-primary tracking-widest text-sm uppercase">Aura</span>
      </div>

      {/* Center: Workspace Indicator */}
      <div className="hidden md:flex items-center gap-2 bg-surface-soft/50 rounded-full px-3 py-1 border border-border/50">
        <div className="w-1.5 h-1.5 rounded-full bg-accent-primary animate-pulse"></div>
        <span className="text-xs font-medium text-text-secondary">Personal Workspace</span>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-1 md:gap-2">
        <HeaderButton icon={<History size={18} />} onClick={onToggleHistory} title="History" />
        <HeaderButton icon={<Search size={18} />} title="Search" />
        <HeaderButton icon={<Settings size={18} />} title="Settings" />
        <div className="hidden md:block w-px h-4 bg-border mx-1"></div>
        <HeaderButton icon={<User size={18} />} />
        <HeaderButton icon={<LogOut size={18} />} onClick={handleLogout} />
      </div>
    </motion.header>
  );
};

const HeaderButton = ({ icon, onClick }) => (
  <button 
    onClick={onClick}
    className="p-2.5 text-text-secondary hover:text-text-primary hover:bg-surface rounded-full transition-all duration-200 hover:shadow-sm hover:-translate-y-0.5 active:scale-95"
  >
    {icon}
  </button>
);
