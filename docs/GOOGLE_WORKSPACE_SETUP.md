# Google Workspace Catch-All Email Setup

This document describes how to configure Google Workspace to route all agent emails to jeff@infiquetra.com.

## Overview

All OpenClaw agents need email addresses for account registration with various services (GitHub, Mattermost, AI tools, etc.). Instead of creating individual Google Workspace users (which costs $6/user/month), we use catch-all routing to forward all emails to a single inbox.

## Agent Email Addresses

| Agent | Email |
|-------|-------|
| Athena | athena@infiquetra.com |
| Apollo | apollo@infiquetra.com |
| Artemis | artemis@infiquetra.com |
| Hermes | hermes@infiquetra.com |
| Perseus | perseus@infiquetra.com |
| Prometheus | prometheus@infiquetra.com |
| Ares | ares@infiquetra.com |
| Poseidon | poseidon@infiquetra.com |

All emails to these addresses will be delivered to: **jeff@infiquetra.com**

## Setup Instructions

### Step 1: Access Google Admin Console

1. Go to https://admin.google.com
2. Sign in with your admin account (jeff@infiquetra.com)

### Step 2: Configure Catch-All Routing

1. Navigate to **Apps** → **Google Workspace** → **Gmail**
2. Click **Default routing** in the left sidebar
3. Scroll to the **Catch-all address** section
4. Click **Configure** (or **Edit** if already configured)
5. Configure the following settings:

   ```
   Messages to non-existent recipients:
   ✓ Deliver to: jeff@infiquetra.com

   Reject messages from:
   ☐ (Leave unchecked - accept all)

   Also route spam to this address:
   ☐ (Recommended: Leave unchecked)
   ```

6. Click **Save**

### Step 3: Verify Configuration

Test the catch-all routing:

```bash
# Send a test email to a non-existent address
echo "Test catch-all routing" | mail -s "Test" test@infiquetra.com

# Check jeff@infiquetra.com inbox - should receive the email
```

### Step 4: Create Email Aliases (Optional)

For better organization, you can create aliases in Gmail:

1. Go to Gmail settings → **See all settings**
2. Navigate to **Accounts and Import** tab
3. Under **Send mail as**, click **Add another email address**
4. Add each agent email as an alias (allows sending from agent@infiquetra.com)

## Account Registration Workflow

When registering accounts for agents:

1. **Use the agent's email**: e.g., athena@infiquetra.com
2. **Verification emails** will arrive at jeff@infiquetra.com
3. **Click verification links** from the jeff@ inbox
4. **Complete registration** on the agent's behalf

## Security Considerations

1. **Email access**: Only jeff@infiquetra.com has access to all agent emails
2. **Password resets**: All password reset emails go to jeff@infiquetra.com
3. **2FA setup**: Configure 2FA for services using authenticator apps or hardware keys
4. **Sensitive accounts**: For high-security services, consider creating dedicated Google Workspace users

## Cost Comparison

| Approach | Monthly Cost | Users |
|----------|--------------|-------|
| **Catch-all routing** | $0 (included) | 1 (jeff@) |
| Individual users | $48 | 8 agents × $6/user |

**Savings**: $48/month ($576/year)

## Limitations

1. **Inbox clutter**: All agent emails mix in one inbox
2. **No separate logins**: Agents can't independently check their email
3. **Gmail filters recommended**: Create filters to organize agent emails

## Gmail Filters Setup (Recommended)

Create filters to auto-label agent emails:

1. Go to Gmail → **Settings** → **Filters and Blocked Addresses**
2. Create a filter for each agent:

   ```
   From: athena@infiquetra.com OR To: athena@infiquetra.com
   → Apply label: "Agent/Athena"
   → Skip inbox (optional)
   ```

3. Repeat for all 8 agents

This keeps the inbox organized while maintaining catch-all functionality.

## Troubleshooting

### Emails not being delivered

1. Check spam folder in jeff@infiquetra.com
2. Verify catch-all is enabled in Admin Console
3. Check domain MX records are correct
4. Review Gmail logs in Admin Console

### Verification emails not arriving

1. Check spam folder
2. Use Gmail search: `to:agent@infiquetra.com`
3. Check email headers to confirm routing
4. Manually verify by checking the service's settings

## Alternative: Email Forwarding

If catch-all doesn't work, use email forwarding:

1. Create each agent as a Google Workspace user ($6/user/month)
2. Set up forwarding to jeff@infiquetra.com
3. Disable access to individual accounts

**Note**: This costs more but provides better isolation.

## Future Considerations

As the agent team scales:

1. **Dedicated email server**: Consider self-hosted email (Mailcow, Mailu)
2. **Programmatic access**: Use IMAP/SMTP for agent email automation
3. **Email-to-Mattermost bridge**: Forward emails directly to Mattermost channels

---

**Last Updated**: 2026-01-30
**Maintainer**: jeff@infiquetra.com
