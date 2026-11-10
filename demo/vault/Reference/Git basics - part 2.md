# Git basics, part 2: remotes and updating a branch

This picks up from [[Git basics - part 1]], which covers commits and branches.

## Remotes

A remote is another copy of the repository, usually on GitHub.

```bash
git remote add origin git@github.com:example-user/example-repo.git
git push -u origin feature/login
```

- `git remote add origin <url>`: names the remote `origin`.
- `git push -u origin feature/login`: uploads the branch and sets it to track the remote one. After this, a plain `git push` works on that branch.

## Updating a feature branch with main

This is the step you need when `main` has moved on while you were working. Part 1 created the branch. This is how you bring `main` into it.

1. Fetch the latest remote state (this does not change your files):

```bash
git fetch origin
```

2. Replay your commits on top of the updated `main`:

```bash
git rebase origin/main
```

3. If there are conflicts, fix the files, then run `git add <file>` and `git rebase --continue`.
4. Push again. Because the history changed, you need a force push. Use `--force-with-lease`, which refuses if someone else pushed in the meantime:

```bash
git push --force-with-lease
```

## Merge vs rebase

- `git merge main` creates a new commit that joins the two histories. Nothing is rewritten.
- `git rebase origin/main` rewrites your commits so they sit on top of `main`. The history is a straight line.

Rule I follow: rebase your own unshared branch, never rebase a branch other people are working on.
