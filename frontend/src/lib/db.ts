import Dexie, { type Table } from 'dexie';

export interface Meta { key: string; value: string; }

export interface Category {
  id: string; user_id: string; name: string; kind: 'income'|'expense';
  icon?: string; color: string; active: number;
  limit_type: string; limit_value: number;
  created_at: string; updated_at: string; deleted_at?: string|null;
}

export interface Source {
  id: string; user_id: string; name: string; currency: string;
  expected_date?: string|null; icon?: string|null; color?: string|null;
  created_at: string; updated_at: string; deleted_at?: string|null;
}

export interface Rule {
  id: string; user_id: string; source_id: string; category_id: string;
  percent: number; cap_cents?: number|null; fixed_cents?: number|null; // NEW
  created_at: string; updated_at: string; deleted_at?: string|null;
}

export interface Operation {
  id: string; user_id: string; type: 'income'|'expense';
  source_id?: string|null; category_id: string; wallet?: string|null;
  amount_cents: number; currency: string; rate: number;
  date: string; note?: string|null;
  created_at: string; updated_at: string; deleted_at?: string|null;
}

class BudgetDB extends Dexie {
  meta!: Table<Meta, string>;
  categories!: Table<Category, string>;
  sources!: Table<Source, string>;
  rules!: Table<Rule, string>;
  operations!: Table<Operation, string>;

  constructor() {
    super('budgetdb');
    this.version(1).stores({
      meta: 'key',
      categories: 'id, user_id, kind, updated_at, deleted_at',
      sources:    'id, user_id, updated_at, deleted_at',
      rules:      'id, user_id, source_id, category_id, updated_at, deleted_at',
      operations: 'id, user_id, type, category_id, date, updated_at, deleted_at'
    });
  }
}

export const db = new BudgetDB();