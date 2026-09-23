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
import { getGreetingText } from "../utils/greeting";
import { speak } from "../utils/speech";

import { useChatStore } from "../store/chatStore";
import { Sidebar } from "../components/chat/Sidebar";

export default function Workspace() {
  const [showSidebar, setShowSidebar] = useState(false);
  const scrollRef = useRef(null);
  
  const currentUser = useAuthStore((state) => state.currentUser);
  const hasSpokenGreeting = useAuthStore((state) => state.hasSpokenGreeting);
  const setHasSpokenGreeting = useAuthStore((state) => state.setHasSpokenGreeting);
  const navigate = useNavigate();
  const hasSpokenLocal = useRef(false);

  const { 
    conversations, 
    activeConversation, 
    messages, 
    isGenerating, 
    fetchConversations, 
    createConversation, 
    selectConversation, 
    sendMessage, 
    deleteConversation,
    stopGenerating
  } = useChatStore();

  const hasSpokenGreeting = useAuthStore((state) => state.hasSpokenGreeting);
  const setHasSpokenGreeting = useAuthStore((state) => state.setHasSpokenGreeting);

  useEffect(() => {
    if (!currentUser) {
      navigate("/auth", { replace: true });
    } else {
      fetchConversations();
    }
  }, [currentUser, navigate, fetchConversations]);

  useEffect(() => {
    if (!currentUser) return;

    if (hasSpokenGreeting || hasSpokenLocal.current) {
      return;
    }

    let isMounted = true;
    const timer = setTimeout(() => {
      if (!isMounted) return;
      hasSpokenLocal.current = true;
      setHasSpokenGreeting(true);
      speak(getGreetingText(currentUser.name));
    }, 800);

    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, [currentUser, hasSpokenGreeting, setHasSpokenGreeting]);

  useEffect(() => {
    if (!currentUser) return;
    if (hasSpokenGreeting) return;

    if (window.speechSynthesis && window.SpeechSynthesisUtterance) {
      setHasSpokenGreeting(true);
      const text = `Hi ${currentUser.name}, how can I help you?`;

      // Cancel any stale speech before playing the new one
      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "en-US";
      utterance.rate = 1;
      utterance.pitch = 1;
      utterance.volume = 1;

      window.speechSynthesis.speak(utterance);
    }
    // We intentionally do NOT place speechSynthesis.cancel() in the cleanup function here.
    // This allows the speech to survive React 18 StrictMode's instant unmount/remount cycle.
    // Legitimate speech cancellation during navigation is handled by the logout() action in authStore.js.
  }, [currentUser, hasSpokenGreeting, setHasSpokenGreeting]);

  if (!currentUser) return null;

  const getGreeting = () => getGreetingText(currentUser.name);

  const handleSend = async (text) => {
    await sendMessage(text);
  };

  const handleStop = () => {
    stopGenerating();
  };

  useEffect(() => {
    if (scrollRef.current) {
      const { scrollHeight, clientHeight, scrollTop } = scrollRef.current;
      const isNearBottom = scrollHeight - clientHeight - scrollTop < 150;
      
      if (isNearBottom || !isGenerating) {
        scrollRef.current.scrollTo({
          top: scrollRef.current.scrollHeight,
          behavior: isGenerating ? "auto" : "smooth"
        });
      }
    }
  }, [messages, isGenerating]);

  const isChatActive = activeConversation !== null || messages.length > 0;

  return (
    <div className="relative h-screen bg-canvas flex flex-col overflow-hidden">
      <Sidebar 
        isOpen={showSidebar}
        onClose={() => setShowSidebar(false)}
        conversations={conversations}
        activeConversation={activeConversation}
        onSelect={selectConversation}
        onNewChat={createConversation}
        onDelete={deleteConversation}
      />

      <Header onToggleHistory={() => setShowSidebar(true)} />

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
              className="flex-1 overflow-y-auto w-full relative z-10 scroll-smooth hide-scrollbar pb-32 pt-20"
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
