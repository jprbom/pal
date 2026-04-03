# Google Authentication (Gmail + Calendar)

Google OAuth gives Pal access to Gmail and Google Calendar. You need three values: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_PROJECT_ID`.

This setup is a one-time process. After completing it, Pal can search email, read threads, create drafts, view your calendar, and create events.

## What Pal Can Do

| Service | Enabled | Disabled |
|---------|---------|----------|
| **Gmail** | Search, read threads, create/update/list drafts, manage labels | Send email, send replies |
| **Calendar** | View events, create events, update events, delete events, find available slots | — |

Sending email is disabled at the code level. Pal always creates drafts: "Draft created in Gmail. Review and send when ready."

Calendar events with external attendees require user confirmation before creation.

## Step 1: Create a Google Cloud Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click the project dropdown (top-left) → **New Project**
3. Name it (e.g., `agents`) and click **Create**
4. Copy the **Project ID** from the project dashboard → save as `GOOGLE_PROJECT_ID`

## Step 2: Enable the APIs

1. Go to **APIs & Services → Library**
2. Search for and enable **Gmail API**
3. Search for and enable **Google Calendar API**

## Step 3: Configure the OAuth Consent Screen

1. Go to **APIs & Services → OAuth consent screen**
2. Click **Get started**
3. **App Information**: Enter an app name (e.g., `pal`) and your support email → **Next**
4. **Audience**: Select **External** → **Next**
5. **Contact Information**: Enter your email → **Next**
6. **Finish**: Click **Create**
7. Go to **Audience** in the sidebar and add your Google email as a test user

## Step 4: Create OAuth Credentials

1. Go to **APIs & Services → Credentials**
2. Click **Create Credentials → OAuth client ID**
3. Application type: **Desktop app**
4. Name it (e.g., `pal-desktop`) → **Create**
5. Copy **Client ID** → `GOOGLE_CLIENT_ID`
6. Copy **Client secret** → `GOOGLE_CLIENT_SECRET`

## Step 5: Add to `.env`

```env
GOOGLE_CLIENT_ID="your-google-client-id"
GOOGLE_CLIENT_SECRET="your-google-client-secret"
GOOGLE_PROJECT_ID="your-google-project-id"
```

## Step 6: Generate `token.json`

Run the OAuth script on your local machine (not inside Docker):

```sh
set -a; source .env; set +a
python scripts/google_auth.py
```

This opens a browser for Google consent and saves `token.json` to the project root. The script uses `prompt='consent'` to ensure a refresh token is always returned, even on re-authorization.

## Step 7: Restart Pal

```sh
docker compose up -d --build
```

Gmail and Google Calendar are now configured.

## Troubleshooting

### Token Expired (7-day limit)

Google defaults to "Testing" mode, which expires tokens every 7 days. When this happens:

```sh
set -a; source .env; set +a
python scripts/google_auth.py
docker compose up -d --build
```

Publishing the app through Google's verification process removes the 7-day limit.

### "Access blocked" Error

Your Google email must be added as a test user in the OAuth consent screen:
1. Go to **APIs & Services → OAuth consent screen → Audience**
2. Add your email under **Test users**

### Missing Credentials

All three values are required. If any are missing, Pal disables Gmail and Calendar with a fallback message:

> Gmail isn't set up yet. Follow the setup guide in `docs/GOOGLE_AUTH.md` to connect your Google account.

### OAuth Scopes

The `scripts/google_auth.py` script requests these scopes:
- `gmail.readonly` — read email
- `gmail.modify` — manage labels, mark read/unread
- `gmail.compose` — create drafts
- `calendar` — full calendar access

## How It Works

1. `scripts/google_auth.py` runs an OAuth flow that opens a browser for consent.
2. On success, it saves `token.json` to the project root with access and refresh tokens.
3. At startup, `pal/team.py` checks if all three Google env vars are set.
4. If yes: `GmailTools` and `GoogleCalendarTools` are loaded, with Gmail's `send_email` and `send_email_reply` disabled.
5. If no: disabled instruction blocks are appended, and no Google tool calls are attempted.

The `token.json` file is mounted into the Docker container via `compose.yaml`. It contains OAuth tokens — do not commit it to version control (it's in `.gitignore`).
