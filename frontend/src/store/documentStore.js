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
      const response = await apiClient.get('/files/');
      set({ documents: response.data, isLoadingDocuments: false });
    } catch (error) {
      set({ error: error.message, isLoadingDocuments: false });
    }
  },

  uploadDocument: async (file) => {
    set({ isUploading: true, error: null });
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await apiClient.post('/files/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      set((state) => ({ 
        documents: [response.data, ...state.documents],
        isUploading: false
      }));
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      set({ error: errorMessage, isUploading: false });
      throw new Error(errorMessage);
    }
  },

  deleteDocument: async (documentId) => {
    try {
      await apiClient.delete(`/files/${documentId}`);
      set((state) => ({
        documents: state.documents.filter(d => d.id !== documentId)
      }));
    } catch (error) {
      set({ error: error.message });
      throw error;
    }
  },
}));
