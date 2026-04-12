# Slack Feedback Digest

Generate a daily HTML summary of customer issue feedback from Slack channels.

## Usage
Run this skill and optionally specify channels:
- Default: reads `SLACK_CHANNELS` env var (comma-separated channel names or IDs)
- Override: mention specific channels in your message, e.g. `/slack-feedback-digest #customer-support #sales-feedback`

## What you need
- `SLACK_BOT_TOKEN` environment variable set (a bot token with `channels:history`, `channels:read`, `users:read` scopes)
- Optional: `SLACK_CHANNELS` env var with default channel list

---

## Instructions

You are a sales intelligence assistant. Follow these steps exactly.

### Step 1 — Resolve channels

Parse the user's message for any channel names (prefixed with `#`) or IDs. If none provided, read the `SLACK_CHANNELS` environment variable and split by comma. If that's also empty, ask the user which channels to pull from before continuing.

### Step 2 — Fetch today's messages from each channel

For each channel, run the following bash command to get messages from the last 24 hours. Replace `CHANNEL_ID` with the actual channel ID (use `conversations.list` first to resolve names to IDs if needed).

```bash
# Resolve channel name → ID (skip if already an ID starting with C)
curl -s "https://slack.com/api/conversations.list?limit=200&exclude_archived=true" \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
for ch in data.get('channels', []):
    print(ch['id'], ch['name'])
"
```

```bash
# Fetch last 24h of messages from a channel
OLDEST=$(python3 -c "import time; print(int(time.time()) - 86400)")
curl -s "https://slack.com/api/conversations.history?channel=CHANNEL_ID&oldest=$OLDEST&limit=200" \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN"
```

```bash
# Resolve a user ID to display name
curl -s "https://slack.com/api/users.info?user=USER_ID" \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('user',{}).get('real_name','Unknown'))"
```

Collect the raw message text and timestamps for all channels. If a channel has 0 messages in the last 24h, note it as quiet.

### Step 3 — Analyse and categorise feedback

For each channel's messages, identify and extract:
- **Bugs / Errors** — reports of something broken or not working
- **Feature Requests** — asks for new functionality
- **Pricing / Commercial** — concerns about cost, contracts, renewals
- **Competitor Mentions** — any named competitors
- **Positive Feedback** — praise, wins, compliments
- **Escalations** — urgent or high-priority issues flagged

For each item, capture: the gist (1 sentence), who raised it (display name), and the approximate time.

### Step 4 — Generate the HTML report

Write the complete HTML to a file named `slack-feedback-digest-YYYY-MM-DD.html` (use today's date). The report must be fully self-contained (no external dependencies) and include:

- A clean header with the date and total message count
- One section per Slack channel
- Within each channel section, one card per feedback category that had items
- Each card lists the individual items with author and time
- A "Key Takeaways" section at the top summarising the 3–5 most important things across all channels
- Color-coded category badges: red for bugs, blue for feature requests, amber for pricing, purple for competitors, green for positive, orange for escalations
- A timestamp footer showing when the report was generated

Use this HTML structure and inline CSS style (no external fonts or scripts):

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Slack Feedback Digest — {DATE}</title>
<style>
  /* paste the full CSS here — make it clean, readable, professional */
  /* Use a system font stack, white background, subtle card shadows */
  /* Category badges should be colored pills */
</style>
</head>
<body>
  <!-- Key Takeaways box -->
  <!-- Per-channel sections with category cards -->
  <!-- Footer with generation timestamp -->
</body>
</html>
```

Make the HTML genuinely polished — someone should be able to open it and immediately understand yesterday's Slack landscape at a glance.

### Step 5 — Confirm output

Tell the user:
- The filename written
- How many channels were processed
- Total messages analysed
- How many feedback items were extracted across all categories

Then offer to open the file or copy the path.