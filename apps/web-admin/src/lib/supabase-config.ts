const SUPABASE_ENV_NAMES = [
  'NEXT_PUBLIC_SUPABASE_URL',
  'NEXT_PUBLIC_SUPABASE_ANON_KEY',
] as const;

export interface SupabasePublicConfig {
  url: string;
  anonKey: string;
}

function isValidHttpUrl(value: string) {
  try {
    const url = new URL(value);
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch {
    return false;
  }
}

export function getSupabaseConfigError() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL?.trim();
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.trim();

  if (!url || !anonKey) {
    return `Set ${SUPABASE_ENV_NAMES.join(' and ')} to use the admin UI.`;
  }

  if (!isValidHttpUrl(url)) {
    return 'NEXT_PUBLIC_SUPABASE_URL must be a valid HTTP or HTTPS URL.';
  }

  return null;
}

export function getSupabasePublicConfig(): SupabasePublicConfig | null {
  const error = getSupabaseConfigError();
  if (error) {
    return null;
  }

  return {
    url: process.env.NEXT_PUBLIC_SUPABASE_URL!.trim(),
    anonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!.trim(),
  };
}
