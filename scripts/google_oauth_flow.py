#!/usr/bin/env python3
"""Browser-based OAuth flow to obtain a Google refresh token.

Usage:
    pip install google-auth-oauthlib
    python scripts/google_oauth_flow.py

The script reads the client secret JSON from ~/Downloads/ and opens a
browser window for consent.  After approval it prints the refresh_token
which should be encrypted with ansible-vault and stored as
vault_google_oauth_refresh_token.
"""

import glob
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

CLIENT_SECRET_PATTERN = "~/Downloads/client_secret_759748773660-*.json"


def main():
    matches = glob.glob(CLIENT_SECRET_PATTERN.replace("~", str(__import__("pathlib").Path.home())))
    if not matches:
        print(f"No client secret file found matching {CLIENT_SECRET_PATTERN}")
        sys.exit(1)

    client_secret_file = matches[0]
    print(f"Using client secret: {client_secret_file}")

    flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, scopes=SCOPES)
    creds = flow.run_local_server(port=8080, open_browser=True)

    print("\n--- Refresh Token ---")
    print(creds.refresh_token)
    print("---------------------")
    print("\nEncrypt with:")
    print(
        "  cd ansible && ansible-vault encrypt_string"
        f" '{creds.refresh_token}'"
        " --name 'vault_google_oauth_refresh_token'"
        " --vault-password-file ~/.vault_pass.txt"
    )


if __name__ == "__main__":
    main()
