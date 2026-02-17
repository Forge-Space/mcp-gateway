# Trunk Based Development Workflow

This project uses Trunk Based Development with the following branch strategy:

## Branch Structure

- **main**: Production-ready code, always deployable
- **dev**: Development environment branch, continuously deployed
- **release/x.y.z**: Release preparation branches
- **feature/***: Feature development branches

## Workflow

1. **Feature Development**
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/your-feature-name dev
   # Make your changes
   git commit -m "feat: add your feature"
   git push origin feature/your-feature-name
   ```

2. **Testing & Review**
   - Create PR from `feature/your-feature-name` to `release/x.y.z`
   - All CI tests must pass
   - Code review required

3. **Release Preparation**
   ```bash
   # Create release branch from main
   ./scripts/create-release-branch.sh 1.0.1
   ```

4. **Production Deployment**
   - Merge `release/x.y.z` to `main`
   - Automatic production deployment triggered
   - Release tag and GitHub release created

## Environments

- **Development**: Auto-deployed from `dev` branch
  - URL: http://dev.mcp-gateway.example.com
  - Database: Development instance

- **Production**: Deployed from `main` branch merges
  - URL: https://mcp-gateway.example.com
  - Database: Production instance with backups

## Automated Deployments

- **Dev**: Every push to `dev` branch triggers deployment
- **Production**: Merge of `release/x.y.z` to `main` triggers deployment

## Rollback Procedures

- **Dev**: Automatic rollback on health check failure
- **Production**: Manual rollback with one-command recovery

## Scripts

- `./scripts/create-release-branch.sh [version]` - Create new release branch
- `./scripts/deploy-dev.sh` - Manual development deployment
- `./scripts/deploy-prod.sh` - Manual production deployment

## CI/CD Pipeline

All branches run:
- Linting (Python, TypeScript, Shell)
- Unit tests
- Build verification
- Security scanning

Additional checks for release branches:
- Integration tests
- E2E tests
- Performance tests

## Branch Protection

- **main**: Requires PR approval, passing CI, no force pushes
- **release/***: Requires PR approval and passing CI
- **dev**: Requires passing CI only

## Version Management

- Semantic versioning (x.y.z)
- Automatic version bumping in release branches
- Git tags created for all releases
- GitHub releases with changelog
