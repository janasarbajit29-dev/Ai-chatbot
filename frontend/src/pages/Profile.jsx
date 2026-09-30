import { motion } from "framer-motion";
import { useAuthStore } from "../store/authStore";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, User, Mail, Activity, LogOut } from "lucide-react";

export default function Profile() {
  const currentUser = useAuthStore((state) => state.currentUser);
  const logout = useAuthStore((state) => state.logout);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/auth");
  };

  // If there's no user, we could redirect or show empty.
  // We'll rely on the app's routing or just show empty state if missing.
  if (!currentUser) {
    return null; 
  }

  return (
    <div 
      className="min-h-screen text-text-primary flex flex-col relative overflow-hidden"
      style={{ background: 'linear-gradient(135deg, #EEF2FF, #E0E7FF)' }}
    >
      {/* Simple Header */}
      <header className="h-16 flex items-center px-4 md:px-8 border-b border-white/5 bg-[#252A5A]">
        <button 
          onClick={() => navigate("/")}
          className="flex items-center gap-2 text-[#DCE3FF] hover:text-[#F8FAFC] transition-colors"
        >
          <ArrowLeft size={20} />
          <span className="font-medium text-sm">Back to Workspace</span>
        </button>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center p-4 relative z-10">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="w-full max-w-md bg-surface border border-white/10 rounded-2xl p-8 shadow-2xl backdrop-blur-sm relative overflow-hidden"
        >
          {/* Decorative background glow */}
          <div className="absolute -top-24 -right-24 w-48 h-48 bg-accent-primary/20 blur-3xl rounded-full pointer-events-none"></div>

          <div className="flex flex-col items-center mb-8 relative z-10">
            <div className="w-20 h-20 bg-accent-primary/10 rounded-full flex items-center justify-center mb-4 border border-accent-primary/20">
              <User size={32} className="text-accent-primary" />
            </div>
            <h1 className="text-2xl font-semibold tracking-tight text-[#1F2937]">
              {currentUser.name}
            </h1>
            <p className="text-[#64748B] mt-1 text-sm">
              Your Profile
            </p>
          </div>

          <div className="space-y-6 relative z-10">
            {/* Info Row: Name */}
            <div className="flex items-center gap-4 bg-black/5 p-4 rounded-xl border border-black/5">
              <div className="bg-black/10 p-2 rounded-lg">
                <User size={18} className="text-[#64748B]" />
              </div>
              <div>
                <p className="text-xs text-[#64748B] mb-0.5">Full Name</p>
                <p className="text-sm font-medium text-[#1E293B]">{currentUser.name}</p>
              </div>
            </div>

            {/* Info Row: Email */}
            <div className="flex items-center gap-4 bg-black/5 p-4 rounded-xl border border-black/5">
              <div className="bg-black/10 p-2 rounded-lg">
                <Mail size={18} className="text-[#64748B]" />
              </div>
              <div>
                <p className="text-xs text-[#64748B] mb-0.5">Email Address</p>
                <p className="text-sm font-medium text-[#1E293B]">{currentUser.email}</p>
              </div>
            </div>

            {/* Info Row: Status */}
            <div className="flex items-center gap-4 bg-black/5 p-4 rounded-xl border border-black/5">
              <div className="bg-green-500/20 p-2 rounded-lg">
                <Activity size={18} className="text-green-500" />
              </div>
              <div>
                <p className="text-xs text-[#64748B] mb-0.5">Account Status</p>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                  <p className="text-sm font-medium text-[#1E293B]">Active</p>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-10 relative z-10">
            <button 
              onClick={handleLogout}
              className="w-full flex items-center justify-center gap-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 p-3 rounded-xl transition-all duration-200 border border-red-500/20 font-medium active:scale-[0.98]"
            >
              <LogOut size={18} />
              <span>Logout</span>
            </button>
          </div>
        </motion.div>
      </main>
    </div>
  );
}
