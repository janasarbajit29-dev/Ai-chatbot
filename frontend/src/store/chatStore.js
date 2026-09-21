import { create } from 'zustand';
import { apiClient } from '../lib/axios';
import { getToken } from '../utils/auth';

export const useChatStore = create((set, get) => ({
  conversations: [],
  activeConversation: null,
  messages: [],
  isLoadingConversations: false,
  isLoadingMessages: false,
  isGenerating: false,
  error: null,
  abortController: null,

  fetchConversations: async () => {
    set({ isLoadingConversations: true, error: null });
    try {
      const response = await apiClient.get('/conversations/');
      set({ conversations: response.data, isLoadingConversations: false });
    } catch (error) {
      set({ error: error.message, isLoadingConversations: false });
    }
  },

  createConversation: async (title = "New Chat") => {
    set({ isGenerating: true, error: null });
    try {
      const response = await apiClient.post('/conversations/', { title });
      set((state) => ({ 
        conversations: [response.data, ...state.conversations],
        activeConversation: response.data,
        messages: [],
        isGenerating: false
      }));
      return response.data;
    } catch (error) {
      set({ error: error.message, isGenerating: false });
      throw error;
    }
  },

  selectConversation: async (conversation) => {
    if (get().activeConversation?.id === conversation.id) return;
    set({ activeConversation: conversation, isLoadingMessages: true, messages: [], error: null });
    try {
      const response = await apiClient.get(`/conversations/${conversation.id}/messages`);
      set({ messages: response.data, isLoadingMessages: false });
    } catch (error) {
      set({ error: error.message, isLoadingMessages: false });
    }
  },

  sendMessage: async (content) => {
    let { activeConversation } = get();
    
    if (!activeConversation) {
      try {
        activeConversation = await get().createConversation("New Chat");
      } catch (err) {
        return;
      }
    }

    const userMessageId = Date.now().toString() + "-user";
    const assistantMessageId = Date.now().toString() + "-assistant";

    set((state) => ({
      isGenerating: true,
      error: null,
      messages: [
        ...state.messages,
        { id: userMessageId, role: "user", content },
        { id: assistantMessageId, role: "assistant", content: "" }
      ]
    }));

    const controller = new AbortController();
    set({ abortController: controller });
    
    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
      const token = getToken();

      const response = await fetch(`${baseUrl}/api/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { "Authorization": `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          conversation_id: activeConversation.id,
          content
        }),
        signal: controller.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let done = false;

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          const chunkString = decoder.decode(value, { stream: true });
          const events = chunkString.split("\n\n");
          
          for (const event of events) {
            if (event.startsWith("data: ")) {
              try {
                const dataStr = event.replace("data: ", "").trim();
                if (!dataStr) continue;
                
                const data = JSON.parse(dataStr);
                
                if (data.type === "chunk") {
                  set((state) => ({
                    messages: state.messages.map((m) => 
                      m.id === assistantMessageId ? { ...m, content: m.content + data.content } : m
                    )
                  }));
                } else if (data.type === "done") {
                  set((state) => ({
                    messages: state.messages.map((m) => 
                      m.id === assistantMessageId ? { ...m, id: data.message_id } : m
                    ),
                    isGenerating: false,
                    abortController: null
                  }));
                  get().fetchConversations();
                } else if (data.type === "start") {
                  set((state) => ({
                    messages: state.messages.map((m) => 
                      m.id === userMessageId ? { ...m, id: data.user_message_id } : m
                    )
                  }));
                } else if (data.type === "error") {
                  throw new Error(data.content);
                }
              } catch (e) {
                console.error("Stream parse error:", e);
              }
            }
          }
        }
      }
    } catch (error) {
      if (error.name === "AbortError") {
        console.log("Stream aborted");
      } else {
        set({ error: error.message });
      }
      set({ isGenerating: false, abortController: null });
    }
  },

  deleteConversation: async (conversationId) => {
    try {
      await apiClient.delete(`/conversations/${conversationId}`);
      set((state) => {
        const filtered = state.conversations.filter(c => c.id !== conversationId);
        const isActiveDeleted = state.activeConversation?.id === conversationId;
        return {
          conversations: filtered,
          activeConversation: isActiveDeleted ? null : state.activeConversation,
          messages: isActiveDeleted ? [] : state.messages
        };
      });
    } catch (error) {
      set({ error: error.message });
    }
  },

  clearActive: () => set({ activeConversation: null, messages: [] }),
  
  stopGenerating: () => {
    const { abortController } = get();
    if (abortController) {
      abortController.abort();
    }
    set({ isGenerating: false, abortController: null });
  }
}));
