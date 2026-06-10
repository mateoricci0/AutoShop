import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface StoreSelectorStore {
  activeStoreId: string | null
  setActiveStoreId: (id: string | null) => void
}

export const useStoreSelectorStore = create<StoreSelectorStore>()(
  persist(
    (set) => ({
      activeStoreId: null,
      setActiveStoreId: (id) => set({ activeStoreId: id }),
    }),
    { name: 'ase-active-store' }
  )
)
