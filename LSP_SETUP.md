# LSP (Language Server Protocol) Setup

**Date**: 2025-12-26  
**Status**: ✅ All LSP servers installed and configured

---

## Overview

This project uses multiple programming languages. LSP servers provide IDE features like:
- ✅ Autocompletion
- ✅ Type checking
- ✅ Go to definition
- ✅ Find references
- ✅ Linting errors/warnings
- ✅ Refactoring support

---

## Languages Used in This Project

| Language | File Count | LSP Server |
|----------|-----------|------------|
| **Python** | 22 files | pylsp + pyright |
| **TypeScript/TSX** | 29 files | typescript-language-server |
| **JavaScript** | 9 files | typescript-language-server (also handles JS) |
| **JSON** | 676 files | Built-in (most editors) |
| **Markdown** | 77 files | Built-in (most editors) |
| **YAML** | 7 files | yaml-language-server |
| **Shell/Bash** | 12 files | bash-language-server |

---

## Installed LSP Servers

### 1. Python LSP (`pylsp`)

**Location**: `backend/venv/bin/pylsp`  
**Version**: 1.14.0  
**Scope**: Backend Python code

**Features**:
- Autocompletion (via Jedi)
- Linting (pylint, flake8, pycodestyle, pyflakes)
- Formatting (autopep8, yapf, black)
- Code navigation
- Refactoring (via rope)

**Configuration**: Automatically uses `backend/venv` virtual environment

**Installed Plugins**:
- `jedi` - Autocompletion and navigation
- `pylint` - Advanced linting
- `flake8` - Style checking
- `pycodestyle` - PEP 8 checking
- `pyflakes` - Error detection
- `autopep8` - Auto-formatting
- `yapf` - Code formatter
- `rope` - Refactoring support

---

### 2. Pyright (Python Type Checker)

**Location**: `backend/venv/bin/pyright`  
**Version**: 1.1.407  
**Scope**: Backend Python type checking

**Features**:
- Static type checking
- Type inference
- Fast performance
- Type hints validation

**Configuration**: Works alongside pylsp for enhanced type checking

---

### 3. TypeScript Language Server

**Location**: `frontend/node_modules/.bin/typescript-language-server`  
**Version**: 5.1.3  
**Scope**: Frontend TypeScript/JavaScript/TSX/JSX

**Features**:
- TypeScript/JavaScript autocompletion
- Type checking
- Imports management
- Refactoring
- IntelliSense

**TypeScript Compiler**:
- `tsc` version: 5.9.3
- Config: `frontend/tsconfig.json`

---

### 4. ESLint

**Location**: `frontend/node_modules/.bin/eslint`  
**Version**: 9.39.2  
**Scope**: JavaScript/TypeScript linting

**Features**:
- Code quality checks
- Style enforcement
- Best practices validation
- Next.js specific rules (via eslint-config-next)

**Configuration**: `frontend/eslint.config.mjs`

---

### 5. YAML Language Server

**Location**: `~/.local/state/fnm_multishells/.../bin/yaml-language-server` (global)  
**Scope**: YAML configuration files

**Features**:
- YAML syntax validation
- Schema validation
- Autocompletion for known schemas
- Formatting

**Used For**:
- GitHub Actions (`.github/workflows/*.yml`)
- Backend deployment configs (`backend/*.yaml`)

---

### 6. Bash Language Server

**Location**: `~/.local/state/fnm_multishells/.../bin/bash-language-server` (global)  
**Scope**: Shell scripts

**Features**:
- Bash syntax checking
- Command completion
- ShellCheck integration
- Documentation on hover

**Used For**:
- `.bifrost/scripts/*.sh` (12 files)

---

## How OpenCode Uses LSP Servers

OpenCode automatically detects and uses LSP servers based on:

1. **Python Files** (`.py`):
   - Uses `backend/venv/bin/pylsp` if found
   - Falls back to system Python LSP

2. **TypeScript/JavaScript Files** (`.ts`, `.tsx`, `.js`, `.jsx`):
   - Uses `frontend/node_modules/.bin/typescript-language-server`
   - Requires `node_modules` to be installed (`npm install`)

3. **Other Files**:
   - YAML: Uses global `yaml-language-server`
   - Bash: Uses global `bash-language-server`
   - JSON/Markdown: Built-in editor support

---

## Troubleshooting

### LSP Not Working for Python

**Check**:
```bash
# Verify pylsp is installed
backend/venv/bin/pylsp --version

# Should output: pylsp v1.14.0
```

**Fix**:
```bash
# Reinstall LSP server
backend/venv/bin/python -m pip install 'python-lsp-server[all]' pyright
```

---

### LSP Not Working for TypeScript

**Check**:
```bash
# Verify TypeScript LSP is installed
cd frontend
npx typescript-language-server --version

# Should output: 5.1.3
```

**Fix**:
```bash
# Reinstall dependencies
cd frontend
npm install

# If still broken, reinstall LSP
npm install --save-dev typescript-language-server
```

---

### LSP Not Working for YAML/Bash

**Check**:
```bash
# Verify global LSP servers
which yaml-language-server
which bash-language-server
```

**Fix**:
```bash
# Install globally
npm install -g yaml-language-server bash-language-server
```

---

## Virtual Environment Setup

### Python (Backend)

The backend uses a virtual environment at `backend/venv`:

```bash
# Activate venv
source backend/venv/bin/activate

# Check Python version
python --version  # Python 3.14.0

# Installed packages
pip list
```

**OpenCode Configuration**: Automatically detects and uses `backend/venv/bin/python`

---

### Node.js (Frontend)

The frontend uses local `node_modules`:

```bash
# Install dependencies
cd frontend
npm install

# Check Node version
node --version  # v22.14.0

# Check TypeScript version
npx tsc --version  # 5.9.3
```

**OpenCode Configuration**: Automatically detects and uses `frontend/node_modules`

---

## Recommended OpenCode Settings

For optimal LSP experience, OpenCode should be configured to:

1. **Use project virtual environments**:
   - Python: `backend/venv/bin/python`
   - Node.js: Automatically uses `frontend/node_modules`

2. **Enable all LSP features**:
   - Autocompletion
   - Type checking
   - Linting
   - Formatting on save

3. **Workspace awareness**:
   - Root: `/Users/eivindjonassen/Documents/GitHub/vmkula`
   - Python projects: `backend/`
   - Node.js projects: `frontend/`, `poc/`

---

## Installation Summary

```bash
# Python LSP (already done)
backend/venv/bin/python -m pip install 'python-lsp-server[all]' pyright

# TypeScript LSP (already done)
cd frontend
npm install --save-dev typescript-language-server

# Global LSP servers (already done)
npm install -g yaml-language-server bash-language-server
```

---

## What Was Fixed

### Before
- ❌ Python LSP: NOT INSTALLED
- ❌ TypeScript LSP: NOT INSTALLED (only TypeScript compiler)
- ❌ YAML LSP: NOT INSTALLED
- ❌ Bash LSP: NOT INSTALLED

### After
- ✅ Python LSP: `pylsp v1.14.0` + plugins
- ✅ Pyright: `1.1.407` for type checking
- ✅ TypeScript LSP: `5.1.3`
- ✅ ESLint: `9.39.2`
- ✅ YAML LSP: Installed globally
- ✅ Bash LSP: Installed globally

---

## Testing LSP

### Test Python LSP
1. Open `backend/src/main.py`
2. Type `fs_manager.` and wait for autocompletion
3. Hover over `FirestoreManager` to see type info
4. Cmd+Click on `FirestoreManager` to go to definition

### Test TypeScript LSP
1. Open `frontend/app/page.tsx`
2. Type `useState` and wait for autocompletion
3. Hover over React components to see types
4. Cmd+Click on imports to go to definition

### Test YAML LSP
1. Open `.github/workflows/backend-test.yml`
2. Edit the file and check for syntax validation
3. Autocompletion should work for YAML keys

### Test Bash LSP
1. Open `.bifrost/scripts/check-dependencies.sh`
2. Type commands and check for completion
3. Syntax errors should be highlighted

---

## Next Steps

If LSP still isn't working after this setup:

1. **Reload OpenCode window** - LSP servers are loaded on startup
2. **Check OpenCode logs** - Look for LSP initialization errors
3. **Verify paths** - Ensure virtual environments exist
4. **Restart OpenCode** - Sometimes a full restart is needed

---

## References

- Python LSP Server: https://github.com/python-lsp/python-lsp-server
- Pyright: https://github.com/microsoft/pyright
- TypeScript Language Server: https://github.com/typescript-language-server/typescript-language-server
- YAML Language Server: https://github.com/redhat-developer/yaml-language-server
- Bash Language Server: https://github.com/bash-lsp/bash-language-server
