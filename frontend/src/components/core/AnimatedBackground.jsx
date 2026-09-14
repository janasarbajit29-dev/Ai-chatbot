import { motion } from "framer-motion";

export const AnimatedBackground = () => {
  return (
    <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none bg-canvas">
      
      {/* Soft floating gradients */}
      <motion.div
        animate={{
          x: [0, 40, -20, 0],
          y: [0, -50, 30, 0],
          scale: [1, 1.1, 0.9, 1],
        }}
        transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
        className="absolute top-[10%] left-[15%] w-[45vw] h-[45vw] max-w-[600px] max-h-[600px] bg-accent-primary/5 rounded-full mix-blend-multiply filter blur-[100px]"
      />
      <motion.div
        animate={{
          x: [0, -50, 40, 0],
          y: [0, 40, -40, 0],
          scale: [1, 1.2, 0.8, 1],
        }}
        transition={{ duration: 25, repeat: Infinity, ease: "easeInOut" }}
        className="absolute bottom-[10%] right-[15%] w-[40vw] h-[40vw] max-w-[550px] max-h-[550px] bg-indigo-400/5 rounded-full mix-blend-multiply filter blur-[100px]"
      />
      
      {/* Subtle bottom gradient to blend with the canvas */}
      <div className="absolute inset-0 bg-gradient-to-t from-canvas via-canvas/50 to-transparent opacity-80"></div>
    </div>
  );
};
