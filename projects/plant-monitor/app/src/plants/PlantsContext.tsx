import React, { createContext, useContext } from 'react';
import type { PlantsService } from './types';

const Ctx = createContext<PlantsService | null>(null);
export function PlantsProvider({ service, children }: { service: PlantsService; children: React.ReactNode }) {
  return <Ctx.Provider value={service}>{children}</Ctx.Provider>;
}
export function usePlants(): PlantsService {
  const s = useContext(Ctx);
  if (!s) throw new Error('usePlants outside PlantsProvider');
  return s;
}
