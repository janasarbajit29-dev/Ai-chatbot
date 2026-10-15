import { create } from 'zustand';
import { apiClient } from '../lib/axios';

export const useDocumentStore = create((set, get) => ({
  documents: [],
  isLoadingDocuments: false,
  isUploading: false,
  error: null,

  fetchDocuments: async () => {
    set({ isLoadingDocuments: true, error: null });
    try {
      const response = await apiClient.get('/api/files/');
      set({ documents: response.data, isLoadingDocuments: false });
    } catch (error) {
      set({ error: error.message, isLoadingDocuments: false });
    }
  },

  fetchDocument: async (id) => {
    try {
      const response = await apiClient.get(`/api/files/${id}`);
      set((state) => ({
        documents: state.documents.some((d) => d.id === id)
          ? state.documents.map((d) => (d.id === id ? response.data : d))
          : [response.data, ...state.documents],
      }));
      return response.data;
    } catch (error) {
      console.error("Failed to fetch document", error);
      throw error;
    }
  },

  uploadDocument: async (file) => {
    set({ isUploading: true, error: null });
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await apiClient.post('/api/files/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      set((state) => ({
        documents: [response.data, ...state.documents],
        isUploading: false
      }));

      // Automatically trigger processing in the background
      get().processDocument(response.data.id).catch(() => {});

      return response.data;
    } catch (error) {
      if (error.response?.status === 409) {
        set({ isUploading: false });
        await get().fetchDocuments();
        const existing = get().documents.find(
          (d) => d.original_filename === file.name && d.file_size === file.size
        );
        if (existing) {
          if (existing.processing_status === 'uploaded' || existing.processing_status === 'failed') {
            get().processDocument(existing.id).catch(() => {});
          }
          return existing;
        }
      }
      set({
        error: error.response?.data?.detail || 'Failed to upload document',
        isUploading: false
      });
      throw error;
    }
  },

  processDocument: async (id) => {
    try {
      // Optimistically update status
      set((state) => ({
        documents: state.documents.map(doc =>
          doc.id === id ? { ...doc, processing_status: 'processing', processing_error: null } : doc
        )
      }));

      const response = await apiClient.post(`/api/files/${id}/process`);

      set((state) => ({
        documents: state.documents.map(doc =>
          doc.id === id ? response.data : doc
        )
      }));
      return response.data;
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Processing failed';
      set((state) => ({
        documents: state.documents.map(doc =>
          doc.id === id ? {
            ...doc,
            processing_status: 'failed',
            processing_error: errorMsg
          } : doc
        )
      }));
      throw error;
    }
  },

  deleteDocument: async (documentId) => {
    try {
      await apiClient.delete(`/api/files/${documentId}`);
      set((state) => ({
        documents: state.documents.filter(d => d.id !== documentId)
      }));
    } catch (error) {
      set({ error: error.message });
      throw error;
    }
  },
}));
