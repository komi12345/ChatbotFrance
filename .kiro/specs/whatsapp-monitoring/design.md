# Design Document - WhatsApp Monitoring System

## Overview

Ce document décrit l'architecture et la conception du système de monitoring WhatsApp pour le dashboard d'administration. Le système permet de suivre en temps réel les messages envoyés, d'appliquer une limite quotidienne de 180 messages, et d'afficher des alertes visuelles sur le dashboard.

L'architecture utilise une approche hybride :
- **Redis** : Compteurs temps réel (performance, < 100ms)
- **Supabase** : Persistance et historique (fiabilité, survit aux redémarrages)

## Architecture

```mermaid
graph TB
    subgraph Frontend["Frontend (Next.js)"]
        MP[Monitoring Page]
        Nav[Navigation Badge]
        Hook[useMonitoring Hook]
    end
    
    subgraph Backend["Backend (FastAPI)"]
        API[/api/monitoring/*]
        MS[MonitoringService]
        CT[Celery Tasks]
    end
    
    subgraph Storage["Storage"]
        Redis[(Redis)]
        Supabase[(Supabase)]
    end
    
    MP --> Hook
    Nav --> Hook
    Hook --> API
    API --> MS
    CT --> MS
    MS --> Redis
    MS --> Supabase
    
    CT -->|"send_single_message"| MS
    MS -->|"check_can_send()"| CT
```

## Components and Interfaces

### Backend Components

#### 1. MonitoringService (`backend/app/services/monitoring_service.py`)

Service principal gérant les compteurs et la logique de monitoring.

```python
class MonitoringService:
    """Service de monitoring des messages WhatsApp"""
    
    def __init__(self, redis_url: str):
        """Initialise le service avec connexion Redis"""
    
    # Compteurs
    def increment_message_counter(self, message_type: str) -> int:
        """Incrémente le compteur pour message_1 ou message_2"""
    
    def increment_error_counter(self) -> int:
        """Incrémente le compteur d'erreurs"""
    
    def get_daily_stats(self) -> DailyStats:
        """Retourne les statistiques du jour"""
    
    # Protection
    def can_send_message(self) -> tuple[bool, str]:
        """Vérifie si un message peut être envoyé (limite 180)"""
    
    def get_alert_level(self) -> AlertLevel:
        """Retourne le niveau d'alerte actuel"""
    
    # Calculs
    def calculate_remaining_capacity(self) -> int:
        """Calcule la capacité restante avec taux d'interaction"""
    
    def calculate_interaction_rate(self) -> float:
        """Calcule le taux d'interaction (message_2/message_1)"""
    
    # Persistance
    def sync_to_supabase(self) -> None:
        """Synchronise les compteurs Redis vers Supabase"""
    
    def sync_from_supabase(self) -> None:
        """Récupère les compteurs depuis Supabase au démarrage"""
    
    def reset_daily_counters(self) -> None:
        """Reset les compteurs à minuit (avec persistance)"""
```

#### 2. Monitoring Router (`backend/app/routers/monitoring.py`)

Endpoints API pour le monitoring.

```python
# GET /api/monitoring/stats
# Retourne les statistiques temps réel
{
    "message_1_count": 45,
    "message_2_count": 12,
    "total_sent": 57,
    "error_count": 2,
    "daily_limit": 180,
    "remaining": 123,
    "alert_level": "ok",
    "interaction_rate": 0.267,
    "remaining_capacity": 97,
    "is_blocked": false,
    "last_sync": "2024-12-09T14:30:00Z"
}

# GET /api/monitoring/history?days=7
# Retourne l'historique des 7 derniers jours
[
    {"date": "2024-12-09", "message_1": 45, "message_2": 12, "errors": 2},
    {"date": "2024-12-08", "message_1": 120, "message_2": 35, "errors": 5},
    ...
]

# GET /api/monitoring/errors?limit=10
# Retourne les dernières erreurs
[
    {"timestamp": "...", "message_id": 123, "error": "..."},
    ...
]
```

#### 3. Redis Keys Structure

```
whatsapp:daily:{YYYY-MM-DD}:message_1    # Compteur message_1
whatsapp:daily:{YYYY-MM-DD}:message_2    # Compteur message_2
whatsapp:daily:{YYYY-MM-DD}:errors       # Compteur erreurs
whatsapp:daily:{YYYY-MM-DD}:last_sync    # Timestamp dernière sync
whatsapp:blocked                          # Flag de blocage (TTL jusqu'à minuit)
```

### Frontend Components

#### 1. Monitoring Page (`frontend/src/app/dashboard/monitoring/page.tsx`)

Page principale de monitoring avec :
- Jauge circulaire (messages/limite)
- Cartes de statistiques (message_1, message_2, erreurs)
- Carte capacité restante
- Graphique historique 7 jours
- Liste des erreurs récentes

#### 2. useMonitoring Hook (`frontend/src/hooks/useMonitoring.ts`)

Hook React Query pour récupérer les données de monitoring avec auto-refresh.

```typescript
interface MonitoringStats {
    message_1_count: number;
    message_2_count: number;
    total_sent: number;
    error_count: number;
    daily_limit: number;
    remaining: number;
    alert_level: 'ok' | 'attention' | 'danger' | 'blocked';
    interaction_rate: number;
    remaining_capacity: number;
    is_blocked: boolean;
}

function useMonitoring(refreshInterval: number = 10000): {
    stats: MonitoringStats | undefined;
    history: DailyHistory[];
    errors: RecentError[];
    isLoading: boolean;
}
```

#### 3. Alert Level Badge Component

Composant réutilisable pour afficher le niveau d'alerte.

```typescript
interface AlertBadgeProps {
    level: 'ok' | 'attention' | 'danger' | 'blocked';
    showLabel?: boolean;
}
```

## Data Models

### Supabase Tables

#### Table `daily_message_stats`

```sql
CREATE TABLE daily_message_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    message_1_count INTEGER DEFAULT 0,
    message_2_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_daily_stats_date ON daily_message_stats(date);
```

#### Table `message_errors` (extension de la table existante ou nouvelle)

```sql
CREATE TABLE message_errors (
    id SERIAL PRIMARY KEY,
    message_id INTEGER REFERENCES messages(id) ON DELETE SET NULL,
    error_code VARCHAR(100),
    error_message TEXT,
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_message_errors_occurred ON message_errors(occurred_at);
```

### TypeScript Types

```typescript
interface DailyStats {
    date: string;
    message_1_count: number;
    message_2_count: number;
    error_count: number;
}

interface AlertLevel {
    level: 'ok' | 'attention' | 'danger' | 'blocked';
    percentage: number;
    message: string;
}

interface RemainingCapacity {
    contacts: number;
    messages: number;
    warning: boolean;
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Counter Increment Consistency

*For any* message successfully sent via Wassenger API, the corresponding Redis counter (message_1 or message_2) SHALL be incremented by exactly 1, and the total_sent SHALL equal message_1_count + message_2_count.

**Validates: Requirements 1.1, 1.2**

### Property 2: Daily Limit Blocking

*For any* Daily_Message_Counter value >= 180, all subsequent calls to `can_send_message()` SHALL return `(False, "daily_limit_reached")` until the counter is reset.

**Validates: Requirements 2.2, 2.3**

### Property 3: Alert Level Calculation

*For any* Daily_Message_Counter value N:
- If 0 <= N <= 135, alert_level SHALL be "ok"
- If 136 <= N <= 162, alert_level SHALL be "attention"
- If 163 <= N <= 180, alert_level SHALL be "danger"
- If N > 180, alert_level SHALL be "blocked"

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

### Property 4: Remaining Capacity Formula

*For any* combination of messages_sent (S) and interaction_rate (R) where R >= 0, the remaining_capacity SHALL equal floor((180 - S) / (1 + R)), and SHALL never be negative.

**Validates: Requirements 5.1**

### Property 5: Error Rate Alert

*For any* combination of total_sent (T) and error_count (E) where T > 0, if E/T > 0.10 then the error_rate_warning SHALL be true.

**Validates: Requirements 6.2**

### Property 6: Persistence Round-Trip

*For any* daily statistics persisted to Supabase, querying the same date SHALL return identical values for message_1_count, message_2_count, and error_count.

**Validates: Requirements 1.4, 7.4**

### Property 7: Navigation Badge Threshold

*For any* Daily_Message_Counter value N, the navigation badge SHALL be visible if and only if N > 135.

**Validates: Requirements 8.2**

### Property 8: Authentication Required

*For any* request to `/api/monitoring/*` endpoints without a valid JWT token, the response SHALL be HTTP 401 Unauthorized.

**Validates: Requirements 8.4**

## Error Handling

### Redis Connection Errors

- Si Redis est indisponible, le service tente de récupérer les compteurs depuis Supabase
- Les erreurs de connexion sont loggées mais ne bloquent pas l'envoi (fail-open pour éviter de bloquer les campagnes)
- Un flag `redis_available` est maintenu pour informer le dashboard

### Supabase Sync Errors

- Les erreurs de sync sont loggées et retentées à la prochaine heure
- Le dashboard affiche un avertissement si la dernière sync date de plus de 2 heures

### Counter Overflow Protection

- Les compteurs Redis utilisent INCR qui est atomique
- Un TTL de 48h est appliqué aux clés pour éviter l'accumulation

## Testing Strategy

### Unit Tests

- Tests des calculs (alert_level, remaining_capacity, interaction_rate)
- Tests des validations (can_send_message avec différentes valeurs)
- Tests des formatages de réponse API

### Property-Based Tests (Hypothesis)

Le projet utilise **Hypothesis** pour les tests property-based en Python et **fast-check** pour TypeScript.

Chaque propriété de correction sera implémentée comme un test property-based avec :
- Minimum 100 itérations par test
- Générateurs intelligents pour les valeurs de compteurs (0-200)
- Tag explicite référençant la propriété du design document

Format du tag : `**Feature: whatsapp-monitoring, Property {number}: {property_text}**`

### Integration Tests

- Test du flux complet : envoi message → incrémentation → vérification limite
- Test de la synchronisation Redis ↔ Supabase
- Test du reset à minuit (avec mock du temps)

### Frontend Tests

- Tests des composants avec React Testing Library
- Tests du hook useMonitoring avec MSW pour mocker l'API
- Tests visuels des différents états d'alerte
