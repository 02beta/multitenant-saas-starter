#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install dependencies
install_dependencies() {
    print_info "Checking and installing dependencies..."

    # Check for gh CLI
    if ! command_exists gh; then
        print_info "Installing GitHub CLI..."
        if command_exists brew; then
            brew install gh
        elif command_exists apt-get; then
            # For Ubuntu/Debian
            curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
            sudo apt update
            sudo apt install gh
        elif command_exists yum; then
            # For RHEL/CentOS/Fedora
            sudo dnf install 'dnf-command(config-manager)'
            sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
            sudo dnf install gh
        else
            print_error "Could not install GitHub CLI. Please install it manually."
            exit 1
        fi
    fi

    # Check for jq
    if ! command_exists jq; then
        print_info "Installing jq..."
        if command_exists brew; then
            brew install jq
        elif command_exists apt-get; then
            sudo apt-get update && sudo apt-get install -y jq
        elif command_exists yum; then
            sudo yum install -y jq
        else
            print_error "Could not install jq. Please install it manually."
            exit 1
        fi
    fi

    print_success "Dependencies installed successfully"
}

# Function to authenticate GitHub CLI
authenticate_github_cli() {
    print_info "Checking GitHub CLI authentication..."

    # Check if gh is already authenticated
    if gh auth status >/dev/null 2>&1; then
        print_success "GitHub CLI is already authenticated"
        return 0
    fi

    # Try to authenticate using GITHUB_PERSONAL_ACCESS_TOKEN
    if [ -n "${GITHUB_PERSONAL_ACCESS_TOKEN:-}" ]; then
        print_info "Authenticating GitHub CLI with personal access token..."
        echo "$GITHUB_PERSONAL_ACCESS_TOKEN" | gh auth login --with-token

        if gh auth status >/dev/null 2>&1; then
            print_success "GitHub CLI authenticated successfully"
            return 0
        else
            print_error "Failed to authenticate with provided token"
            return 1
        fi
    else
        print_error "GitHub CLI is not authenticated and GITHUB_PERSONAL_ACCESS_TOKEN is not set."
        print_error "Please either run 'gh auth login' manually or set GITHUB_PERSONAL_ACCESS_TOKEN environment variable."
        return 1
    fi
}

# Function to get current version from root package.json
get_current_version() {
    if [ -f "package.json" ]; then
        node -p "require('./package.json').version" 2>/dev/null || echo "0.0.0"
    else
        echo "0.0.0"
    fi
}

# Function to get last release tag
get_last_release_tag() {
    git tag --sort=-version:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -n 1 || echo ""
}

# Function to generate release notes using AI
generate_release_notes() {
	local from_tag=$1
	local to_ref=$2
	local version=$3

	print_info "Generating release notes for v$version..."

	# Get git diff
	local git_diff
	if [ -n "$from_tag" ]; then
		git_diff=$(git log --oneline --pretty=format:"- %s" "$from_tag..$to_ref" 2>/dev/null || echo "")
	else
		git_diff=$(git log --oneline --pretty=format:"- %s" 2>/dev/null || echo "")
	fi

	if [ -z "$git_diff" ]; then
		git_diff="- Initial release"
	fi

	# Create a temporary file with the changes
	local temp_file
	temp_file=$(mktemp)
	cat > "$temp_file" << EOF
Please format the following git commit messages into a professional changelog entry for version $version.

Git commits since last release:
$git_diff

Please format this as a markdown changelog entry with the following structure:
- Start with "## [$version] - $(date +%Y-%m-%d)"
- Group changes into categories like "### Added", "### Changed", "### Fixed", "### Removed" as appropriate
- Make the descriptions more user-friendly and professional
- Remove any internal/technical commit prefixes like "chore:", "feat:", "fix:" etc.
- Focus on user-facing changes and improvements

Return only the markdown changelog entry, nothing else.
EOF

	# Try to use different AI tools in order of preference
	local release_notes

	if command_exists ollama && ollama list | grep -q "llama"; then
		print_info "Using Ollama to generate release notes..."
		release_notes=$(ollama run llama3.2 "$(cat "$temp_file")" 2>/dev/null || echo "")
	elif command_exists openai && [ -n "${OPENAI_API_KEY:-}" ]; then
		print_info "Using OpenAI to generate release notes..."
		release_notes=$(openai api chat.completions.create -m gpt-4 \
			--messages '[{"role": "user", "content": "'"$(sed 's/"/\\"/g' "$temp_file")"'"}]' \
			--max-tokens 1000 2>/dev/null | jq -r '.choices[0].message.content' || echo "")
	elif command_exists curl && [ -n "${OPENAI_API_KEY:-}" ]; then
		print_info "Using OpenAI API to generate release notes..."
		local prompt
		prompt=$(cat "$temp_file" | jq -Rs .)
		release_notes=$(curl -s -X POST "https://api.openai.com/v1/chat/completions" \
			-H "Authorization: Bearer $OPENAI_API_KEY" \
			-H "Content-Type: application/json" \
			-d "{
				\"model\": \"gpt-4\",
				\"messages\": [{\"role\": \"user\", \"content\": $prompt}],
				\"max_tokens\": 1000
			}" | jq -r '.choices[0].message.content' 2>/dev/null || echo "")
	fi

	# Fallback to manual formatting if AI is not available
	if [ -z "$release_notes" ] || [ "$release_notes" = "null" ]; then
		print_warning "AI tools not available, generating basic release notes..."
		release_notes="## [$version] - $(date +%Y-%m-%d)

### Changes
$git_diff"
	fi

	rm -f "$temp_file"
	echo "$release_notes"
}

# Function to update changelog
update_changelog() {
    local version=$1
    local release_notes=$2

    print_info "Updating CHANGELOG.md..."

    local changelog_file="CHANGELOG.md"
    local temp_changelog
    temp_changelog=$(mktemp)

    # Create changelog header if file doesn't exist
    if [ ! -f "$changelog_file" ]; then
        cat > "$changelog_file" << EOF
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

EOF
    fi

    # Insert new release notes at the top (after the header)
    {
        # Keep the header
        head -n 6 "$changelog_file" 2>/dev/null || echo "# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"

        # Add new release notes
        echo "$release_notes"
        echo ""

        # Add existing content (skip header if it exists)
        if [ -f "$changelog_file" ]; then
            tail -n +7 "$changelog_file" 2>/dev/null || true
        fi
    } > "$temp_changelog"

    mv "$temp_changelog" "$changelog_file"
    print_success "Updated CHANGELOG.md"
}

# Function to create GitHub release
create_github_release() {
    local version=$1
    local release_notes=$2

    print_info "Creating GitHub release for v$version..."

    # Ensure GitHub CLI is authenticated
    if ! authenticate_github_cli; then
        return 1
    fi

    # Create the release
    echo "$release_notes" | gh release create "v$version" \
        --title "Release v$version" \
        --notes-file - \
        --latest

    print_success "GitHub release created: v$version"
}

# Function to bump version
bump_version() {
    local version_type=$1
    local current_version
    current_version=$(get_current_version)

    print_info "Current version: $current_version"

    # Parse version parts
    IFS='.' read -ra VERSION_PARTS <<< "$current_version"
    local major=${VERSION_PARTS[0]:-0}
    local minor=${VERSION_PARTS[1]:-0}
    local patch=${VERSION_PARTS[2]:-0}

    # Bump version based on type
    case $version_type in
        "patch")
            patch=$((patch + 1))
            ;;
        "minor")
            minor=$((minor + 1))
            patch=0
            ;;
        "major")
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        *)
            print_error "Invalid version type: $version_type"
            exit 1
            ;;
    esac

    local new_version="$major.$minor.$patch"
    print_info "New version: $new_version"
    echo "$new_version"
}
# Function to update package.json files
update_package_json_files() {
    local new_version=$1

    print_info "Updating package.json files..."

    # Use git ls-files to find tracked package.json files, respecting .gitignore
    git ls-files '*.json' | grep 'package\.json$' | while read -r file; do
        print_info "Updating $file"

        # Use node to update the version in package.json
        node -e "
            const fs = require('fs');
            const path = '$file';
            try {
                const pkg = JSON.parse(fs.readFileSync(path, 'utf8'));
                pkg.version = '$new_version';
                fs.writeFileSync(path, JSON.stringify(pkg, null, 2) + '\n');
                console.log('Updated version in ' + path);
            } catch (error) {
                console.error('Error updating ' + path + ':', error.message);
            }
        "
    done

    print_success "Updated all package.json files"
}

# Function to update pyproject.toml files
update_pyproject_toml_files() {
    local new_version=$1

    print_info "Updating pyproject.toml files..."

    # Use git ls-files to find tracked pyproject.toml files, respecting .gitignore
    git ls-files '*.toml' | grep 'pyproject\.toml$' | while read -r file; do
        print_info "Updating $file"

        # Use Python to update the version in pyproject.toml
        python3 -c "
import sys
import re

try:
    with open('$file', 'r') as f:
        content = f.read()

    # Update version in [project] section
    content = re.sub(
        r'(version\s*=\s*[\"\']).+?([\"\']\s*)',
        r'\g<1>$new_version\g<2>',
        content
    )

    with open('$file', 'w') as f:
        f.write(content)

    print(f'Updated version in $file')
except Exception as e:
    print(f'Error updating $file: {e}', file=sys.stderr)
"
    done
}

# Function to update package.json files
update_package_json_files() {
    local new_version=$1
    print_info "Updating package.json files..."

    # Use git ls-files to find tracked package.json files, respecting .gitignore
    git ls-files '*.json' | grep 'package\.json$' | while read -r file; do
        print_info "Updating $file"

        # Use node to update the version in package.json
        node -e "
            const fs = require('fs');
            const path = '$file';
            try {
                const pkg = JSON.parse(fs.readFileSync(path, 'utf8'));
                pkg.version = '$new_version';
                fs.writeFileSync(path, JSON.stringify(pkg, null, 2) + '\n');
                console.log('Updated version in ' + path);
            } catch (error) {
                console.error('Error updating ' + path + ':', error.message);
            }
        "
    done
}
sync_versions() {
    local current_version
    current_version=$(get_current_version)

    if [ "$current_version" = "0.0.0" ]; then
        print_warning "No root package.json found or version not set. Using 0.0.1 as default."
        current_version="0.0.1"
    fi

    print_info "Syncing all versions to: $current_version"

    update_package_json_files "$current_version"
    update_pyproject_toml_files "$current_version"

    print_success "All versions synced to $current_version"
}

# Function to run precommit tasks
run_precommit() {
    print_info "Running precommit tasks..."

    # Run linting and formatting for all apps
    for app_dir in apps/*/; do
        if [ -d "$app_dir" ] && [ -f "$app_dir/package.json" ]; then
            print_info "Running precommit for $app_dir"
            (cd "$app_dir" && pnpm run precommit 2>/dev/null || true)
        fi
    done

    print_success "Precommit tasks completed"
}

# Function to commit and push changes
commit_and_push() {
    local version_type=$1
    local new_version=$2

    print_info "Committing and pushing changes..."

    git add .
    git commit -m "chore: release:$version_type - bump to v$new_version"
    git tag "v$new_version"
    git push
    git push --tags

    print_success "Changes committed and pushed with tag v$new_version"
}

# Main functions
bump_patch() {
    local new_version
    new_version=$(bump_version "patch")
    update_package_json_files "$new_version"
    update_pyproject_toml_files "$new_version"
    print_success "Bumped patch version to $new_version"
}

bump_minor() {
    local new_version
    new_version=$(bump_version "minor")
    update_package_json_files "$new_version"
    update_pyproject_toml_files "$new_version"
    print_success "Bumped minor version to $new_version"
}

bump_major() {
    local new_version
    new_version=$(bump_version "major")
    update_package_json_files "$new_version"
    update_pyproject_toml_files "$new_version"
    print_success "Bumped major version to $new_version"
}

release_patch() {
    print_info "Starting patch release..."
    install_dependencies
    run_precommit
    local new_version
    new_version=$(bump_version "patch")
    local last_tag
    last_tag=$(get_last_release_tag)
    local release_notes
    release_notes=$(generate_release_notes "$last_tag" "HEAD" "$new_version")

    update_package_json_files "$new_version"
    update_pyproject_toml_files "$new_version"
    update_changelog "$new_version" "$release_notes"

    commit_and_push "patch" "$new_version"
    create_github_release "$new_version" "$release_notes"

    print_success "Patch release completed: v$new_version"
}

release_minor() {
    print_info "Starting minor release..."
    install_dependencies
    run_precommit
    local new_version
    new_version=$(bump_version "minor")
    local last_tag
    last_tag=$(get_last_release_tag)
    local release_notes
    release_notes=$(generate_release_notes "$last_tag" "HEAD" "$new_version")

    update_package_json_files "$new_version"
    update_pyproject_toml_files "$new_version"
    update_changelog "$new_version" "$release_notes"

    commit_and_push "minor" "$new_version"
    create_github_release "$new_version" "$release_notes"

    print_success "Minor release completed: v$new_version"
}

release_major() {
    print_info "Starting major release..."
    install_dependencies
    run_precommit
    local new_version
    new_version=$(bump_version "major")
    local last_tag
    last_tag=$(get_last_release_tag)
    local release_notes
    release_notes=$(generate_release_notes "$last_tag" "HEAD" "$new_version")

    update_package_json_files "$new_version"
    update_pyproject_toml_files "$new_version"
    update_changelog "$new_version" "$release_notes"

    commit_and_push "major" "$new_version"
    create_github_release "$new_version" "$release_notes"

    print_success "Major release completed: v$new_version"
}

# Command handling
case "${1:-}" in
    "release-patch") release_patch ;;
    "release-minor") release_minor ;;
    "release-major") release_major ;;
    "bump-patch") bump_patch ;;
    "bump-minor") bump_minor ;;
    "bump-major") bump_major ;;
    "sync-versions") sync_versions ;;
    *)
        echo "Usage: $0 {release-patch|release-minor|release-major|bump-patch|bump-minor|bump-major|sync-versions}"
        echo
        echo "Commands:"
        echo "  release-patch   - Run precommit, bump patch version, generate release notes, commit, push, and create GitHub release"
        echo "  release-minor   - Run precommit, bump minor version, generate release notes, commit, push, and create GitHub release"
        echo "  release-major   - Run precommit, bump major version, generate release notes, commit, push, and create GitHub release"
        echo "  bump-patch      - Bump patch version only (no commit)"
        echo "  bump-minor      - Bump minor version only (no commit)"
        echo "  bump-major      - Bump major version only (no commit)"
        echo "  sync-versions   - Sync all package.json and pyproject.toml versions to root version"
        echo
        echo "Required Environment Variables:"
        echo "  GITHUB_PERSONAL_ACCESS_TOKEN - GitHub personal access token for GitHub CLI authentication"
        echo
        echo "Optional Environment Variables:"
        echo "  OPENAI_API_KEY  - OpenAI API key for AI-generated release notes"
        echo
        echo "Dependencies:"
        echo "  - GitHub CLI (gh) - automatically installed if missing"
        echo "  - jq - automatically installed if missing"
        exit 1
        ;;
esac
