# RSS & Crypto Alert Discord Bot

A versatile Discord bot that provides cryptocurrency price alerts, on-demand price checks, and RSS feed monitoring to keep your server updated.

## Features

- **RSS Feed Monitoring:** Automatically posts new articles from any RSS feed into a designated channel.
- **Crypto Price Alerts:** Get a direct message when a cryptocurrency of your choice goes above or below a certain price.
- **On-Demand Price Checks:** Instantly fetch detailed price information for any cryptocurrency.
- **Easy Management:** Simple and intuitive commands for managing feeds, alerts, and settings.

## Commands

All commands use the `-` prefix.

### General Commands

-   `**-help**`
    Displays a complete and organized list of all available commands.
-   `**-ping**`
    Checks if the bot is online and responsive.

### Configuration

-   `**-setchannel #channel-name**`
    Sets the specific channel where the bot will post all RSS feed updates. This requires "Manage Channels" permission.

### Crypto Commands

-   `**-price <cryptocurrency>**`
    Fetches the current price, 24h change, market cap, and volume for a specific crypto.
    *Example: `-price bitcoin`*

-   `**-alert add <crypto> <condition> <price>**`
    Sets a personal price alert. The bot will DM you when the condition is met.
    *Example: `-alert add ethereum < 4000`*

-   `**-alert list**`
    Lists all of your currently active price alerts with their corresponding IDs.

-   `**-alert remove <ID>**`
    Removes a specific price alert using the ID from the alert list.
    *Example: `-alert remove 3`*

### RSS Commands

-   `**-rss**`
    Shows the current RSS settings, including the check interval and the list of all configured feeds with their index numbers.

-   `**-rss add <url>**`
    Adds a new RSS feed to the monitoring list. Requires administrator permissions.
    *Example: `-rss add http://www.theverge.com/rss/index.xml`*

-   `**-rss remove <index>**`
    Removes an RSS feed from the list using its index number. Requires administrator permissions.
    *Example: `-rss remove 2`*

-   `**-rss interval <minutes>**`
    Sets how often the bot checks for new articles. The minimum interval is 5 minutes. Requires administrator permissions.
    *Example: `-rss interval 15`*

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/DevCh3ng/RSS_DC_BOT.git
    cd RSS_DC_BOT
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Create a `.env` file:**
    Create a `.env` file in the root directory and add your bot's token and a default channel ID.
    ```env
    DISCORD_TOKEN=your_discord_bot_token
    CHANNEL_ID=your_default_discord_channel_id
    ```
    *Note: The `CHANNEL_ID` is used as a fallback. It is recommended to set a channel per-server using the `-setchannel` command.*

4.  **Run the bot:**
    ```bash
    python bot.py
    ```
