# Git basics, part 1: commits and branches

Git stores snapshots of a project, called commits. Each commit points to its parent, which makes a chain of history. This note covers the local side. For remotes and updating a branch, see [[Git basics - part 2]].

## Core commands

```bash
git init
git add lab2/main.c
git commit -m "Add ring buffer for UART input"
git log --oneline
```

- `git init`: creates the `.git` folder in the current directory.
- `git add <file>`: stages a file for the next commit.
- `git commit -m "<message>"`: saves the staged changes as a commit.
- `git log --oneline`: one line per commit, newest first.

## Branches

A branch is a movable label on a commit. Make one for each feature so `main` stays clean.

```bash
git switch -c feature/login
```

`-c` creates the branch and switches to it. Without `-c`, `git switch feature/login` only switches to an existing branch.

## Commit message rules I use

1. First line: 50 characters or fewer, imperative mood ("Add", not "Added").
2. Blank line.
3. Body, if needed: why the change was made, wrapped at 72 characters.

## Undoing (safe ones only)

- `git restore <file>`: throw away unstaged changes in one file. This deletes the changes permanently, so check with `git diff` first.
- `git restore --staged <file>`: unstage a file, keep the changes.
