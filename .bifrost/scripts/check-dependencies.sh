#!/bin/bash

# Checks and updates dependency tracking for the project
# Usage: check-dependencies.sh [--update]

PROJECT_ROOT="."
DEPS_FILE=".bifrost/dependencies.json"
UPDATE_MODE=false

if [[ "$1" == "--update" ]]; then
    UPDATE_MODE=true
fi

echo "🔍 Checking project dependencies..."

# Create dependencies.json if it doesn't exist
if [[ ! -f "$DEPS_FILE" ]]; then
    echo "📝 Creating initial dependencies.json"
    mkdir -p "$(dirname "$DEPS_FILE")"
    cat > "$DEPS_FILE" << 'EOF'
{
  "lastUpdated": "",
  "packageManagers": {},
  "frameworks": {},
  "databases": {},
  "testing": {},
  "cicd": {},
  "infrastructure": {}
}
EOF
fi

# Detect package managers and frameworks
detect_tech_stack() {
    local tech_stack="{}"

    # Package managers
    if [[ -f "package.json" ]]; then
        local pkg_manager="npm"
        [[ -f "yarn.lock" ]] && pkg_manager="yarn"
        [[ -f "pnpm-lock.yaml" ]] && pkg_manager="pnpm"

        tech_stack=$(echo "$tech_stack" | jq --arg pm "$pkg_manager" '.packageManagers.node = $pm')

        # Extract main frameworks from package.json
        if command -v jq >/dev/null 2>&1; then
            local frameworks=$(jq -r '(.dependencies // {}) + (.devDependencies // {}) | keys[]' package.json 2>/dev/null | grep -E '^(react|vue|angular|next|nuxt|express|fastify|nest)' | head -5 | jq -R . | jq -s .)
            tech_stack=$(echo "$tech_stack" | jq --argjson frameworks "$frameworks" '.frameworks.node = $frameworks')
        fi
    fi

    if [[ -f "requirements.txt" || -f "pyproject.toml" ]]; then
        tech_stack=$(echo "$tech_stack" | jq '.packageManagers.python = "pip"')
    fi

    if [[ -f "Cargo.toml" ]]; then
        tech_stack=$(echo "$tech_stack" | jq '.packageManagers.rust = "cargo"')
    fi

    if [[ -f "go.mod" ]]; then
        tech_stack=$(echo "$tech_stack" | jq '.packageManagers.go = "go mod"')
    fi

    # Testing frameworks
    if [[ -f "package.json" ]] && command -v jq >/dev/null 2>&1; then
        local test_frameworks=$(jq -r '(.dependencies // {}) + (.devDependencies // {}) | keys[]' package.json 2>/dev/null | grep -E '^(jest|vitest|mocha|cypress|playwright)' | head -3 | jq -R . | jq -s .)
        tech_stack=$(echo "$tech_stack" | jq --argjson testing "$test_frameworks" '.testing.frameworks = $testing')
    fi

    # CI/CD
    if [[ -d ".github/workflows" ]]; then
        tech_stack=$(echo "$tech_stack" | jq '.cicd.github = true')
    fi

    if [[ -f ".gitlab-ci.yml" ]]; then
        tech_stack=$(echo "$tech_stack" | jq '.cicd.gitlab = true')
    fi

    echo "$tech_stack"
}

# Get current tech stack
CURRENT_STACK=$(detect_tech_stack)

if [[ "$UPDATE_MODE" == true ]]; then
    echo "📝 Updating dependencies.json..."

    # Update the dependencies file
    jq --arg date "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
       --argjson stack "$CURRENT_STACK" \
       '.lastUpdated = $date | .packageManagers = $stack.packageManagers | .frameworks = $stack.frameworks | .testing = $stack.testing | .cicd = $stack.cicd' \
       "$DEPS_FILE" > "${DEPS_FILE}.tmp" && mv "${DEPS_FILE}.tmp" "$DEPS_FILE"

    echo "✅ Dependencies updated successfully"
else
    echo "📊 Current tech stack:"
    echo "$CURRENT_STACK" | jq .

    echo
    echo "💡 Run with --update to save this information to $DEPS_FILE"
fi