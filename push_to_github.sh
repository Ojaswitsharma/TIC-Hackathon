#!/bin/bash

# Git Commands to Replace Combined Branch with Current Directory
# ============================================================

# Note: Run these commands manually in your terminal
# Make sure you have git configured and authenticated with GitHub

echo "🚀 Preparing to push current directory to GitHub combined branch"
echo "==============================================================="

# Step 1: Initialize git if not already done
# git init

# Step 2: Add the GitHub remote (replace with your actual repo URL)
# git remote add origin https://github.com/Ojaswitsharma/TIC-Hackathon.git
# OR if already added:
# git remote set-url origin https://github.com/Ojaswitsharma/TIC-Hackathon.git

# Step 3: Fetch the latest from remote
echo "📥 Fetching latest from remote..."
git fetch origin

# Step 4: Create and switch to combined branch (or switch if exists)
echo "🌿 Switching to combined branch..."
git checkout -B combined

# Step 5: Remove all existing files from the branch
echo "🗑️ Removing existing files..."
git rm -rf .
git clean -fd

# Step 6: Copy all files from current directory
echo "📂 Adding current directory files..."
git add .

# Step 7: Commit the changes
echo "💾 Committing changes..."
git commit -m "Replace combined branch with simplified TIC system

- Removed universal solution generator (solution.py)
- Direct company-specific routing (Amazon + Apple agents)
- 6-question structured conversation flow
- Enhanced company detection from product mentions
- Simplified workflow: Conversation → Company Agent → Direct Response
- Added comprehensive JSON conversation logging
- Robust error handling and fallback extraction"

# Step 8: Force push to combined branch (WARNING: This will overwrite everything)
echo "🚀 Pushing to GitHub..."
git push -f origin combined

echo "✅ Successfully pushed current directory to combined branch!"
echo "🔗 Repository: https://github.com/Ojaswitsharma/TIC-Hackathon"
echo "🌿 Branch: combined"
