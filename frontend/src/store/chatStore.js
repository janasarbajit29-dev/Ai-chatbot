import { create } from 'zustand';

export const useChatStore = create((set) => ({
  messages: [],
  isTyping: false,
  
  addMessage: (message) => set((state) => ({ 
    messages: [...state.messages, { ...message, id: Date.now().toString() }] 
  })),
  
  setTyping: (isTyping) => set({ isTyping }),
  
  // Mock function to simulate AI response
  sendMessage: async (content) => {
    set((state) => ({ 
      messages: [...state.messages, { id: Date.now().toString(), role: 'user', content }] 
    }));
    
    set({ isTyping: true });
    
    // Simulate network delay
    setTimeout(() => {
      set((state) => ({
        isTyping: false,
        messages: [
          ...state.messages, 
          { 
            id: (Date.now() + 1).toString(), 
            role: 'assistant', 
            content: "This is a simulated AI response. The actual implementation will stream from our FastAPI backend." 
          }
        ]
      }));
    }, 1500);
  },
  
  clearMessages: () => set({ messages: [] })
}));
