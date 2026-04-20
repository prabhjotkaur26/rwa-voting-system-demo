# RWA Voting System - Frontend

Modern, responsive web interface for voting.

## Features

- **Mobile-First Design**: Responsive layout works on phones, tablets, and desktops
- **Real-time Voting**: Immediate vote submission and confirmation
- **Live Results Dashboard**: Auto-refreshing vote counts per candidate
- **OTP Authentication**: Secure SMS-based voter verification
- **Accessibility**: WCAG compliant, keyboard navigable
- **No Dependencies**: Pure HTML5, CSS3, and vanilla JavaScript (no framework required)

## Quick Start

### Local Development

1. **Update API Endpoint**
   - Open `app.js`
   - Find line: `return "https://your-api-id.execute-api..."`
   - Replace with your actual API endpoint

2. **Serve Locally**
   ```bash
   # Python 3
   python -m http.server 8000

   # Or using Node.js
   npx http-server

   # Or using any web server (nginx, Apache, etc.)
   ```

3. **Open in Browser**
   ```
   http://localhost:8000
   ```

### Production Deployment

#### Option 1: AWS S3 Hosting

```bash
# Upload to S3
aws s3 cp . s3://your-bucket-name --recursive --include "*.html" --include "*.css" --include "*.js"

# Access via S3 website endpoint
# http://your-bucket-name.s3-website-ap-south-1.amazonaws.com
```

#### Option 2: CloudFront CDN

```bash
# Create CloudFront distribution pointing to S3
# Provides global edge locations and caching
```

#### Option 3: Traditional Web Server

```bash
# Copy files to web server
scp -r ./* user@server:/var/www/voting-system

# Configure web server (nginx/Apache)
```

## File Structure

```
frontend/
├── index.html       # Main HTML markup
├── style.css        # Styling (4000+ lines)
├── app.js           # Application logic (600+ lines)
└── README.md        # This file
```

## API Integration

The JavaScript client communicates with the backend via REST API.

### Configuration

Update API endpoint in `app.js`:

```javascript
getAPIEndpoint() {
    return "https://your-api-id.execute-api.ap-south-1.amazonaws.com/prod";
}
```

Or set via prompt on first run.

### Endpoints Used

- `POST /auth/send-otp` - Request OTP
- `POST /auth/verify-otp` - Verify OTP
- `POST /vote/cast-vote` - Cast vote
- `GET /results/{electionId}` - Get results

## User Flow

### 1. Authentication
```
User enters mobile number
  ↓
Frontend sends to /auth/send-otp
  ↓
User receives SMS with OTP
  ↓
User enters OTP
  ↓
Frontend sends to /auth/verify-otp
  ↓
User authenticated, voting interface loads
```

### 2. Voting
```
Frontend displays 7 posts
  ↓
User selects candidate for each post
  ↓
User clicks "Submit All Votes"
  ↓
Frontend sends 7 requests to /vote/cast-vote (one per post)
  ↓
Success page shows
  ↓
Optional: View live results
```

### 3. Results
```
User clicks "View Results"
  ↓
Frontend auto-refreshes every 5 seconds
  ↓
Shows vote counts per candidate per post
  ↓
Bars and numbers update in real-time
```

## Styling & Customization

### Colors

Edit `:root` in `style.css`:

```css
:root {
    --primary-color: #2563eb;      /* Blue */
    --secondary-color: #64748b;    /* Gray */
    --success-color: #10b981;      /* Green */
    --danger-color: #ef4444;       /* Red */
}
```

### Fonts

Current stack: System fonts (no external dependencies)

To change:
```css
body {
    font-family: 'Your Font', sans-serif;
}
```

### Branding

1. **Logo/Header**: Edit `.logo h1` in `style.css`
2. **Colors**: Update `:root` variables
3. **Footer**: Edit `.footer` HTML in `index.html`

## Accessibility

### Already Implemented

- Semantic HTML5
- ARIA labels where needed
- Keyboard navigation support
- Color contrast ratios meet WCAG AA
- Focus indicators on all interactive elements
- Alt text for images

### Further Improvements

```html
<!-- Add aria-live region for status updates -->
<div aria-live="polite" aria-label="Operation status">
    <!-- Updates announced to screen readers -->
</div>

<!-- Add lang attribute -->
<html lang="en">
</html>
```

## Browser Compatibility

Tested and supported:
- Chrome/Edge 80+
- Firefox 75+
- Safari 13+
- Mobile browsers (iOS Safari 13+, Chrome Android 80+)

Uses:
- ES6 JavaScript (fetch API, async/await)
- CSS Grid and Flexbox
- CSS Variables

## Performance Optimization

### Current

- Minimal HTTP requests (1 HTML, 1 CSS, 1 JS)
- No third-party dependencies
- Gzip compression (enable in web server)
- Responsive images
- Lazy loading (if needed)

### Further Optimization

```bash
# Minify CSS and JS
npm install -g uglify-js clean-css-cli

# Minify
uglifyjs app.js -o app.min.js
cleancss style.css -o style.min.css

# Update HTML to reference minified files
```

## Error Handling

The app handles:
- Network failures (shows retry option)
- Invalid OTP (shows max attempts warning)
- API errors (provides user-friendly messages)
- Timeout errors (with retry mechanism)

### User-Facing Messages

All API errors are translated to user-friendly messages:

```javascript
error.message = "OTP not found or expired" (not raw: OTP_NOT_FOUND)
```

## Testing

### Manual Testing Checklist

- [ ] OTP generation works
- [ ] OTP verification works
- [ ] Voting interface loads
- [ ] Vote can be cast
- [ ] Results display correctly
- [ ] Results auto-refresh
- [ ] Mobile responsiveness works
- [ ] Keyboard navigation works
- [ ] API errors handled gracefully

### Automated Testing (Optional)

```bash
# Install testing framework
npm install --save-dev jest

# Run tests
npm test
```

## Troubleshooting

### API Endpoint Not Reachable

```
Error: CORS policy
Solution: Ensure API endpoint is correct and CORS is enabled
```

### OTP Not Received

```
Issue: SMS not sent
Solution: 
1. Check SNS sandbox status in AWS
2. Verify phone number format
3. Check SMS budget limits
```

### Votes Not Submitted

```
Issue: "You have already voted" error
Solution: Clear browser storage, use different phone number
```

### Results Not Updating

```
Issue: Results stuck old data
Solution:
1. Click "Refresh Results"
2. Check auto-refresh is enabled
3. Verify election is still active
```

## Development

### Local Changes

1. Edit HTML/CSS/JS files
2. Save and refresh browser (Ctrl+R or Cmd+R)
3. Open DevTools (F12) to see console logs

### Debugging

```javascript
// Enable debug logs in app.js
console.log('Voting Client initialized');
console.log('API Endpoint:', votingClient.API_ENDPOINT);
```

Monitor network requests in DevTools → Network tab.

## Production Checklist

- [ ] API endpoint configured correctly
- [ ] CORS headers allow frontend domain
- [ ] Both HTTP and HTTPS work  
- [ ] Mobile layout tested on real devices
- [ ] Keyboard navigation tested
- [ ] Error messages are clear
- [ ] Accessibility audit passed
- [ ] Performance meets requirements
- [ ] Analytics configured (if needed)
- [ ] Loading states work
- [ ] Images optimized
- [ ] Cache headers configured

## Future Enhancements

1. **Framework Migration** (React/Vue)
   - Better state management
   - Component reusability
   - Testing frameworks

2. **Offline Support**
   - Service workers
   - Progressive Web App (PWA)
   - Offline vote caching

3. **Advanced Features**
   - 2FA authentication
   - Biometric voting
   - Vote confirmation timeout
   - Audit trail

4. **Internationalization**
   - Multi-language support
   - RTL layout support
   - Currency/format localization

## License

MIT - See LICENSE file

## Support

For issues:
1. Check console errors (DevTools)
2. Review API connectivity
3. Verify API endpoint configuration
4. Check AWS DynamoDB and Lambda logs

---

**Last Updated**: 2024  
**Maintained by**: RWA Tech Team
