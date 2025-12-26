# tg-db-backup

A Telegram bot for automated database backups.

## Supported Databases

Currently, only PostgreSQL is supported.

To add support for more databases, implement a new class inheriting from `DatabaseBackup` in `common/db_backup.py` and add it to the `backup_handlers` dictionary in `BackupService.__init__`.

## Setup

1. **Prerequisites**

   - Python 3.10 or higher
   - uv package manager

2. **Install dependencies**

   ```bash
   uv sync
   ```

3. **Configuration**

   - Copy `sample.config.yaml` to `config.yaml` and configure your databases
   - Create a `.env` file with your Telegram API credentials:
     ```
     API_ID=your_api_id
     API_HASH=your_api_hash
     BOT_TOKEN=your_bot_token
     OWNER_ID=your_telegram_user_id
     ```

4. **Run the bot**
   ```bash
   python main.py
   ```
