import { writable } from 'svelte/store';
import { browser } from '$app/environment';

// Auth state
export const isAuthenticated = writable(false);
export const currentUser = writable<{user_id: string; email: string} | null>(null);

// Sync state
export const lastSync = writable<Date | null>(null);
export const syncInProgress = writable(false);

// Initialize auth state from localStorage
if (browser) {
  const token = localStorage.getItem('jwt');
  if (token) {
    isAuthenticated.set(true);
    // TODO: decode JWT to get user info
  }
}