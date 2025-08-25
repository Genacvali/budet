import Dexie, { Table } from 'dexie';

export interface Category { 
  id: string; 
  user_id: string; 
  name: string; 
  kind: 'income'|'expense'; 
  icon?: string; 
  color?: string; 
  active: boolean; 
  limit_type: 'none'|'fixed'|'percent'; 
  limit_value: number; 
  created_at: string; 
  updated_at: string; 
  deleted_at?: string|null; 
}

export interface Source { 
  id: string; 
  user_id: string; 
  name: string; 
  currency: string; 
  expected_date?: string|null; 
  icon?: string; 
  color?: string; 
  created_at: string; 
  updated_at: string; 
  deleted_at?: string|null; 
}

export interface Rule { 
  id: string; 
  user_id: string; 
  source_id: string; 
  category_id: string; 
  percent: number; 
  cap_cents?: number|null; 
  created_at: string; 
  updated_at: string; 
  deleted_at?: string|null; 
}

export interface Operation { 
  id: string; 
  user_id: string; 
  type: 'income'|'expense'; 
  source_id?: string|null; 
  category_id: string; 
  wallet?: string|null; 
  amount_cents: number; 
  currency: string; 
  rate: number; 
  date: string; 
  note?: string|null; 
  created_at: string; 
  updated_at: string; 
  deleted_at?: string|null; 
}

export class BudgetDB extends Dexie {
  categories!: Table<Category, string>;
  sources!: Table<Source, string>;
  rules!: Table<Rule, string>;
  operations!: Table<Operation, string>;
  meta!: Table<{key: string; value: string}, string>;

  constructor() {
    super('budgetdb');
    this.version(1).stores({
      categories: 'id, updated_at, deleted_at',
      sources: 'id, updated_at, deleted_at',
      rules: 'id, updated_at, deleted_at, [source_id+category_id]',
      operations: 'id, date, updated_at, deleted_at',
      meta: 'key'
    });
  }
}

export const db = new BudgetDB();