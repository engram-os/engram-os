#!/bin/bash

# 1. g-commit: Stages changes and asks AI for a message
function g-commit() {
    # Check if there are staged changes
    if git diff --cached --quiet; then
        echo "No staged changes! Run 'git add' first."
        return 1
    fi

    echo "Engram is reading your changes..."
    
    # Capture diff (Disable color to avoid weird symbols)
    DIFF=$(git diff --cached --no-color)
    
    # Send to Docker (Escape quotes safely using jq)
    MSG=$(curl -s -X POST http://localhost:8000/api/git/commit-msg \
        -H "Content-Type: application/json" \
        -d "$(jq -n --arg diff "$DIFF" '{diff: $diff}')")
    
    # Extract message from JSON response (QUOTED to prevent breakage)
    COMMIT_MSG=$(echo "$MSG" | jq -r '.message')
    
    # Check if we got a valid message or an error
    if [[ "$COMMIT_MSG" == "null" || -z "$COMMIT_MSG" ]]; then
        echo "Error generating message. Server response:"
        echo "$MSG"
        return 1
    fi
    
    printf "\nSuggested Commit Message:\n"
    printf "%s\n\n" "$COMMIT_MSG"
    
    printf "Do you want to use this? (y/n/e to edit): "
    read -r reply < /dev/tty
    if [[ "$reply" == "y" ]]; then
        git commit -m "$COMMIT_MSG"
    elif [[ "$reply" == "e" ]]; then
        git commit -m "$COMMIT_MSG" -e
    else
        echo "Aborted."
    fi
}

# 2. g-pr: Generates a PR description from main branch
function g-pr() {
    echo "Analyzing branch against main..."
    
    # Diff against main (assuming 'main' is your base)
    DIFF=$(git diff main...HEAD --no-color)
    
    RESPONSE=$(curl -s -X POST http://localhost:8000/api/git/pr-description \
        -H "Content-Type: application/json" \
        -d "$(jq -n --arg diff "$DIFF" '{diff: $diff}')")
        
    echo "$RESPONSE" | jq -r '.markdown'
}

# 3. g-check: Scans staged files for secrets
function g-check() {
    echo "Scanning staged files for leaks..."
    DIFF=$(git diff --cached --no-color)
    
    RESPONSE=$(curl -s -X POST http://localhost:8000/api/git/safety-check \
        -H "Content-Type: application/json" \
        -d "$(jq -n --arg diff "$DIFF" '{diff: $diff}')")
        
    SAFE=$(echo "$RESPONSE" | jq -r '.safe')
    
    if [[ "$SAFE" == "true" ]]; then
        echo "No secrets detected. Safe to push."
    else
        LEAKS=$(echo "$RESPONSE" | jq -r '.leaks[]')
        echo "WARNING: POSSIBLE SECRET LEAK DETECTED!"
        echo "Found potential: $LEAKS"
        echo "Check your diff before pushing!"
    fi
}