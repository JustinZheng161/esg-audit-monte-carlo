# Git Initialization and Push Command Sequence

The commands below reproduce the release structure used for this project. Run them only after replacing paths, repository owner, and names as appropriate. They assume that the public release tree has already passed the data-boundary and credential checks in `REPOSITORY_BOUNDARY.md`.

## 1. Prepare local public and private release trees

```bash
BASE=/absolute/path/to/esg_audit
PUB="$BASE/github_public/esg-audit-monte-carlo"
PRIV="$BASE/github_private/esg-audit-monte-carlo-private"
mkdir -p "$PUB" "$PRIV"
```

Populate `$PUB` using the documented whitelist only. Populate `$PRIV` with the manuscript, full simulation outputs, permitted raw snapshots, audit notes, and a reproducibility snapshot. Never place API keys, `.env` files, or unlicensed commercial data in either tree.

## 2. Initialize and commit the public code repository

```bash
cd "$PUB"
git init -b main
git config user.name "<GitHub-user-name>"
git config user.email "<GitHub-noreply-or-verified-email>"
git add .
git diff --cached --check
git commit -m "Initial reproducible synthetic Monte Carlo package"
```

## 3. Create and push the public GitHub repository

```bash
# Requires GitHub CLI authentication: gh auth login
cd "$PUB"
gh repo create <owner>/esg-audit-monte-carlo \
  --public \
  --source=. \
  --remote=origin \
  --push \
  --description "Synthetic Monte Carlo diagnostics for ESG, audit quality, and investment inefficiency."
```

## 4. Initialize and commit the private archive

```bash
cd "$PRIV"
git init -b main
git config user.name "<GitHub-user-name>"
git config user.email "<GitHub-noreply-or-verified-email>"
git add .
git diff --cached --check
git commit -m "Initial private research archive and full simulation record"
```

## 5. Create and push the private GitHub repository

```bash
cd "$PRIV"
gh repo create <owner>/esg-audit-monte-carlo-private \
  --private \
  --source=. \
  --remote=origin \
  --push \
  --description "Private manuscript, full simulation outputs, and controlled data archive for ESG audit Monte Carlo research."
```

## 6. Verify remote visibility and synchronization

```bash
gh repo view <owner>/esg-audit-monte-carlo --json nameWithOwner,isPrivate,url,defaultBranchRef
gh repo view <owner>/esg-audit-monte-carlo-private --json nameWithOwner,isPrivate,url,defaultBranchRef

git -C "$PUB" status --short
git -C "$PRIV" status --short

gh repo clone <owner>/esg-audit-monte-carlo /tmp/esg-audit-monte-carlo-verify
cd /tmp/esg-audit-monte-carlo-verify
python3 tests/test_pipeline.py
```

The expected verification output is `Pipeline tests passed.` and both working trees should have no uncommitted changes. The public repository must not contain a manuscript, raw data, or restricted vendor data.
