# Git Repository Setup Script for Traffic Analysis Project
# This script automates the Git initialization and push process

Write-Host "=== Git Repository Setup for Traffic Analysis Project ===" -ForegroundColor Cyan
Write-Host ""

# Check if Git is installed
try {
    $gitVersion = git --version
    Write-Host "✓ Git is installed: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Git is not installed!" -ForegroundColor Red
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "After installation, restart PowerShell and run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Check if already a Git repository
if (Test-Path ".git") {
    Write-Host "⚠ This directory is already a Git repository." -ForegroundColor Yellow
    $continue = Read-Host "Do you want to continue? This will add and push changes. (y/n)"
    if ($continue -ne "y") {
        Write-Host "Setup cancelled." -ForegroundColor Yellow
        exit 0
    }
} else {
    Write-Host "Initializing Git repository..." -ForegroundColor Cyan
    git init
    git branch -M main
    Write-Host "✓ Repository initialized" -ForegroundColor Green
}

Write-Host ""

# Configure Git user (if not already configured)
$userName = git config --global user.name
$userEmail = git config --global user.email

if (-not $userName) {
    Write-Host "Git user name not configured." -ForegroundColor Yellow
    $userName = Read-Host "Enter your name (for Git commits)"
    git config --global user.name "$userName"
}

if (-not $userEmail) {
    Write-Host "Git user email not configured." -ForegroundColor Yellow
    $userEmail = Read-Host "Enter your email (should match GitHub email)"
    git config --global user.email "$userEmail"
}

Write-Host "✓ Git configured for: $userName <$userEmail>" -ForegroundColor Green
Write-Host ""

# Add files
Write-Host "Adding files to Git..." -ForegroundColor Cyan
git add .

# Show status
Write-Host ""
Write-Host "Files to be committed:" -ForegroundColor Cyan
git status --short

Write-Host ""
$proceed = Read-Host "Proceed with commit? (y/n)"
if ($proceed -ne "y") {
    Write-Host "Setup cancelled." -ForegroundColor Yellow
    exit 0
}

# Commit
Write-Host ""
Write-Host "Creating initial commit..." -ForegroundColor Cyan
git commit -m "Initial commit: Real-Time Traffic Analysis and Prediction System

- Complete traffic analysis and prediction system
- IoT sensor simulation and data pipeline
- Machine learning models for traffic prediction
- FastAPI backend and Streamlit dashboard
- Docker containerization support
- Comprehensive documentation"

Write-Host "✓ Initial commit created" -ForegroundColor Green
Write-Host ""

# Add remote (if not already added)
$remoteUrl = "https://github.com/keshavabc12/traffic.git"
$existingRemote = git remote get-url origin 2>$null

if ($existingRemote) {
    Write-Host "✓ Remote 'origin' already configured: $existingRemote" -ForegroundColor Green
} else {
    Write-Host "Adding remote repository..." -ForegroundColor Cyan
    git remote add origin $remoteUrl
    Write-Host "✓ Remote added: $remoteUrl" -ForegroundColor Green
}

Write-Host ""

# Push to GitHub
Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
Write-Host "Note: You may be prompted for GitHub credentials." -ForegroundColor Yellow
Write-Host "Use your GitHub username and Personal Access Token (not password)." -ForegroundColor Yellow
Write-Host ""

try {
    git push -u origin main
    Write-Host ""
    Write-Host "✓ Successfully pushed to GitHub!" -ForegroundColor Green
    Write-Host ""
    Write-Host "View your repository at: https://github.com/keshavabc12/traffic" -ForegroundColor Cyan
} catch {
    Write-Host ""
    Write-Host "✗ Push failed!" -ForegroundColor Red
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "1. Authentication failed - Use Personal Access Token instead of password" -ForegroundColor Yellow
    Write-Host "2. Repository not found - Verify you have access to the repository" -ForegroundColor Yellow
    Write-Host "3. Remote has changes - Try: git pull origin main --rebase" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "See GIT_SETUP_GUIDE.md for detailed troubleshooting." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Visit: https://github.com/keshavabc12/traffic" -ForegroundColor White
Write-Host "2. Verify all files are present" -ForegroundColor White
Write-Host "3. Check that README.md displays correctly" -ForegroundColor White
Write-Host ""
Write-Host "For future updates, use:" -ForegroundColor Cyan
Write-Host "  git add ." -ForegroundColor White
Write-Host "  git commit -m 'Your commit message'" -ForegroundColor White
Write-Host "  git push" -ForegroundColor White
