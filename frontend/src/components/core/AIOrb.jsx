import { motion } from "framer-motion";

export const AIOrb = ({ state = "idle", size = "large" }) => {
  // states: idle, thinking, generating, voice, error, success
  
  const sizeClasses = {
    small: "w-6 h-6",
    medium: "w-12 h-12",
    large: "w-24 h-24",
    huge: "w-40 h-40"
  };

  const animations = {
    idle: {
      scale: [1, 1.03, 1],
      rotate: [0, 5, -2, 0],
      transition: { duration: 8, repeat: Infinity, ease: "easeInOut" }
    },
    thinking: {
      scale: [1, 1.15, 1],
      rotate: [0, 45, 90, 0],
      borderRadius: ["50%", "45%", "50%", "48%", "50%"],
      boxShadow: [
        "0px 0px 20px rgba(109, 99, 246, 0.1)", 
        "0px 0px 50px rgba(109, 99, 246, 0.4)", 
        "0px 0px 20px rgba(109, 99, 246, 0.1)"
      ],
      transition: { duration: 2.5, repeat: Infinity, ease: "easeInOut" }
    },
    generating: {
      scale: [1, 1.05, 1],
      rotate: [0, 360],
      borderRadius: ["50%", "40%", "48%", "42%", "50%"],
      transition: { duration: 4, repeat: Infinity, ease: "linear" }
    },
    typing: {
      scale: [1, 1.02, 1],
      rotate: [0, 2, -2, 0],
      transition: { duration: 2, repeat: Infinity, ease: "easeInOut" }
    }
  };

  return (
    <div className={`relative flex items-center justify-center ${sizeClasses[size]}`}>
      {/* Outer Glow */}
      <motion.div
        animate={animations[state] || animations.idle}
        className="absolute inset-0 rounded-full bg-gradient-to-br from-accent-soft via-accent-primary to-accent-secondary opacity-60 blur-xl"
      />
      {/* Glass Shell */}
      <motion.div
        animate={animations[state] || animations.idle}
        className="absolute inset-1 rounded-full bg-gradient-to-tr from-white/60 to-white/10 backdrop-blur-2xl border border-white/60 shadow-inner"
      />
      {/* Inner Core */}
      <motion.div 
        animate={{ scale: [1, 1.3, 1], opacity: [0.4, 0.7, 0.4] }}
        transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
        className="absolute w-1/2 h-1/2 rounded-full bg-white blur-md"
      />
    </div>
  );
};
