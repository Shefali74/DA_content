# To-Do API

A small REST API for managing to-do items, built with **Express 5**, **TypeScript**,
**Prisma** (PostgreSQL), and **zod** for input validation.

## Requirements

- Node.js 20+ (developed against Node 26)
- A PostgreSQL database

## Setup

```bash
# 1. Install dependencies
npm install

# 2. Configure the database connection
cp .env.example .env
# then edit DATABASE_URL in .env

# 3. Generate the Prisma client
npm run prisma:generate

# 4. Apply the database migration
#    (requires a running PostgreSQL instance reachable via DATABASE_URL)
npx prisma migrate deploy
```

> The initial migration is checked in at
> [`db/migrations/`](./db/migrations/). Migrations are stored there (not under
> `scripts/`) via the `migrations.path` setting in
> [`prisma.config.ts`](./prisma.config.ts).

## Running

```bash
npm run dev     # development server with live reload (tsx)
npm run build   # generate Prisma client + compile TypeScript to dist/
npm start       # run the compiled server from dist/
```

The server listens on `http://localhost:3000` (override with `PORT`).

## Data model

`Todo`

| Field         | Type      | Notes                          |
| ------------- | --------- | ------------------------------ |
| `id`          | String    | UUID, primary key              |
| `title`       | String    | required                       |
| `description` | String?   | optional                       |
| `completed`   | Boolean   | defaults to `false`            |
| `createdAt`   | DateTime  | defaults to `now()`            |

## API

| Method | Path          | Description          | Success |
| ------ | ------------- | -------------------- | ------- |
| GET    | `/todos`      | List all todos       | 200     |
| POST   | `/todos`      | Create a todo        | 201     |
| PUT    | `/todos/:id`  | Update a todo        | 200     |
| DELETE | `/todos/:id`  | Delete a todo        | 204     |
| GET    | `/health`     | Health check         | 200     |

### Request bodies

`POST /todos`

```json
{ "title": "Buy milk", "description": "From the store", "completed": false }
```

`title` is required; `description` and `completed` are optional.

`PUT /todos/:id` accepts any subset of `title`, `description`, `completed`
(at least one field is required). `description` may be set to `null` to clear it.

Validation is enforced with zod; invalid requests return `400` with a
`ValidationError` body. Unknown ids return `404`.

## Testing & quality

```bash
npm run lint    # ESLint (typescript-eslint, flat config)
npm test        # Vitest unit tests
```

Tests are co-located next to the source files they cover
(`todo.controller.ts` + `todo.controller.test.ts`,
`todo.schema.ts` + `todo.schema.test.ts`). The controller tests mock the
Prisma client, so no database is required to run them.

## Project layout

```
.
├── db/
│   └── migrations/          # Prisma migrations (initial schema)
├── prisma/
│   └── schema.prisma        # Prisma schema (Todo model)
├── prisma.config.ts         # Prisma config (points migrations at db/migrations)
├── src/
│   ├── app.ts               # Express app factory
│   ├── index.ts             # Server bootstrap
│   ├── prisma-client.ts     # Shared PrismaClient instance
│   ├── todo.controller.ts   # CRUD handlers
│   ├── todo.controller.test.ts
│   ├── todo.routes.ts       # /todos router
│   ├── todo.schema.ts       # zod validation schemas
│   └── todo.schema.test.ts
├── eslint.config.mjs
├── vitest.config.ts
└── tsconfig.json
```
