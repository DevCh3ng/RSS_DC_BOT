# RSS Discord Bot

This is a simple Discord bot that can monitor RSS feeds and send alerts for cryptocurrency prices.

## Features

- **RSS Feed Monitoring:** The bot can monitor multiple RSS feeds and post new articles to a specified channel.
- **Cryptocurrency Price Alerts:** Users can set price alerts for their favorite cryptocurrencies and receive a DM when the price target is reached.

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/DevCh3ng/RSS_DC_BOT.git
   cd RSS_DC_BOT
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file:**
   Create a `.env` file in the root directory of the project and add the following:
   ```
   DISCORD_TOKEN=your_discord_bot_token
   CHANNEL_ID=your_discord_channel_id
   ```

4. **Run the bot:**
   ```bash
   python bot.py
   ```

## Commands

### RSS

- `-rss`: Show the current RSS settings.
- `-rss add <url>`: Add an RSS feed to the list of monitored feeds.
- `-rss remove <index>`: Remove an RSS feed from the list.
- `-rss interval <minutes>`: Set the interval for checking the RSS feeds.

### Alerts

- `-alert`: Show the alert command help.
- `-alert add <crypto> <condition> <price>`: Set a price alert for a cryptocurrency. 
  - `crypto`: The name of the cryptocurrency (e.g., `bitcoin`).
  - `condition`: The price condition, either `>` or `<`.
  - `price`: The target price in USD.
- `-alert list`: List your active price alerts.
- `-alert remove <id>`: Remove a price alert.

### Other

- `-ping`: Check if the bot is online.