# Publishing Guide for @mcp-gateway/client

This guide covers how to publish the NPX client package to NPM.

## Prerequisites

1. **NPM Account**: Create account at [npmjs.com](https://www.npmjs.com/signup)
2. **NPM CLI**: Already installed with Node.js
3. **Package Built**: Run `npm run build` to compile TypeScript

## Pre-Publishing Checklist

- [ ] Package builds successfully (`npm run build`)
- [ ] Version number updated in `package.json`
- [ ] CHANGELOG.md updated with release notes
- [ ] README/documentation reviewed
- [ ] No sensitive data in package files
- [ ] `.gitignore` excludes build artifacts
- [ ] `package.json` "files" field includes only necessary files

## Publishing Steps

### 1. Login to NPM

```bash
npm login
```

Enter your NPM credentials when prompted.

### 2. Verify Package Contents

Check what will be published:

```bash
npm pack --dry-run
```

This shows all files that will be included in the package.

### 3. Test Package Locally

Link the package for local testing:

```bash
npm link
```

Then test in your IDE configuration:

```json
{
  "mcpServers": {
    "test-gateway": {
      "command": "mcp-gateway",
      "args": ["--url=http://localhost:4444/servers/<UUID>/mcp"]
    }
  }
}
```

### 4. Publish to NPM

**First time (public package):**

```bash
npm publish --access public
```

**Subsequent updates:**

```bash
npm publish
```

### 5. Verify Publication

Check the package page:

```text
https://www.npmjs.com/package/@mcp-gateway/client
```

Test installation:

```bash
npx @mcp-gateway/client --help
```

## Version Management

Follow semantic versioning (semver):

- **Patch (0.1.X)**: Bug fixes, documentation updates
- **Minor (0.X.0)**: New features, non-breaking changes
- **Major (X.0.0)**: Breaking changes

### Update Version

```bash
# Patch release (0.1.0 -> 0.1.1)
npm version patch

# Minor release (0.1.0 -> 0.2.0)
npm version minor

# Major release (0.1.0 -> 1.0.0)
npm version major
```

This automatically:
- Updates `package.json` version
- Creates a git commit
- Creates a git tag

Then publish:

```bash
npm publish
git push --follow-tags
```

## Package Scope

The package is scoped as `@mcp-gateway/client`. To change the scope or make it unscoped:

1. Update `package.json` name field
2. Ensure you have permissions for that scope on NPM
3. Publish with `--access public` for scoped packages

## Troubleshooting

### "You do not have permission to publish"

- Verify you're logged in: `npm whoami`
- Check package name isn't taken: `npm view @mcp-gateway/client`
- Use `--access public` for scoped packages

### "Package already exists"

- Update version number in `package.json`
- Run `npm version patch` (or minor/major)

### "ENEEDAUTH"

- Run `npm login` again
- Check NPM token hasn't expired

### Files Missing from Package

- Check `package.json` "files" field
- Verify `.npmignore` or `.gitignore` isn't excluding needed files
- Use `npm pack --dry-run` to preview

## Unpublishing (Emergency Only)

**Warning**: Unpublishing is permanent and discouraged.

```bash
# Unpublish specific version
npm unpublish @mcp-gateway/client@0.1.0

# Unpublish entire package (within 72 hours of publish)
npm unpublish @mcp-gateway/client --force
```

## Automated Publishing (Optional)

### GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to NPM

on:
  push:
    tags:
      - 'v*'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
          registry-url: 'https://registry.npmjs.org'
      - run: npm ci
      - run: npm run build
      - run: npm publish --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

Add `NPM_TOKEN` to GitHub repository secrets.

## Post-Publishing

1. **Update Documentation**: Ensure README reflects published package name
2. **Announce**: Share on relevant channels (Discord, Twitter, etc.)
3. **Monitor**: Watch for issues on GitHub/NPM
4. **Maintain**: Respond to issues and publish updates as needed

## Package Maintenance

### Regular Updates

- Keep dependencies updated: `npm update`
- Security audits: `npm audit`
- Check for outdated deps: `npm outdated`

### Deprecating Versions

If a version has critical bugs:

```bash
npm deprecate @mcp-gateway/client@0.1.0 "Critical bug, use 0.1.1+"
```

## Support

- **NPM Documentation**: https://docs.npmjs.com/
- **Package Issues**: GitHub Issues
- **NPM Support**: support@npmjs.com
