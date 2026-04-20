# Contributing to RWA Voting System

Thank you for your interest in contributing! This document provides guidelines for contributing.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Report issues professionally
- No harassment or discrimination

## How to Contribute

### 1. Report Issues

Found a bug? Please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Screenshots if applicable
- Environment details

### 2. Feature Requests

Have an idea? Submit a feature request with:
- Clear description of the feature
- Use case and benefits
- Potential implementation approach
- Priority level (nice-to-have vs critical)

### 3. Code Contributions

#### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/rwa-voting-system.git
cd rwa-voting-system

# Create feature branch
git checkout -b feature/your-feature-name

# Install dependencies
pip install -r requirements.txt
terraform init
```

#### Code Style

**Python (Lambda functions):**
- Follow PEP 8
- Use meaningful variable names
- Add docstrings for functions
- Max line length: 100 characters
- Type hints where helpful

```python
def send_otp(mobile_number: str) -> Dict[str, Any]:
    """Send OTP to mobile number via SNS.
    
    Args:
        mobile_number: 10-digit phone number
        
    Returns:
        Dict with success status and message
    """
```

**Terraform:**
- Resource names must be descriptive
- Use variables for configuration
- Add comments for complex logic
- Follow HashiCorp style guide

```hcl
resource "aws_dynamodb_table" "votes" {
  # Description of purpose
  name = "${var.project_name}-votes-${var.environment}"
  # ...
}
```

**JavaScript:**
- Follow Airbnb style guide
- Use const/let, not var
- Arrow functions preferred
- Meaningful function names

```javascript
// Good
const sendOTP = async (mobileNumber) => {
    const response = await api.post('/auth/send-otp', { mobileNumber });
    return response.data;
};

// Avoid
function s(m) {
    // unclear
}
```

#### Testing

Before submitting:
1. Write tests for new functionality
2. Ensure all tests pass: `pytest tests/`
3. Check code coverage
4. Run linting: `pylint lambda/functions/`

#### Documentation

- Update relevant docs for new features
- Include code examples
- Explain configuration options
- Add troubleshooting if needed

### 4. Pull Request Process

1. **Fork and Create Branch**
   ```bash
   git checkout -b feature/awesome-feature
   ```

2. **Make Changes**
   - Keep commits atomic and logical
   - Write clear commit messages
   - Update tests and docs

3. **Commit and Push**
   ```bash
   git add .
   git commit -m "Add awesome feature: description"
   git push origin feature/awesome-feature
   ```

4. **Create Pull Request**
   - Provide clear title and description
   - Reference related issues (#123)
   - Include testing notes
   - Request reviews from maintainers

5. **Code Review**
   - Address reviewer comments
   - Make updates in new commits
   - Request re-review when ready

6. **Merge**
   - Squash commits if requested
   - Ensure CI/CD passes
   - Delete feature branch

## Best Practices

### Lambda Functions

- Keep functions focused and small
- Use environment variables for config
- Add comprehensive error handling
- Log important events (masked sensitive data)
- Optimize for cold starts

```python
# Good
def send_otp(event, context):
    return result

# Avoid
def do_everything(event, context):
    # Avoid multiple responsibilities
```

### Security

- Never commit credentials
- Use AWS IAM roles, not keys
- Validate all inputs
- Escape output
- Use HTTPS only
- Keep dependencies updated

### Performance

- Optimize DynamoDB queries
- Use Lambda layers for shared code
- Implement caching where appropriate
- Monitor CloudWatch metrics
- Benchmark before optimizing

### Documentation

- Document public APIs
- Include usage examples
- Explain configuration options
- Provide troubleshooting tips
- Keep docs up-to-date

## Commit Message Format

```
type(scope): description

body (optional)

footer (optional)
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Test additions
- `perf`: Performance improvement
- `chore`: Build/dependency update

Example:
```
feat(lambda): add email OTP support

- Implement email OTP sending via SES
- Support fallback to SMS if email fails
- Add email validation

Fixes #42
```

## Review Process

1. **Automated Checks**
   - Linting and formatting
   - Unit tests
   - Security scanning
   - Infrastructure validation

2. **Manual Review**
   - Code quality
   - Architectural alignment
   - Documentation completeness
   - Security implications

3. **Approval**
   - At least 2 approvals required
   - No unresolved conversations
   - All checks passing

## Deployment

Contributors with deployment rights:
1. Create release branch: `release/v1.0.0`
2. Update version numbers
3. Update CHANGELOG.md
4. Create tag: `git tag v1.0.0`
5. Push tag: `git push origin v1.0.0`

## Areas for Contribution

### High Priority
- [ ] Email OTP support (replace expensive SMS)
- [ ] Admin authentication
- [ ] Result export (CSV, PDF)
- [ ] Rate limiting per IP
- [ ] Comprehensive error handling

### Medium Priority
- [ ] Multi-language support
- [ ] Admin dashboard
- [ ] Audit logging
- [ ] Performance optimizations
- [ ] CloudFront CDN integration

### Nice-to-Have
- [ ] Mobile app wrapper
- [ ] Biometric voting
- [ ] Blockchain integration (for audit)
- [ ] End-to-end encryption
- [ ] Decentralized voting

## Getting Help

- **Documentation**: See `/docs` folder
- **Issues**: Check GitHub issues
- **Discussions**: Use GitHub discussions
- **Email**: Contact maintainers

## Contact

- GitHub: [@yourusername]
- Email: maintainers@rwa-voting-system.dev

---

Thank you for contributing to make RWA voting more secure and accessible!
