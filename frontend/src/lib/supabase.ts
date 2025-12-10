import { createClient } from "@supabase/supabase-js";

// Configuration Supabase
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

// Création du client Supabase
export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Fonction utilitaire pour vérifier la connexion Supabase
export async function checkSupabaseConnection(): Promise<boolean> {
  try {
    const { error } = await supabase.from("users").select("count").limit(1);
    return !error;
  } catch {
    return false;
  }
}

export default supabase;
