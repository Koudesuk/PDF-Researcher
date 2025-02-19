import { create, StateCreator } from 'zustand';

interface ChatFeatureState {
  enableChatWithPicture: boolean;
  enableWebResearch: boolean;
  toggleChatWithPicture: () => void;
  toggleWebResearch: () => void;
}

const createStore: StateCreator<ChatFeatureState> = (set) => ({
  enableChatWithPicture: false,
  enableWebResearch: false,
  toggleChatWithPicture: () => 
    set((state) => ({ enableChatWithPicture: !state.enableChatWithPicture })),
  toggleWebResearch: () => 
    set((state) => ({ enableWebResearch: !state.enableWebResearch })),
});

const useChatFeatureStore = create<ChatFeatureState>(createStore);

export default useChatFeatureStore;