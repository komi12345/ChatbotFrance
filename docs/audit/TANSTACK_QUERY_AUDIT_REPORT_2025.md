# Rapport d'Audit TanStack Query

**Date de l'audit** : 29 décembre 2025  
**Version du projet** : 1.0  
**Objectifs** :
- Vérifier les valeurs staleTime et gcTime
- Identifier les requêtes qui refetch trop souvent
- Vérifier l'utilisation des optimistic updates

---

## 📊 Résumé Exécutif

| Aspect | Statut | Commentaire |
|--------|--------|-------------|
| Configuration globale | ✅ Bon | staleTime 2min, gcTime 10min |
| Optimistic Updates | ✅ Implémenté | Contacts et Catégories |
| Rollback sur erreur | ✅ Implémenté | Contexte de rollback présent |
| Polling excessif | ⚠️ À surveiller | Monitoring toutes les 10s |
| DevTools en production | ❌ Problème | Inclus dans le bundle prod |

---

## 🔧 Configuration Globale

### query-client.ts

```typescript
// Configuration actuelle
{
  queries: {
    staleTime: 2 * 60 * 1000,      // ✅ 2 minutes
    gcTime: 10 * 60 * 1000,        // ✅ 10 minutes
    retry: 1,                       // ✅ 1 retry
    refetchOnWindowFocus: true,     // ⚠️ Peut causer des refetch
    refetchOnReconnect: true,       // ✅ Bon
    refetchOnMount: false,          // ✅ Évite les refetch inutiles
  },
  mutations: {
    retry: 0,                       // ✅ Pas de retry
  },
}
```

### Évaluation

| Paramètre | Valeur | Objectif | Statut |
|-----------|--------|----------|--------|
| staleTime | 2 min | 2 min | ✅ |
| gcTime | 10 min | 10 min | ✅ |
| retry | 1 | 1-2 | ✅ |
| refetchOnWindowFocus | true | false | ⚠️ |
| refetchOnMount | false | false | ✅ |

**Recommandation** : Désactiver `refetchOnWindowFocus` pour éviter les requêtes inutiles lors du changement de fenêtre.

---

## 📋 Analyse par Hook

### 1. useStats.ts

| Query | staleTime | gcTime | Polling | Statut |
|-------|-----------|--------|---------|--------|
| useDashboardStats | 5 min | 15 min | Non | ✅ |
| useMessageStats | 5 min | 15 min | Non | ✅ |
| useDailyStats | 5 min | 15 min | Non | ✅ |
| useStatusDistribution | 5 min | 15 min | Non | ✅ |
| useRecentMessages | 5 min | 15 min | Non | ✅ |

**Observations** :
- ✅ staleTime de 5 minutes pour les statistiques (approprié)
- ✅ gcTime de 15 minutes (bon pour le cache)
- ⚠️ `useDashboardStats` fait 4 requêtes API en parallèle (peut être optimisé)

### 2. useContacts.ts

| Query | staleTime | gcTime | Polling | Statut |
|-------|-----------|--------|---------|--------|
| useContacts | 2 min | 10 min | Non | ✅ |
| useContact | 2 min | 10 min | Non | ✅ |
| useWhatsAppVerificationStats | 2 min | 10 min | Non | ✅ |

**Optimistic Updates** :
- ✅ `useCreateContact` : Mise à jour optimiste du compteur
- ✅ Rollback implémenté en cas d'erreur
- ✅ Invalidation des caches liés après mutation

### 3. useCategories.ts

| Query | staleTime | gcTime | Polling | Statut |
|-------|-----------|--------|---------|--------|
| useCategories | 2 min | 10 min | Non | ✅ |
| useCategory | 2 min | 10 min | Non | ✅ |
| useAvailableContactsForCategory | 30 sec | 5 min | Non | ✅ |

**Optimistic Updates** :
- ✅ `useCreateCategory` : Mise à jour optimiste du compteur
- ✅ Rollback implémenté en cas d'erreur
- ✅ Invalidation des caches liés après mutation

### 4. useCampaigns.ts

| Query | staleTime | gcTime | Polling | Statut |
|-------|-----------|--------|---------|--------|
| useCampaigns | défaut (2 min) | défaut (10 min) | Non | ✅ |
| useCampaign | défaut (2 min) | défaut (10 min) | 3s si "sending" | ✅ |
| useCampaignStats | défaut (2 min) | défaut (10 min) | 3s si "sending" | ✅ |

**Observations** :
- ✅ Polling conditionnel (seulement si campagne en cours)
- ⚠️ Pas d'optimistic updates pour les mutations
- ✅ Invalidation correcte des caches

### 5. useMessages.ts

| Query | staleTime | gcTime | Polling | Statut |
|-------|-----------|--------|---------|--------|
| useMessages | défaut (2 min) | défaut (10 min) | Non | ✅ |
| useMessage | défaut (2 min) | défaut (10 min) | Non | ✅ |
| useMessageStats | défaut (2 min) | défaut (10 min) | Non | ✅ |

**Observations** :
- ✅ Utilise les valeurs par défaut (approprié)
- ✅ Pas de polling inutile

### 6. useMonitoring.ts

| Query | staleTime | gcTime | Polling | Statut |
|-------|-----------|--------|---------|--------|
| useMonitoringStats | 5 sec | défaut | 10 sec | ⚠️ |
| useMonitoringHistory | 5 sec | défaut | 10 sec | ⚠️ |
| useMonitoringErrors | 5 sec | défaut | 10 sec | ⚠️ |

**Observations** :
- ⚠️ Polling toutes les 10 secondes (3 requêtes)
- ⚠️ staleTime très court (5 secondes)
- ⚠️ Impact potentiel sur les performances et la bande passante

**Recommandation** : Augmenter l'intervalle de polling à 30 secondes ou permettre à l'utilisateur de le configurer.

### 7. useUsers.ts

| Query | staleTime | gcTime | Polling | Statut |
|-------|-----------|--------|---------|--------|
| useUsers | défaut (2 min) | défaut (10 min) | Non | ✅ |
| useUser | défaut (2 min) | défaut (10 min) | Non | ✅ |

**Observations** :
- ✅ Utilise les valeurs par défaut
- ⚠️ Pas d'optimistic updates pour les mutations

---

## ✅ Optimistic Updates - Analyse Détaillée

### Implémentations Existantes

#### useCreateContact
```typescript
onMutate: async () => {
  await queryClient.cancelQueries({ queryKey: ["stats"] });
  const previousDashboardStats = queryClient.getQueryData(["stats", "dashboard"]);
  
  // Mise à jour optimiste
  queryClient.setQueryData(["stats", "dashboard"], (old) => ({
    ...old,
    total_contacts: (old.total_contacts || 0) + 1,
  }));
  
  return { previousDashboardStats };
},
onError: (_err, _newContact, context) => {
  // Rollback
  if (context?.previousDashboardStats) {
    queryClient.setQueryData(["stats", "dashboard"], context.previousDashboardStats);
  }
},
```

#### useCreateCategory
```typescript
// Même pattern que useCreateContact
// ✅ Mise à jour optimiste du compteur total_categories
// ✅ Rollback en cas d'erreur
```

### Mutations Sans Optimistic Updates

| Hook | Mutation | Impact | Priorité |
|------|----------|--------|----------|
| useCampaigns | useCreateCampaign | Moyen | Basse |
| useCampaigns | useSendCampaign | Faible | Basse |
| useContacts | useDeleteContact | Élevé | Haute |
| useCategories | useDeleteCategory | Élevé | Haute |
| useUsers | useCreateUser | Faible | Basse |

**Recommandation** : Ajouter des optimistic updates pour `useDeleteContact` et `useDeleteCategory` pour améliorer la réactivité de l'UI.

---

## ⚠️ Problèmes Identifiés

### 1. ReactQueryDevtools en Production

**Fichier** : `providers.tsx`

```typescript
// PROBLÈME : DevTools inclus en production
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

<ReactQueryDevtools initialIsOpen={false} />
```

**Impact** : ~30KB ajoutés au bundle en production

**Solution** :
```typescript
// Charger conditionnellement
const ReactQueryDevtools = process.env.NODE_ENV === 'development'
  ? lazy(() => import('@tanstack/react-query-devtools').then(m => ({ default: m.ReactQueryDevtools })))
  : () => null;
```

### 2. Polling Excessif sur Monitoring

**Fichier** : `useMonitoring.ts`

```typescript
// PROBLÈME : 3 requêtes toutes les 10 secondes
refetchInterval: 10000,
staleTime: 5000,
```

**Impact** : 18 requêtes/minute même si l'utilisateur n'est pas sur la page

**Solution** :
```typescript
// Augmenter l'intervalle et utiliser visibilitychange
refetchInterval: 30000, // 30 secondes
refetchIntervalInBackground: false, // Pas de polling en arrière-plan
```

### 3. refetchOnWindowFocus Activé

**Fichier** : `query-client.ts`

```typescript
// PROBLÈME : Refetch à chaque focus de fenêtre
refetchOnWindowFocus: true,
```

**Impact** : Requêtes inutiles lors du changement de fenêtre

**Solution** :
```typescript
refetchOnWindowFocus: false,
```

### 4. useDashboardStats - Requêtes Multiples

**Fichier** : `useStats.ts`

```typescript
// PROBLÈME : 4 requêtes API en parallèle
const messagesResponse = await api.get("/messages/stats");
const contactsResponse = await api.get("/contacts?page=1&size=1");
const campaignsResponse = await api.get("/campaigns?page=1&size=1");
const categoriesResponse = await api.get("/categories?page=1&size=1");
```

**Impact** : 4 requêtes au lieu d'une seule

**Solution** : Créer un endpoint backend `/dashboard/stats` qui retourne toutes les données en une seule requête.

---

## 📈 Recommandations d'Optimisation

### Priorité Haute

1. **Supprimer ReactQueryDevtools en production**
   - Gain : ~30KB bundle size
   - Effort : Faible

2. **Désactiver refetchOnWindowFocus**
   - Gain : Réduction des requêtes inutiles
   - Effort : Faible

### Priorité Moyenne

3. **Réduire le polling du monitoring**
   - Gain : Réduction de 66% des requêtes monitoring
   - Effort : Faible

4. **Ajouter optimistic updates pour les suppressions**
   - Gain : Meilleure réactivité UI
   - Effort : Moyen

### Priorité Basse

5. **Créer un endpoint dashboard consolidé**
   - Gain : Réduction de 75% des requêtes dashboard
   - Effort : Moyen (backend + frontend)

---

## 📊 Métriques de Performance

### Requêtes par Page (estimation)

| Page | Requêtes Initiales | Polling | Total/min |
|------|-------------------|---------|-----------|
| /dashboard | 4 | 0 | 4 |
| /dashboard/monitoring | 3 | 18 | 21 |
| /contacts | 1 | 0 | 1 |
| /categories | 1 | 0 | 1 |
| /campaigns | 1 | 0-20* | 1-21 |
| /messages | 1 | 0 | 1 |

*Polling actif seulement si campagne en cours d'envoi

### Après Optimisations

| Page | Requêtes Initiales | Polling | Total/min |
|------|-------------------|---------|-----------|
| /dashboard | 1 | 0 | 1 |
| /dashboard/monitoring | 3 | 6 | 9 |
| /contacts | 1 | 0 | 1 |
| /categories | 1 | 0 | 1 |
| /campaigns | 1 | 0-20* | 1-21 |
| /messages | 1 | 0 | 1 |

---

## ✅ Points Positifs

1. **Architecture bien structurée** : Clés de cache organisées par domaine
2. **Optimistic updates implémentés** : Pour les créations de contacts et catégories
3. **Rollback fonctionnel** : Gestion des erreurs avec restauration de l'état
4. **Polling conditionnel** : Campagnes ne pollent que si nécessaire
5. **Invalidation correcte** : Les mutations invalident les caches appropriés
6. **staleTime et gcTime appropriés** : Valeurs par défaut raisonnables

---

## 📝 Prochaines Étapes

1. [ ] Corriger ReactQueryDevtools en production
2. [ ] Désactiver refetchOnWindowFocus
3. [ ] Réduire l'intervalle de polling du monitoring
4. [ ] Ajouter optimistic updates pour les suppressions
5. [ ] Créer un endpoint dashboard consolidé (backend)
6. [ ] Re-mesurer les performances après optimisations

---

*Rapport généré dans le cadre de l'audit complet 2025*
