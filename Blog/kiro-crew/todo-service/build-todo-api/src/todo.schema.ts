import { z } from 'zod';

// Schema for creating a Todo. `title` is required; the rest are optional.
export const CreateTodoSchema = z.object({
  title: z.string().trim().min(1, 'title is required').max(255),
  description: z.string().trim().max(2000).optional(),
  completed: z.boolean().optional(),
});

// Schema for updating a Todo. All fields optional, but at least one required.
export const UpdateTodoSchema = z
  .object({
    title: z.string().trim().min(1, 'title must not be empty').max(255).optional(),
    description: z.string().trim().max(2000).nullable().optional(),
    completed: z.boolean().optional(),
  })
  .refine((data) => Object.keys(data).length > 0, {
    message: 'at least one field must be provided',
  });

// Route param schema: Todo ids are UUIDs.
export const TodoIdParamSchema = z.object({
  id: z.string().uuid('id must be a valid UUID'),
});

export type CreateTodoInput = z.infer<typeof CreateTodoSchema>;
export type UpdateTodoInput = z.infer<typeof UpdateTodoSchema>;
