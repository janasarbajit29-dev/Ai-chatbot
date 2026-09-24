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
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await apiClient.post('/files/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      set((state) => ({
        documents: [response.data, ...state.documents],
        isUploading: false
      }));

      // Automatically trigger processing in the background
      get().processDocument(response.data.id);

      return response.data;
    } catch (error) {
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
          doc.id === id ? { ...doc, processing_status: 'processing' } : doc
        )
      }));

      const response = await apiClient.post(`/files/${id}/process`);
      
      set((state) => ({
        documents: state.documents.map(doc => 
          doc.id === id ? response.data : doc
        )
      }));
    } catch (error) {
      set((state) => ({
        documents: state.documents.map(doc => 
          doc.id === id ? { 
            ...doc, 
            processing_status: 'failed', 
            processing_error: error.response?.data?.detail || 'Processing failed' 
          } : doc
        )
      }));
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
