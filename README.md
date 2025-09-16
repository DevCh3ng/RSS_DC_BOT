# RSS & Crypto Alert Discord Bot

A powerful and highly configurable Discord bot that provides cryptocurrency price alerts, on-demand price checks, and advanced RSS feed monitoring to keep your server organized and updated.

## Features

- **Advanced RSS Monitoring:** Assign RSS feeds to specific channels, filter articles by keywords, and set server-wide and per-channel feed limits.
- **Granular Permissions:** A role-based permission system allows server owners to delegate RSS management to specific roles without granting full admin privileges.
- **Crypto Price Alerts:** Get a direct message when a cryptocurrency of your choice goes above or below a certain price.
- **On-Demand Price Checks:** Instantly fetch detailed price information for any cryptocurrency.

## Commands

All commands use the `-` prefix.

### General Commands

-   `**-help**`
    Displays a complete and organized list of all available commands.
-   `**-ping**`
    Checks if the bot is online and responsive.

---

### Server Administration (Admins Only)

These commands are for server owners and administrators to configure the bot's core settings and permissions.

-   `**-rssadmin add @role**`
    Allows a role to manage RSS feeds (use `-rss` commands).

-   `**-rssadmin remove @role**`
    Removes a role's ability to manage RSS feeds.

-   `**-rssadmin list**`
    Lists all roles currently authorized to manage RSS feeds.

-   `**-rss limit <count>**`
    Sets the maximum total number of RSS feeds allowed on this server (max 30).

-   `**-channelconfig limit #channel <count>**`
    Sets a specific limit on how many RSS feeds can be assigned to a single channel.

-   `**-channelconfig allow_multiple #channel <true|false>**`
    Toggles whether a channel can have more than one RSS feed assigned to it.

---

### RSS Feed Management

Can be used by Administrators or users with a role authorized by `-rssadmin`.

-   `**-setchannel #channel-name**`
    Sets the default channel for RSS updates. Feeds added without a specific channel will post here.

-   `**-rss**`
    Shows the current RSS settings for the server, including the check interval, default channel, and a list of all configured feeds with their channels and keywords.

-   `**-rss add <url> [#channel]**`
    Adds a new RSS feed. You can optionally specify a channel for it to post in.
    *Example: `-rss add http://www.theverge.com/rss/index.xml #tech-news`*

-   `**-rss remove <index>**`
    Removes an RSS feed using its index number from the `-rss` list.

-   `**-rss interval <minutes>**`
    Sets the global interval for how often the bot checks for new articles (min 5).

-   `**-rss keywords add <index> <keyword>**`
    Adds a keyword filter to a feed. The bot will only post articles from this feed if they contain the keyword.

-   `**-rss keywords remove <index> <keyword>**`
    Removes a keyword filter from a feed.

-   `**-rss keywords list <index>**`
    Lists all active keywords for a specific feed.

---

### Crypto Commands (Available to all users)

-   `**-price <cryptocurrency>**`
    Fetches the current price, 24h change, market cap, and volume for a specific crypto.
    *Example: `-price bitcoin`*

-   `**-alert add <crypto> <condition> <price>**`
    Sets a personal price alert. The bot will DM you when the condition is met.
    *Example: `-alert add ethereum < 4000`*

-   `**-alert list**`
    Lists all of your currently active price alerts with their corresponding IDs.

-   `**-alert remove <ID>**`
    Removes a specific price alert using the ID from your alert list.

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
    Create a `.env` file in the root directory and add your bot's token.
    ```env
    DISCORD_TOKEN=your_discord_bot_token
    ```

4.  **Run the bot:**
    ```bash
    python bot.py
    ```