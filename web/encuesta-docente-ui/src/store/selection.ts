// src/store/selection.ts
import { create } from "zustand";

type SelState = {
  surveyId: string | null;
  setSurveyId: (id: string | null) => void;
  selected: Record<string, boolean>; // teacher_id -> checked
  toggle: (id: string) => void;
  clear: () => void;
};

export const useSelection = create<SelState>((set) => ({
  surveyId: null,
  setSurveyId: (id) => set({ surveyId: id }),
  selected: {},
  toggle: (id) =>
    set((s) => ({ selected: { ...s.selected, [id]: !s.selected[id] } })),
  clear: () => set({ selected: {} }),
}));
