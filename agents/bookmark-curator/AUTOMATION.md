# Automating bookmark-curator

The bookmark-curator agent can run autonomously on a schedule to continuously process new bookmarks. Here's how to set it up on different platforms.

## Prerequisites

- [Kiro CLI](https://kiro.dev) installed and configured
- Node.js 18+ (for the extract.mjs pre-processor)
- Firefox bookmarks exported as JSON (or set up automatic export)

## How it works

1. Export Firefox bookmarks as JSON (manually or via extension)
2. The agent's pre-processor (`extract.mjs`) parses the JSON and identifies new bookmarks
3. The agent fetches content, categorizes, and generates outputs
4. Outputs: `bookmarks-data.json` (structured data), `bookmarks.md` (markdown), `bookmarks-feed.html` (visual feed)

## macOS: launchd

Create a plist file at `~/Library/LaunchAgents/com.kiro.bookmark-curator.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.kiro.bookmark-curator</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>kiro-cli agent run bookmark-curator --input ~/Downloads/bookmarks-latest.json</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>18</integer>
        <key>Minute</key>
        <integer>0</integer>
        <key>Weekday</key>
        <integer>5</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/bookmark-curator.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/bookmark-curator.err</string>
</dict>
</plist>
```

Load it:

```bash
launchctl load ~/Library/LaunchAgents/com.kiro.bookmark-curator.plist
```

This runs every Friday at 6 PM. Adjust `StartCalendarInterval` as needed.

## Linux: cron

```bash
# Edit crontab
crontab -e

# Add: Run every Friday at 18:00
0 18 * * 5 kiro-cli agent run bookmark-curator --input ~/Downloads/bookmarks-latest.json >> /tmp/bookmark-curator.log 2>&1
```

## Windows: Task Scheduler

1. Open Task Scheduler (`taskschd.msc`)
2. Create Basic Task:
   - Name: `Bookmark Curator`
   - Trigger: Weekly, Friday at 6:00 PM
   - Action: Start a program
   - Program: `powershell.exe`
   - Arguments: `-Command "kiro-cli agent run bookmark-curator --input $env:USERPROFILE\Downloads\bookmarks-latest.json"`
3. Click Finish

## Firefox Auto-Export

To automate the bookmark export step, use the [Bookmarks Export Tool](https://addons.mozilla.org/en-US/firefox/addon/bookmarks-export-tool/) Firefox extension, which can save bookmarks JSON to a fixed path on a schedule.

## Monitoring

Check the agent's progress file after each run:

```bash
cat ~/.kiro/agents/bookmark-curator-data/progress.md
```

Check for errors:

```bash
cat /tmp/bookmark-curator.log
cat /tmp/bookmark-curator.err
```

## Tips

- The agent processes bookmarks in batches of 50. If you have hundreds of new bookmarks, it may take multiple runs.
- The checkpoint system (`checkpoint.json`) allows the agent to resume after crashes.
- The `bookmarks-data.json` is shared with `learning-curator` and `training-mentor` - they read from it automatically.
