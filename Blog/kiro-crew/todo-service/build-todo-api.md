# Build To-Do API

## Steps
1. Initialize an Express.js project with TypeScript
2. Set up Prisma with a Postgres connection
3. Create the Todo model (id, title, description, completed, createdAt)
4. Generate Prisma migration in `db/migrations/`
5. Create CRUD routes: GET /todos, POST /todos, PUT /todos/:id, DELETE /todos/:id
6. Add input validation with zod
7. Write unit tests (co-located with source files)
8. Run `npm run lint` and `npm test`
9. If all pass, generate a README.md

## Constraints
- File naming: kebab-case
- Type naming: PascalCase
- Tests live next to source files (e.g., `todo.controller.ts` + `todo.controller.test.ts`)
- Migrations go in `db/migrations/`, NOT `scripts/`
- Always lint before marking a step complete
- Stop and report if any test fails