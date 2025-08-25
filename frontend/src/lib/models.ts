import { z } from 'zod';

export const zOp = z.object({
  id: z.string(),
  type: z.enum(['income','expense']),
  amount_cents: z.number().int(),
  category_id: z.string(),
  source_id: z.string().nullable().optional(),
  currency: z.string().default('RUB'),
  rate: z.number().default(1),
  date: z.string(), 
  note: z.string().optional().nullable(),
  user_id: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  deleted_at: z.string().nullable().optional(),
});

export type PlanRow = {
  category_id: string;
  plan_cents: number;
  fact_cents: number;
  by_source: Record<string, number>;
};