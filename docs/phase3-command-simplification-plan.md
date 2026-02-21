# Phase 3: Command Simplification Plan

## Current State Analysis

### Command Count: 50 commands (target: 12-15)
- **Setup Commands**: 8 commands (setup, setup-dev, ide-setup, generate-secrets, etc.)
- **Gateway Management**: 6 commands (start, stop, gateway-only, register, etc.)
- **Status & Monitoring**: 5 commands (status, status-detailed, status-json, list-servers, etc.)
- **Authentication**: 4 commands (jwt, auth, auth-check, auth-refresh)
- **Configuration**: 8 commands (config-*, validate-config)
- **Development**: 10 commands (lint-*, format-*, test, deps-*)
- **Help System**: 4 commands (help, help-topics, help-examples)
- **Utility**: 5 commands (clean, reset-db, cleanup-duplicates, etc.)

## Consolidation Strategy

### 1. Setup Commands (8 → 3)
**Current**: `setup`, `setup-dev`, `ide-setup`, `generate-secrets`, `auth`, `auth-check`, `auth-refresh`, `config-install`

**Consolidated**:
- `setup` - Interactive setup wizard (combines setup + setup-dev + ide-setup)
- `auth` - Authentication management (combines auth + auth-check + auth-refresh + generate-secrets)
- `config` - Configuration management (combines config-* commands)

### 2. Gateway Management (6 → 4)
**Current**: `start`, `stop`, `gateway-only`, `register`, `register-wait`, `validate-config`

**Consolidated**:
- `start` - Start gateway (with options: --gateway-only, --wait)
- `stop` - Stop gateway
- `register` - Register servers (with --wait option)
- `status` - System status (combines status commands)

### 3. Development Commands (10 → 3)
**Current**: `lint`, `lint-python`, `lint-typescript`, `lint-all`, `shellcheck`, `format`, `format-python`, `format-typescript`, `test`, `test-coverage`

**Consolidated**:
- `lint` - Run all linters (with --python, --typescript, --shell options)
- `format` - Format all code (with --python, --typescript options)
- `test` - Run tests (with --coverage option)

### 4. Help System (4 → 2)
**Current**: `help`, `help-topics`, `help-examples`

**Consolidated**:
- `help` - Enhanced help (with --topics, --examples options)
- `wizard` - Interactive configuration wizard

### 5. Utility Commands (5 → 3)
**Current**: `clean`, `reset-db`, `cleanup-duplicates`, `list-servers`, `list-prompts`

**Consolidated**:
- `clean` - Clean up (combines clean + reset-db + cleanup-duplicates)
- `list` - List resources (combines list-servers + list-prompts)
- `backup` - Backup management (combines config-* backup commands)

## Implementation Plan

### Phase 3.1: Command Consolidation (Week 1)
1. **Create Interactive Setup Wizard**
   - Combine setup, setup-dev, ide-setup
   - Add step-by-step configuration
   - Include validation and error handling

2. **Implement Command Options**
   - Add parameter parsing to existing commands
   - Implement --help for each command
   - Add subcommand structure where appropriate

3. **Consolidate Authentication Commands**
   - Merge auth-related commands
   - Add interactive secret generation
   - Implement token management

### Phase 3.2: Enhanced Help System (Week 2)
1. **Unified Help Command**
   - Consolidate help commands
   - Add contextual help based on user state
   - Implement command discovery

2. **Interactive Wizard**
   - Create configuration wizard
   - Add guided setup processes
   - Include validation and feedback

### Phase 3.3: Development Workflow Integration (Week 3)
1. **Consolidated Development Commands**
   - Merge lint/format/test commands
   - Add pre-commit integration
   - Implement CI/CD alignment

2. **Status and Monitoring**
   - Consolidate status commands
   - Add JSON output options
   - Implement health checks

## Expected Benefits

### User Experience Improvements
- **Reduced Complexity**: From 50 to 12-15 commands
- **Better Discoverability**: Interactive help and wizard
- **Consistent Interface**: Standardized command options
- **Faster Onboarding**: Guided setup processes

### Maintenance Benefits
- **Reduced Code Duplication**: Consolidated command implementations
- **Easier Testing**: Fewer commands to test and maintain
- **Better Documentation**: Focused help system
- **Simplified CI/CD**: Fewer command variations

## Success Metrics

### Quantitative Metrics
- **Command Count**: Reduce from 50 to 12-15 commands (70% reduction)
- **Setup Time**: Reduce from 15 minutes to 5 minutes (67% improvement)
- **Help Usage**: Increase help command usage by 50%
- **Error Reduction**: Reduce command-related errors by 40%

### Qualitative Metrics
- **User Satisfaction**: Improved user experience feedback
- **Documentation Quality**: Better help and documentation
- **Onboarding Experience**: Smoother new user experience
- **Development Velocity**: Faster development workflows

## Implementation Details

### Command Structure Changes

#### Before:
```bash
make setup
make setup-dev
make ide-setup
make generate-secrets
make auth
make auth-check
```

#### After:
```bash
make setup              # Interactive wizard
make auth --generate    # Generate secrets
make auth --check       # Check configuration
make auth --refresh     # Refresh token
```

### Help System Enhancement

#### Before:
```bash
make help
make help-topics
make help-examples
```

#### After:
```bash
make help               # General help
make help --topics      # List topics
make help --examples    # Show examples
make help setup         # Contextual help
make wizard             # Interactive wizard
```

### Development Workflow

#### Before:
```bash
make lint
make lint-python
make lint-typescript
make format
make test
make test-coverage
```

#### After:
```bash
make lint               # All linters
make lint --python      # Python only
make lint --typescript  # TypeScript only
make format             # All formatters
make test               # Run tests
make test --coverage    # With coverage
```

## Risk Mitigation

### Backward Compatibility
- **Alias Support**: Maintain old command names as aliases
- **Migration Guide**: Provide clear migration documentation
- **Gradual Rollout**: Implement in phases with user feedback

### User Adoption
- **Interactive Help**: Guide users through new command structure
- **Documentation**: Comprehensive updated documentation
- **Training Materials**: Video tutorials and guides

### Technical Risks
- **Testing**: Comprehensive testing of consolidated commands
- **Performance**: Ensure no performance degradation
- **Error Handling**: Robust error handling and user feedback

## Next Steps

1. **Week 1**: Implement command consolidation and options
2. **Week 2**: Create interactive wizard and enhanced help
3. **Week 3**: Complete development workflow integration
4. **Week 4**: Testing, documentation, and user feedback

## Dependencies

- **Phase 2 IDE Integration**: Must be complete for wizard functionality
- **Phase 7 Admin UI**: Should be considered for integration
- **User Feedback**: Collect feedback during implementation

## Success Criteria

- [ ] Command count reduced to 12-15
- [ ] Interactive setup wizard functional
- [ ] Enhanced help system implemented
- [ ] User feedback positive
- [ ] Documentation updated
- [ ] Backward compatibility maintained
- [ ] Performance maintained or improved
