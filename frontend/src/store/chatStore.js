import { create } from 'zustand';
import { apiClient } from '../lib/axios';
import { getAccessToken } from '../utils/auth';

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
      const response = await apiClient.get('/api/conversations/');
      set({ conversations: response.data, isLoadingConversations: false });
    } catch (error) {
      set({ error: error.message, isLoadingConversations: false });
    }
  },

  createConversation: async (title = "New Chat") => {
    set({ isGenerating: true, error: null });
    try {
      const response = await apiClient.post('/api/conversations/', { title });
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
      const response = await apiClient.get(`/api/conversations/${conversation.id}/messages`);
      set({ messages: response.data, isLoadingMessages: false });
    } catch (error) {
      set({ error: error.message, isLoadingMessages: false });
    }
  },

  sendMessage: async (content, regenerateMessageId = null) => {
    let { activeConversation, messages } = get();
    
    if (!activeConversation) {
      try {
        activeConversation = await get().createConversation("New Chat");
      } catch (err) {
        return;
      }
    }

    if (activeConversation.title === "New Chat" || activeConversation.title === "New Conversation") {
      let newTitle = content.split('\n')[0].substring(0, 30).trim();
      if (newTitle.length === 30) newTitle += "...";
      get().renameConversation(activeConversation.id, newTitle).catch(() => {});
    }

    let actualContent = content;
    const userMessageId = regenerateMessageId ? null : Date.now().toString() + "-user";
    const assistantMessageId = regenerateMessageId || Date.now().toString() + "-assistant";

    if (regenerateMessageId) {
      const msgIndex = messages.findIndex(m => m.id === regenerateMessageId);
      if (msgIndex > 0) {
        actualContent = messages[msgIndex - 1].content;
      }
      set((state) => ({
        isGenerating: true,
        error: null,
        messages: state.messages.map(m => m.id === regenerateMessageId ? { ...m, content: "", isError: false, isStreaming: true } : m)
      }));
    } else {
      set((state) => ({
        isGenerating: true,
        error: null,
        messages: [
          ...state.messages,
          { id: userMessageId, role: "user", content: actualContent },
          { id: assistantMessageId, role: "assistant", content: "", isError: false, isStreaming: true }
        ]
      }));
    }

    const controller = new AbortController();
    set({ abortController: controller });
    
    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
      const token = getAccessToken();

      const response = await fetch(`${baseUrl}/api/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { "Authorization": `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          conversation_id: activeConversation.id,
          content: actualContent
        }),
        signal: controller.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("The response did not include a readable stream.");

      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      let streamFinished = false;
      let receivedContent = false;

      const handleEvent = (eventText) => {
        const dataLines = eventText
          .split(/\r?\n/)
          .filter((line) => line.startsWith("data:"))
          .map((line) => line.slice(5).replace(/^ /, ""));
        if (dataLines.length === 0) return;

        const dataStr = dataLines.join("\n").trim();
        if (!dataStr) return;

        let data;
        try {
          data = JSON.parse(dataStr);
        } catch (parseError) {
          console.error("Stream parse error:", parseError);
          return;
        }

        if (data.type === "chunk" && typeof data.content === "string") {
          if (!data.content) return;
          receivedContent = true;
          set((state) => ({
            messages: state.messages.map((message) =>
              message.id === assistantMessageId
                ? { ...message, content: message.content + data.content, isStreaming: false }
                : message
            ),
          }));
        } else if (data.type === "done") {
          streamFinished = true;
          set((state) => ({
            messages: state.messages.map((message) =>
              message.id === assistantMessageId
                ? { ...message, id: data.message_id, isError: false, isStreaming: false }
                : message
            ),
            isGenerating: false,
            abortController: null,
          }));
          get().fetchConversations();
        } else if (data.type === "start") {
          if (userMessageId) {
            set((state) => ({
              messages: state.messages.map((message) =>
                message.id === userMessageId
                  ? { ...message, id: data.user_message_id }
                  : message
              ),
            }));
          }
        } else if (data.type === "sources") {
          set((state) => ({
            messages: state.messages.map((message) =>
              message.id === assistantMessageId
                ? { ...message, sources: data.sources }
                : message
            ),
          }));
        } else if (data.type === "error") {
          throw new Error(data.content || "An error occurred during generation.");
        }
      };

      while (true) {
        const { value, done: readerDone } = await reader.read();
        buffer += decoder.decode(value || new Uint8Array(), { stream: !readerDone });

        let boundary;
        while ((boundary = buffer.match(/\r?\n\r?\n/)) !== null) {
          const eventText = buffer.slice(0, boundary.index);
          buffer = buffer.slice(boundary.index + boundary[0].length);
          handleEvent(eventText);
        }

        if (readerDone) {
          if (buffer.trim()) handleEvent(buffer);
          break;
        }
      }

      if (!streamFinished) {
        set((state) => ({
          isGenerating: false,
          abortController: null,
          error: receivedContent ? state.error : "The response stream ended before a reply arrived.",
          messages: state.messages.map((message) =>
            message.id === assistantMessageId
              ? { ...message, isError: !receivedContent, isStreaming: false }
              : message
          ),
        }));
      }
    } catch (error) {
      if (error.name === "AbortError") {
        console.log("Stream aborted");
      } else {
        set((state) => ({ 
          error: error.message,
          messages: state.messages.map(m => m.id === assistantMessageId ? { ...m, isError: true, isStreaming: false } : m)
        }));
      }
      set((state) => ({
        isGenerating: false,
        abortController: null,
        messages: state.messages.map((message) =>
          message.id === assistantMessageId
            ? { ...message, isStreaming: false }
            : message
        ),
      }));
    }
  },

  renameConversation: async (conversationId, newTitle) => {
    try {
      const response = await apiClient.patch(`/api/conversations/${conversationId}`, { title: newTitle });
      set((state) => ({
        conversations: state.conversations.map(c => c.id === conversationId ? { ...c, title: response.data.title } : c),
        activeConversation: state.activeConversation?.id === conversationId ? { ...state.activeConversation, title: response.data.title } : state.activeConversation
      }));
    } catch (error) {
      set({ error: error.message });
      throw error;
    }
  },

  deleteConversation: async (conversationId) => {
    try {
      await apiClient.delete(`/api/conversations/${conversationId}`);
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
    set((state) => ({
      isGenerating: false,
      abortController: null,
      messages: state.messages.map((message) =>
        message.isStreaming ? { ...message, isStreaming: false } : message
      ),
    }));
  }
}));
