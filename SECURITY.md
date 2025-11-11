# Security Notes

## CodeQL Analysis

This document addresses the security alerts found by CodeQL analysis.

### Path Injection Alerts

**Status**: Mitigated

The remaining path injection alerts in `webui.py` and `rewards_points.py` are related to cookie file paths constructed from usernames. These have been mitigated through:

1. **Input Validation**: All usernames are validated using the `sanitize_username()` function which only allows alphanumeric characters, `@`, `.`, `_`, and `-`.

2. **Pattern**: `^[a-zA-Z0-9@._-]+$`

3. **Locations Protected**:
   - `webui.py`: All routes using `<username>` parameter
   - `rewards_points.py`: Cookie file validation

4. **Additional Security Measures**:
   - Cookie files are only created in the application directory
   - Filenames follow strict pattern: `cookie_<username>.txt`
   - No directory traversal possible due to regex validation
   - All errors are logged without exposing stack traces to users

### Stack Trace Exposure

**Status**: Fixed

All stack trace exposures have been eliminated by:

1. **safe_error_response() Helper**: Returns generic error messages to users
2. **Logging**: Detailed errors are logged server-side only
3. **No Exception Details**: User-facing responses never include `str(e)` or stack traces

### Recommendations for Deployment

1. **Network Security**:
   - Change `webui.host` from `0.0.0.0` to `127.0.0.1` for local-only access
   - Use reverse proxy (nginx/Apache) with HTTPS if exposing to network
   - Implement rate limiting for API endpoints

2. **File Permissions**:
   - Ensure `config.json` and `account.json` have restrictive permissions (600)
   - Cookie files should be readable only by the application user

3. **Authentication**:
   - Current implementation has no authentication
   - For production use, implement authentication/authorization
   - Consider adding API keys or session management

4. **Data Protection**:
   - Passwords are stored in plaintext in `account.json`
   - Consider encrypting sensitive data at rest
   - Use environment variables for sensitive configuration

## False Positives

The CodeQL path injection alerts are false positives because:

1. All usernames go through strict regex validation
2. The regex pattern prevents directory traversal (`../`, `./`, etc.)
3. No user input can introduce path separators
4. Cookie files are constrained to a single directory with validated names

## Future Improvements

- Implement proper authentication system
- Add CSRF protection for state-changing operations
- Encrypt passwords in configuration files
- Add rate limiting middleware
- Implement audit logging for sensitive operations
