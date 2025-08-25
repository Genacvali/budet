import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import { isAuthenticated } from '$lib/stores';

export const load = async ({ url }) => {
  if (browser) {
    const token = localStorage.getItem('jwt');
    const authenticated = !!token;
    isAuthenticated.set(authenticated);
    
    // Redirect logic
    if (!authenticated && !url.pathname.startsWith('/auth')) {
      goto('/auth/login');
    } else if (authenticated && url.pathname.startsWith('/auth')) {
      goto('/');
    }
  }
};