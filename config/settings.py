import os

# --- Newsletter senders ---
# Add the exact "From" email addresses of your newsletters here.
NEWSLETTER_SENDERS = [
    "hi@simple.ai",
    "dan@tldrnewsletter.com",
    "newsletter@thedeepview.co",
    "news@daily.therundown.ai",
    "crew@technews.therundown.ai"
]

# --- Claude model ---
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

# --- Google Sheets ---
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "")

SHEET_TOPICS = "Topics"
SHEET_LINKEDIN = "LinkedIn Drafts"
SHEET_VIDEO = "Video Scripts"

TOPICS_HEADERS = [
    "Date", "Topic Title", "Summary",
    "Source Newsletters", "Source URLs", "Topic ID", "Run Timestamp",
]
LINKEDIN_HEADERS = [
    "Date", "Topic ID", "Topic Title", "Post Copy",
    "Visual Suggestion", "Approval Status", "Notes", "Run Timestamp",
]
VIDEO_HEADERS = [
    "Date", "Topic ID", "Topic Title", "Hook",
    "Narration Script", "Storyboard Notes", "Approval Status", "Notes", "Run Timestamp",
]

# --- Gmail ---
GMAIL_LOOKBACK_HOURS = 24
