**Telegram Casino Bot**

This is a Telegram casino bot built with the aiogram library. It uses Telegram Stars as its in-app currency for various games, including dice and other casino-style games. The bot enables users to deposit, withdraw, and use their stars for playing games.

### Features

Casino Games: Play dice and other games with friends in Telegram groups.

Balance Management: Deposit and withdraw stars.

Commission Tracking: Keeps track of commissions for transactions.

### Requirements
Python 3.8 or higher

PostgreSQL

### Installation and Setup

1. Install PostgreSQL
   
Install PostgreSQL on your machine. You can download it from the official PostgreSQL website.

2. Create a Database

Once PostgreSQL is installed, create a database named payments_db. You can do this using the following commands in the PostgreSQL shell:
`CREATE DATABASE payments_db;`

3. Clone the Repository

Clone this repository to your local machine:
git clone https://github.com/nazar067/payments-tg.git
cd payments-tg

4. Install Python Dependencies

Create and activate a virtual environment:

`python3 -m venv venv`

`source venv/bin/activate  # For Linux/MacOS`

`venv\Scripts\activate     # For Windows`

Install the required Python packages:

`pip install -r requirements.txt`

5. Configure the Project

Rename the config.example.py file to config.py:

`cp config.example.py config.py`

Open the config.py file and fill in your credentials:

Telegram Bot Token: You can obtain this token from BotFather.

Database Connection String: Configure the DATABASE_URL for your PostgreSQL database.

Example:

`API_TOKEN = "your_telegram_bot_token"`

`DATABASE_URL = "postgresql://username:password@localhost:5432/payments_db"`

6. Start the Bot

Run the bot using the following command:

`python bot.py`

### Contributing
If you have suggestions or find any issues, feel free to open an issue or submit a pull request. Contributions are welcome!

### License
This project is licensed under the MIT License.
