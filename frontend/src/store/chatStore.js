import { create } from 'zustand';
import { apiClient } from '../lib/axios';
import { getAccessToken } from '../utils/auth';
import { useDocumentStore } from './documentStore';

const ATTACHMENTS_STORAGE_KEY = "aura_conversation_attachments";

const loadSavedAttachments = () => {
  try {
    const raw = localStorage.getItem(ATTACHMENTS_STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch (_e) {
    return {};
  }
};

const persistAttachments = (attachments) => {
  try {
    localStorage.setItem(ATTACHMENTS_STORAGE_KEY, JSON.stringify(attachments));
  } catch (e) {
    console.error("Failed to save attachments to localStorage", e);
  }
};

export const useChatStore = create((set, get) => ({
  conversations: [],
  activeConversation: null,
  attachedDocument: null,
  conversationAttachments: loadSavedAttachments(),
  messages: [],
  isLoadingConversations: false,
  isLoadingMessages: false,
  isGenerating: false,
  error: null,
  abortController: null,
  messagesAbortController: null,

  attachDocument: (document, targetConvId = null) => {
    const { activeConversation, conversationAttachments } = get();
    const convId = targetConvId || activeConversation?.id;
    const updated = convId
      ? { ...conversationAttachments, [convId]: document }
      : conversationAttachments;
    if (convId) {
      persistAttachments(updated);
    }
    set({
      attachedDocument: (!convId || convId === activeConversation?.id) ? document : get().attachedDocument,
      conversationAttachments: updated,
    });
  },

  updateAttachedDocument: (updates, targetConvId = null) => {
    const { activeConversation, conversationAttachments } = get();
    const convId = targetConvId || activeConversation?.id;
    const current = (convId && conversationAttachments[convId]) || get().attachedDocument;
    if (!current) return;
    const merged = { ...current, ...updates };
    const updated = convId
      ? { ...conversationAttachments, [convId]: merged }
      : conversationAttachments;
    if (convId) {
      persistAttachments(updated);
    }
    set({
      attachedDocument: (!convId || convId === activeConversation?.id) ? merged : get().attachedDocument,
      conversationAttachments: updated,
    });
  },

  detachDocument: (documentId = null) => {
    const { activeConversation, conversationAttachments, attachedDocument } = get();
    if (documentId && attachedDocument && attachedDocument.id !== documentId) {
      return;
    }
    const updated = { ...conversationAttachments };
    if (activeConversation) {
      delete updated[activeConversation.id];
      persistAttachments(updated);
    }
    set({
      attachedDocument: null,
      conversationAttachments: updated,
    });
  },

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
    if (get().messagesAbortController) {
      get().messagesAbortController.abort();
    }
    set({ isGenerating: true, error: null });
    try {
      const response = await apiClient.post('/api/conversations/', { title });
      set((state) => ({
        conversations: [response.data, ...state.conversations],
        activeConversation: response.data,
        attachedDocument: null,
        messages: [],
        isLoadingMessages: false,
        messagesAbortController: null,
        isGenerating: false
      }));
      return response.data;
    } catch (error) {
      set({ error: error.message, isGenerating: false });
      throw error;
    }
  },

  selectConversation: async (conversation) => {
    if (!conversation) return;
    if (get().activeConversation?.id === conversation.id) return;

    if (get().isGenerating) {
      get().stopGenerating();
    }

    if (get().messagesAbortController) {
      get().messagesAbortController.abort();
    }

    const controller = new AbortController();
    const savedDoc = (conversation && get().conversationAttachments[conversation.id]) || null;

    set({
      activeConversation: conversation,
      attachedDocument: savedDoc,
      isLoadingMessages: true,
      messages: [],
      error: null,
      messagesAbortController: controller,
    });

    if (savedDoc && typeof savedDoc.id === 'number' && savedDoc.id > 0) {
      useDocumentStore.getState().fetchDocument(savedDoc.id).then((freshDoc) => {
        if (freshDoc && get().activeConversation?.id === conversation.id) {
          get().updateAttachedDocument(freshDoc, conversation.id);
        }
      }).catch(() => {});
    }

    try {
      const response = await apiClient.get(`/api/conversations/${conversation.id}/messages`, {
        signal: controller.signal,
      });

      if (get().activeConversation?.id === conversation.id) {
        set({
          messages: response.data || [],
          isLoadingMessages: false,
          messagesAbortController: null,
          error: null,
        });
      }
    } catch (error) {
      if (
        error?.name === "CanceledError" ||
        error?.name === "AbortError" ||
        error?.code === "ERR_CANCELED" ||
        error?.message === "canceled"
      ) {
        return;
      }

      if (get().activeConversation?.id === conversation.id) {
        set({
          error:
            error.response?.data?.detail ||
            error.message ||
            "Failed to load messages",
          isLoadingMessages: false,
          messagesAbortController: null,
        });
      }
    }
  },

  sendMessage: async (content, regenerateMessageId = null) => {
    let { activeConversation, messages } = get();

    if (!activeConversation) {
      try {
        activeConversation = await get().createConversation("New Chat");
      } catch (_err) {
        return;
      }
    }

    // Determine the attached document strictly for the active conversation
    const currentAttachments = get().conversationAttachments || {};
    const attachedForThisConv = (activeConversation && currentAttachments[activeConversation.id]) || null;
    const documentIdToSend = (attachedForThisConv && typeof attachedForThisConv.id === 'number' && attachedForThisConv.id > 0)
      ? attachedForThisConv.id
      : null;

    if (get().attachedDocument !== attachedForThisConv) {
      set({ attachedDocument: attachedForThisConv });
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
          content: actualContent,
          document_id: documentIdToSend
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
      const isActiveDeleted = get().activeConversation?.id === conversationId;
      if (isActiveDeleted) {
        if (get().isGenerating) {
          get().stopGenerating();
        }
        if (get().messagesAbortController) {
          get().messagesAbortController.abort();
        }
      }

      await apiClient.delete(`/api/conversations/${conversationId}`);
      const updatedAttachments = { ...get().conversationAttachments };
      delete updatedAttachments[conversationId];
      persistAttachments(updatedAttachments);

      set((state) => {
        const filtered = state.conversations.filter(c => c.id !== conversationId);
        return {
          conversations: filtered,
          activeConversation: isActiveDeleted ? null : state.activeConversation,
          attachedDocument: isActiveDeleted ? null : state.attachedDocument,
          conversationAttachments: updatedAttachments,
          messages: isActiveDeleted ? [] : state.messages,
          isLoadingMessages: isActiveDeleted ? false : state.isLoadingMessages,
          messagesAbortController: isActiveDeleted ? null : state.messagesAbortController,
          error: isActiveDeleted ? null : state.error,
        };
      });
    } catch (error) {
      set({
        error:
          error.response?.data?.detail ||
          error.message ||
          "Failed to delete conversation",
      });
    }
  },

  clearActive: () => {
    if (get().isGenerating) {
      get().stopGenerating();
    }
    if (get().messagesAbortController) {
      get().messagesAbortController.abort();
    }
    set({
      activeConversation: null,
      messages: [],
      attachedDocument: null,
      isLoadingMessages: false,
      error: null,
      messagesAbortController: null,
    });
  },

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
