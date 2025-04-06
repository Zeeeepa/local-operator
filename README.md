# Local Operator

Python environment for AI agents to complete tasks on-device through a conversational chat interface. Agents plan step-wise execution paths with real-time problem solving to complete complex tasks.

## Windows Setup with WSL2 Integration

This guide will help you set up Local Operator on Windows with WSL2 integration to receive implementation requests from Slack.

### Prerequisites

1. Windows 10 version 2004 or higher (Build 19041 or higher) or Windows 11
2. WSL2 installed and configured
3. A Slack workspace with admin privileges to create apps

### Installation Steps

1. **Install WSL2 (if not already installed)**

   Open PowerShell as Administrator and run:

   ```powershell
   wsl --install
   ```

   This will install the default Ubuntu distribution. If you want a different distribution, you can specify it:

   ```powershell
   wsl --install -d <Distribution Name>
   ```

   Restart your computer if prompted.

2. **Clone the Local Operator repository**

   ```powershell
   git clone https://github.com/Zeeeepa/local-operator.git
   cd local-operator
   ```

3. **Install Python dependencies**

   ```powershell
   pip install -e .
   ```

4. **Configure Slack Integration**

   Create a Slack app in your workspace:
   
   - Go to [https://api.slack.com/apps](https://api.slack.com/apps)
   - Click "Create New App" and choose "From scratch"
   - Name your app and select your workspace
   - Under "Add features and functionality", select "Bots"
   - Click "Review & Add" and then "Add Bot User"
   - Go to "OAuth & Permissions" and add the following scopes:
     - `chat:write`
     - `chat:write.public`
     - `channels:read`
     - `channels:history`
     - `app_mentions:read`
   - Install the app to your workspace
   - Copy the "Bot User OAuth Token" (starts with `xoxb-`)

5. **Configure Local Operator credentials**

   Run the following commands to set up your Slack credentials:

   ```powershell
   python -m local_operator credential update SLACK_BOT_TOKEN
   # Enter your Bot User OAuth Token when prompted

   python -m local_operator credential update SLACK_APP_TOKEN
   # Enter your App-Level Token (starts with xapp-) if you have one

   python -m local_operator credential update SLACK_DEFAULT_CHANNEL
   # Enter the channel ID where you want test messages to be sent (e.g., C12345678)
   ```

6. **Start the Local Operator server**

   ```powershell
   python -m local_operator serve --host 0.0.0.0 --port 1111
   ```

   The server will start and validate your Slack credentials. If everything is set up correctly, you should see:
   
   ```
   Validating Slack credentials...
   ✅ Slack bot token is valid
   ✅ Slack app token is valid
   ✅ Test message sent to Slack
   ```

   And a test message will be sent to your specified Slack channel.

### Using WSL2 Commands via Slack

Once the Local Operator is running, you can send implementation requests from Slack that will execute commands in your WSL2 environment.

Example message format:

```
use wsl2 instance named "Ubuntu" "username" "password-123"

git remote add origin https://github.com/yourusername/your-repo-name.git
git checkout -b main
git add .
git commit -m "Initial commit"
git push -u origin main
```

The Local Operator will:
1. Parse the WSL2 configuration
2. Extract the Git commands
3. Execute each command in the specified WSL2 distribution
4. Return the results to Slack

### Troubleshooting

- **WSL2 not available**: Make sure WSL2 is properly installed and configured. Run `wsl --status` to check.
- **Slack authentication errors**: Verify your Slack tokens are correct and have the necessary permissions.
- **Command execution errors**: Check that the specified WSL2 distribution exists and the commands are valid.

## Additional Resources

- [WSL2 Documentation](https://docs.microsoft.com/en-us/windows/wsl/)
- [Slack API Documentation](https://api.slack.com/docs)
- [Local Operator Documentation](https://github.com/Zeeeepa/local-operator)
