# Lab Notes Manager

Manage a `geno-tools/labnotes/` directory for the current project.

## Input

The user provides a subcommand as `$ARGUMENTS`.

## Subcommands

### `create`

Initialize the lab notes structure in the current working directory:

1. Create the directory `geno-tools/labnotes/` (and parents if needed)
2. Create `geno-tools/labnotes/tasks.md` with this template:

```markdown
# Tasks

## Active

## Backlog

## Done
```

3. Create `geno-tools/labnotes/notes.md` with this template:

```markdown
# Lab Notes
```

4. Create the directory `geno-tools/labnotes/plans/`

5. Confirm to the user that the lab notes directory was created and list the files.

If `geno-tools/labnotes/` already exists, warn the user and do NOT overwrite existing files.

### `add-task: <description>`

Add a new task to `geno-tools/labnotes/tasks.md`:

1. Read the current `tasks.md`
2. Add `- [ ] <description>` as a new line under the `## Backlog` section
3. Confirm the task was added

### `do-task: <description>`

Move a task from Backlog to Active:

1. Read `tasks.md`
2. Find the matching task in Backlog (fuzzy match on description)
3. Move it under `## Active`
4. Confirm the change

### `done-task: <description>`

Mark a task as done:

1. Read `tasks.md`
2. Find the matching task in Active or Backlog (fuzzy match)
3. Change `- [ ]` to `- [x]` and move it under `## Done`
4. Confirm the change

### `note: <text>`

Append a timestamped note to `geno-tools/labnotes/notes.md`:

1. Read the current `notes.md`
2. Append a new entry with format:
   ```
   ## YYYY-MM-DD HH:MM
   <text>
   ```
3. Confirm the note was added
