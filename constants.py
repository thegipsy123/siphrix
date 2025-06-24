# constants.py – Shared settings for Siphrix

# Allowed and blocked file types
SAFE_EXTENSIONS = {'.txt', '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.docx', '.xlsx'}
BLOCKED_EXTENSIONS = {'.exe', '.bat', '.cmd', '.sh', '.msi'}

# Inbox history file
HISTORY_FILE = "inbox_history.txt"

# WebSocket settings (optional for future use)
WS_HOST = "127.0.0.1"
WS_PORT = 8000
WS_PROTOCOL = "wss"
USAGE_FILE = "usage_stats.json"
GROUP_FILE = "groups.json"
PINNED_FILE = "pinned_messages.json"
