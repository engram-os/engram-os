import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/calendar',
          'https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.compose'
          ]

def main():
    if not os.path.exists('credentials.json'):
        print("Error: credentials.json not found!")
        return

    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    
   
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    
    print("Success! 'token.json' created. Docker can now access your Calendar.")

if __name__ == '__main__':
    main()