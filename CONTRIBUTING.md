# Contributing to Image Processing Gate Checker

Thank you for contributing to the **Image Processing Gate Checker** project. This document outlines our development workflows, code style guidelines, and pull request procedures.

---

## 🛠️ Development Setup

1. **Prerequisites**:
   - Python 3.10+
   - Git
   - VLC Media Player (for local manual stream playback)

2. **Setup Steps**:
   ```powershell
   git clone https://github.com/your-username/image-processing-gate-checker.git
   cd "image-processing-gate-checker"
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install -r requirements-dev.txt   # linting & testing tools
   ```

---

## 🌿 Branching Strategy

We follow a GitFlow / GitHub Flow branching convention:
- `main`: Production-ready, stable releases.
- `develop`: Integration branch for active features.
- `feature/<name>`: New features (e.g., `feature/clahe-illumination`).
- `fix/<name>`: Bug fixes (e.g., `fix/rtsp-reconnect-timeout`).
- `docs/<name>`: Documentation improvements.

---

## 📝 Commit Message Convention

All commits must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```text
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

**Allowed Types**:
- `feat`: A new feature or algorithm enhancement.
- `fix`: A bug fix.
- `docs`: Documentation changes only.
- `style`: Formatting, missing semicolons, etc. (no code change).
- `refactor`: Refactoring production code without changing behavior.
- `test`: Adding or correcting tests.
- `chore`: Build tasks, package manager configs, maintenance.

---

## 🧪 Testing & Code Quality

Before opening a pull request, ensure:
1. **Linting & Formatting**:
   ```powershell
   ruff check src/ tests/
   black --check src/ tests/
   mypy src/
   ```
2. **Automated Tests**:
   ```powershell
   pytest tests/ -v
   ```
3. **Audit Verification**:
   - Verify that your changes do not leak credentials or unmasked camera passwords.
   - Update `CHANGELOG.md` under the `[Unreleased]` section.

---

## 📋 Pull Request Checklist

When submitting a PR, verify:
- [ ] Code follows PEP 8 and project style conventions.
- [ ] Type hints are present on all new public functions and classes.
- [ ] Unit tests are added for new vision logic and state transitions.
- [ ] Documentation and inline comments are updated.
- [ ] [CHANGELOG.md](CHANGELOG.md) reflects the changes made.
- [ ] No local `.env` or sensitive camera credentials are included in the commit.
