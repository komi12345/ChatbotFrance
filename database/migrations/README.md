# Database Migrations

This folder contains SQL migration scripts for updating the database schema.

## Migration Files

| File | Description |
|------|-------------|
| `001_add_whatsapp_verification.sql` | Adds WhatsApp verification columns to contacts table |

## Running Migrations

### For Existing Databases

Run the migration scripts in order against your Supabase database:

```sql
-- In Supabase SQL Editor, run:
\i 001_add_whatsapp_verification.sql
```

Or copy and paste the contents of each migration file into the Supabase SQL Editor.

### For New Installations

New installations should use the main `schema.sql` file which includes all columns.

## Migration Naming Convention

Migrations are numbered sequentially: `NNN_description.sql`

- `001` - First migration
- `002` - Second migration
- etc.
