import { motion } from "framer-motion";
import robotImg from "../../assets/roboat.png";

export const AIAvatar = ({ state = "idle", size = "large" }) => {
  const sizeClasses = {
    small: "w-16 h-16",
    medium: "w-32 h-32",
    large: "w-72 h-72",
    huge: "w-96 h-96"
  };

  const floatAnimation = {
    y: [-8, 8, -8],
    transition: {
      duration: 6,
      repeat: Infinity,
      ease: "easeInOut"
    }
  };

  return (
    <div className={`relative flex items-center justify-center ${sizeClasses[size]}`}>
      {/* Glow Effect Behind Robot */}
      <motion.div
        animate={{ scale: [1, 1.05, 1], opacity: [0.4, 0.7, 0.4] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        className="absolute inset-4 rounded-full bg-gradient-to-br from-accent-primary/30 to-accent-secondary/30 blur-2xl"
      />
      
      {/* Robot Image Container */}
      <motion.div
        animate={floatAnimation}
        className="relative w-full h-full flex items-center justify-center"
      >
        <img 
          src={robotImg} 
          alt="AI Robot" 
          className="w-full h-full object-contain drop-shadow-2xl mix-blend-multiply"
        />
      </motion.div>
    </div>
  );
};
