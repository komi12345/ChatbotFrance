"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Mail, Lock, MessageCircle } from "lucide-react";

// Schéma de validation avec Zod
const loginSchema = z.object({
  email: z
    .string()
    .min(1, "L'email est requis")
    .email("Format d'email invalide"),
  password: z
    .string()
    .min(1, "Le mot de passe est requis")
    .min(6, "Le mot de passe doit contenir au moins 6 caractères"),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated, isLoading: authLoading } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const hasRedirected = useRef(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  useEffect(() => {
    // Éviter les redirections multiples
    if (!authLoading && isAuthenticated && !hasRedirected.current) {
      hasRedirected.current = true;
      router.push("/dashboard");
    }
  }, [isAuthenticated, authLoading, router]);

  const onSubmit = async (data: LoginFormData) => {
    setError(null);
    setIsSubmitting(true);

    const result = await login(data);

    if (result.success) {
      hasRedirected.current = true;
      router.push("/dashboard");
    } else {
      setError(result.error || "Erreur de connexion");
    }

    setIsSubmitting(false);
  };

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F0F9FF]">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent" />
      </div>
    );
  }

  if (isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F0F9FF]">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <main className="flex min-h-screen">
      {/* Partie gauche - Formulaire */}
      <div className="flex flex-1 flex-col items-center justify-center bg-gradient-to-br from-[#e0f2fe] to-[#bae6fd] p-6 lg:p-12">
        <div className="w-full max-w-md">
          {/* Carte de login */}
          <div className="rounded-2xl bg-white p-8 shadow-login">
            {/* Logo et titre */}
            <div className="mb-8 text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500">
                <MessageCircle className="h-8 w-8 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-[#111827]">
                WhatsApp Chatbot
              </h1>
              <p className="mt-2 text-sm text-[#6B7280]">
                Connectez-vous à votre compte administrateur
              </p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              {/* Message d'erreur global */}
              {error && (
                <div className="rounded-lg bg-[#FEE2E2] p-3 text-sm text-[#DC2626]">
                  {error}
                </div>
              )}

              {/* Champ Email */}
              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm font-medium text-[#111827]">
                  Email
                </Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-[#9CA3AF]" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="admin@example.com"
                    autoComplete="email"
                    disabled={isSubmitting}
                    {...register("email")}
                    className={`h-12 pl-10 rounded-lg border-[#E5E7EB] bg-white text-[#111827] placeholder:text-[#9CA3AF] focus:border-emerald-500 focus:ring-emerald-500/10 ${
                      errors.email ? "border-[#EF4444]" : ""
                    }`}
                    inputMode="email"
                  />
                </div>
                {errors.email && (
                  <p className="text-sm text-[#EF4444]">{errors.email.message}</p>
                )}
              </div>

              {/* Champ Mot de passe */}
              <div className="space-y-2">
                <Label htmlFor="password" className="text-sm font-medium text-[#111827]">
                  Mot de passe
                </Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-[#9CA3AF]" />
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    autoComplete="current-password"
                    disabled={isSubmitting}
                    {...register("password")}
                    className={`h-12 pl-10 rounded-lg border-[#E5E7EB] bg-white text-[#111827] placeholder:text-[#9CA3AF] focus:border-emerald-500 focus:ring-emerald-500/10 ${
                      errors.password ? "border-[#EF4444]" : ""
                    }`}
                  />
                </div>
                {errors.password && (
                  <p className="text-sm text-[#EF4444]">{errors.password.message}</p>
                )}
              </div>

              {/* Bouton de connexion */}
              <Button
                type="submit"
                className="w-full h-12 rounded-lg bg-emerald-500 text-white font-medium hover:bg-emerald-500/90 transition-colors touch-manipulation"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <span className="flex items-center gap-2">
                    <span className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Connexion...
                  </span>
                ) : (
                  "Se connecter"
                )}
              </Button>
            </form>
          </div>
        </div>
      </div>

      {/* Partie droite - Décoration (visible uniquement sur grand écran) */}
      <div className="hidden lg:flex lg:flex-1 items-center justify-center bg-gradient-to-br from-[#a7f3d0] via-[#6ee7b7] to-[#5eead4] relative overflow-hidden">
        {/* Cercles décoratifs */}
        <div className="absolute top-20 left-20 h-32 w-32 rounded-full bg-emerald-500/20" />
        <div className="absolute top-40 right-32 h-48 w-48 rounded-full bg-[#34D399]/30" />
        <div className="absolute bottom-32 left-40 h-40 w-40 rounded-full bg-[#5EEAD4]/25" />
        <div className="absolute bottom-20 right-20 h-24 w-24 rounded-full bg-emerald-500/15" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-64 w-64 rounded-full bg-white/10" />
        
        {/* Contenu central */}
        <div className="relative z-10 text-center px-12">
          <div className="mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-3xl bg-white/20 backdrop-blur-sm">
            <MessageCircle className="h-12 w-12 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-white mb-4">
            Gérez vos campagnes WhatsApp
          </h2>
          <p className="text-lg text-white/80 max-w-md">
            Envoyez des messages personnalisés à vos contacts et suivez vos performances en temps réel.
          </p>
        </div>
      </div>
    </main>
  );
}
