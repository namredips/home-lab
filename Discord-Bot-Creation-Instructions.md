# Discord Bot Creation Instructions (Phase 2)

## Overview
You need to create 9 bot applications in the Discord Developer Portal. This will take approximately 18 minutes.

## Bot List
1. Zeus (Greek leader, all projects)
2. Athena (Greek agent)
3. Apollo (Greek agent)
4. Artemis (Greek agent)
5. Hermes (Greek agent)
6. Perseus (Greek agent)
7. Prometheus (Greek agent)
8. Ares (Greek agent)
9. Freya (Norse supervisor)

## Creation Steps (Per Bot)

For each bot above, follow these steps:

### 1. Create Application
1. Go to https://discord.com/developers/applications
2. Click **New Application**
3. Enter the bot name (e.g., "Zeus")
4. Accept Terms of Service
5. Click **Create**

### 2. Configure Bot
1. In the left sidebar, click **Bot**
2. Click **Add Bot** → **Yes, do it!**
3. Under **Privileged Gateway Intents**, enable:
   - ✅ **PRESENCE INTENT**
   - ✅ **SERVER MEMBERS INTENT**
   - ✅ **MESSAGE CONTENT INTENT**
4. Click **Save Changes**

### 3. Copy Bot Token
1. Under **TOKEN**, click **Reset Token** → **Yes, do it!**
2. Click **Copy** to copy the token
3. **IMPORTANT**: Save this token immediately - you won't be able to see it again
4. Store tokens in a secure location (I'll add them to Ansible Vault later)

### 4. Copy Application ID
1. In the left sidebar, click **OAuth2** → **General**
2. Copy the **CLIENT ID** (also called Application ID)
3. Save this alongside the bot token

## Token Storage Format

As you create each bot, save the information in this format:

```
Zeus:
  Token: <paste-token-here>
  App ID: <paste-app-id-here>

Athena:
  Token: <paste-token-here>
  App ID: <paste-app-id-here>

... (repeat for all 9 bots)
```

## OAuth2 Invite URLs

After you've created all bots and provided me with the Application IDs, I'll generate the OAuth2 invite URLs with the correct permissions.

### Required Permissions Breakdown

**Greek Agents (@Olympus role):**
- Send Messages
- Send Messages in Threads
- Create Public Threads
- Create Private Threads
- Embed Links
- Attach Files
- Add Reactions
- Use External Emoji
- Read Message History
- Use Application Commands

**Permissions Integer**: `274878295104`

**Freya (Supervisor):**
- Manage Channels
- Manage Messages
- Send Messages
- Read Message History
- Embed Links
- Attach Files

**Permissions Integer**: `275415359552`

## Next Steps

After you provide the tokens and Application IDs:
1. I'll encrypt tokens in Ansible Vault
2. I'll generate OAuth2 invite URLs for each bot
3. You'll click the invite URLs to add bots to the server
4. I'll run Phase 3 automation to assign roles and nicknames

## Time Estimate
- Per bot: ~2 minutes
- Total: ~18 minutes for all 9 bots

## Questions?
If you encounter any issues during bot creation, let me know!
