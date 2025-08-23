# Manual Branch Protection Setup (Single Developer)

**⚠️ CRITICAL: This setup prevents AI agents from bypassing security scans**

Since you're the only developer, we'll set up protection **without required reviews** but **with mandatory security checks**.

---

## 🚀 Quick Setup

### Option 1: GitHub CLI (Automated)

```bash
# Install GitHub CLI if not installed
brew install gh  # macOS
# or visit: https://cli.github.com/

# Authenticate
gh auth login

# Run automated setup
./scripts/setup-branch-protection.sh
```

### Option 2: Manual Setup (Web Interface)

1. **Go to your repository on GitHub**

   - Navigate to: `https://github.com/[USERNAME]/Orchestra/settings/branches`

2. **Add protection for `main` branch:**

   - Click "Add branch protection rule"
   - Branch name pattern: `main`
   - **☑️ Require status checks to pass before merging**
     - ☑️ Require branches to be up to date before merging
     - Add these required status checks:
       - `Test Suite`
       - `Security & Quality Gates`
       - `Docker Build & Security`
   - **☐ Require a pull request before merging** (UNCHECKED - single developer)
   - **☐ Require review from code owners** (UNCHECKED - single developer)
   - **☑️ Restrict pushes that create files larger than 100 MB**
   - **☐ Allow force pushes** (UNCHECKED)
   - **☐ Allow deletions** (UNCHECKED)
   - Click "Create"

3. **Add protection for `develop` branch (if it exists):**
   - Click "Add branch protection rule"
   - Branch name pattern: `develop`
   - Same settings as main branch above

---

## 🔍 Verify Protection is Working

### Test 1: Direct Push Should Fail

```bash
# Make a small change
echo "# Test" >> README.md
git add README.md
git commit -m "Test direct push"

# This should FAIL with protection error
git push origin main
```

**Expected:** `remote: error: GH006: Protected branch update failed`

### Test 2: PR Workflow Should Require Checks

```bash
# Create feature branch
git checkout -b test-security-gates
echo "# Test change" >> README.md
git add README.md
git commit -m "Test security gates"
git push origin test-security-gates

# Create PR via web interface or CLI
gh pr create --title "Test security gates" --body "Testing that security scans are required"
```

**Expected:** PR shows required status checks that must pass before merge

### Test 3: Failing Security Scan Should Block Merge

```bash
# Create a branch with security issue
git checkout -b test-security-failure
echo 'API_KEY = "sk-1234567890abcdef"' > test_secret.py
git add test_secret.py
git commit -m "Add fake secret (should fail security scan)"
git push origin test-security-failure

# Create PR
gh pr create --title "Test security failure" --body "This should fail Bandit scan"
```

**Expected:** Security scan fails, merge blocked until fixed

---

## 🎯 What This Achieves

### ✅ Protection Enabled:

- **Status checks REQUIRED:** All three CI jobs must pass
- **No direct pushes:** Forces PR workflow even for solo developer
- **Security scans BLOCKING:** Bandit, Safety, Trivy must all pass
- **No bypass possible:** Even you as admin cannot bypass (recommended)

### ✅ Single Developer Friendly:

- **No required reviews:** You can merge your own PRs
- **No conversation resolution required:** Merge when ready
- **Admin enforcement disabled:** You retain control if needed

### ✅ AI Agent Protection:

- **Cannot bypass security:** All commits must pass security scans
- **Cannot direct push:** Must go through CI validation
- **Cannot merge failing tests:** Status checks prevent bad code

---

## 🚨 Troubleshooting

### Status Checks Not Appearing

1. **Push a commit** to trigger CI pipeline first
2. **Check CI job names** match exactly:
   - `Test Suite`
   - `Security & Quality Gates`
   - `Docker Build & Security`
3. **Wait for CI to complete** - status checks appear after first run

### "Status check has not run" Error

- Make sure you've **pushed commits** to trigger the CI pipeline
- Check that **job names in CI** match the required status checks
- Verify **CI is actually running** in the Actions tab

### Still Can Push to Main

- Check **branch protection rules** are saved correctly
- Verify **branch name pattern** is exact: `main` (not `master`)
- Make sure you're pushing to the **correct branch** name

### Security Scans Not Blocking

- Verify your **latest changes to CI** are on the branch you're testing
- Check that **continue-on-error** has been removed from CI jobs
- Look at **CI logs** to see if scans are actually running

---

## 🔧 Status Check Commands

```bash
# Check current protection status
./scripts/setup-branch-protection.sh --status

# Test security scans locally
poetry install  # Install security tools
poetry run bandit -r src/
poetry run safety scan

# Test full CI pipeline locally
make ci
```

---

## ❓ FAQ

**Q: Can I still push directly in emergencies?**
A: No, and that's the point! This prevents AI agents (and accidents) from bypassing security. Use PRs for all changes.

**Q: What if CI is broken?**
A: You can temporarily disable branch protection, fix CI, then re-enable protection. But this should be rare.

**Q: Can I approve my own PRs?**
A: Yes! No reviews are required. You just need the status checks to pass.

**Q: What about hotfixes?**
A: Create a hotfix branch, ensure it passes security scans, then merge via PR. Security scans are non-negotiable.

---

**🎉 Once set up, AI agents cannot bypass your security controls!**
