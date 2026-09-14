import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Header } from "../components/core/Header";
import { AIAvatar } from "../components/core/AIAvatar";
import { AnimatedBackground } from "../components/core/AnimatedBackground";
import { MainComposer } from "../components/chat/MainComposer";
import { SmartPromptChips } from "../components/chat/SmartPromptChips";
import { MessageList } from "../components/chat/MessageList";
import { useAuthStore } from "../store/authStore";
import { useNavigate } from "react-router-dom";

export default function Workspace() {
  const [messages, setMessages] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const scrollRef = useRef(null);
  const currentUser = useAuthStore((state) => state.currentUser);
  const navigate = useNavigate();

  useEffect(() => {
    if (!currentUser) {
      navigate("/auth", { replace: true });
    }
  }, [currentUser, navigate]);

  if (!currentUser) return null;

  const getGreeting = () => {
    const hour = new Date().getHours();
    let timeOfDay = "Good evening";
    if (hour < 12) timeOfDay = "Good morning";
    else if (hour < 18) timeOfDay = "Good afternoon";
    
    return `Hi ${currentUser.name}, how can I help you?`;
  };

  const handleSend = (text) => {
    setMessages(prev => [...prev, { id: Date.now(), role: "user", content: text }]);
    setIsGenerating(true);
    
    // Simulate AI response
    setTimeout(() => {
      setIsGenerating(false);
      setMessages(prev => [...prev, { 
        id: Date.now() + 1, 
        role: "assistant", 
        content: "This is a simulated response. The UI has transitioned smoothly into the chat workspace, presenting a clean and spacious reading experience. The AI Orb provides a calm ambient presence, and micro-interactions make the interface feel alive." 
      }]);
    }, 2500);
  };

  const handleStop = () => {
    setIsGenerating(false);
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth"
      });
    }
  }, [messages, isGenerating]);

  const isChatActive = messages.length > 0;

  return (
    <div className="relative h-screen bg-canvas flex flex-col overflow-hidden">
      <Header />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative w-full h-full overflow-hidden">
        <AnimatedBackground />
        
        {/* Empty State / Hero */}
        <AnimatePresence>
          {!isChatActive && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0, scale: 0.95, filter: "blur(10px)", y: -40 }}
              transition={{ duration: 0.6, ease: [0.32, 0.72, 0, 1] }}
              className="absolute inset-0 flex flex-col items-center justify-center px-4 z-0 pointer-events-none pb-[25vh]"
            >
              <motion.div layoutId="hero-orb" className="mb-10">
                <AIAvatar size="large" state="idle" />
              </motion.div>
              
              <motion.div layoutId="hero-text" className="text-center mb-16">
                <h1 className="text-[2.25rem] leading-[1.2] md:text-5xl font-medium text-text-primary mb-4 tracking-tight">
                  {getGreeting()}
                </h1>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Chat Interface */}
        <AnimatePresence>
          {isChatActive && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3, duration: 0.5 }}
              className="flex-1 overflow-y-auto w-full relative z-10 scroll-smooth hide-scrollbar"
              ref={scrollRef}
            >
              <MessageList messages={messages} isGenerating={isGenerating} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Composer Area */}
        <motion.div 
          layout
          initial={false}
          animate={{
            bottom: isChatActive ? "32px" : "12%",
          }}
          transition={{ duration: 0.7, ease: [0.32, 0.72, 0, 1] }}
          className="absolute inset-x-0 px-4 z-20 flex flex-col items-center pointer-events-auto"
        >
          <div className="w-full max-w-3xl flex flex-col items-center gap-6">
            <MainComposer 
              onSend={handleSend} 
              isGenerating={isGenerating} 
              onStop={handleStop}
            />
            
            <AnimatePresence>
              {!isChatActive && (
                <motion.div
                  initial={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0, marginTop: 0 }}
                  transition={{ duration: 0.4 }}
                  className="overflow-hidden w-full"
                >
                  <SmartPromptChips onSelect={handleSend} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>

      </main>
    </div>
  );
}
