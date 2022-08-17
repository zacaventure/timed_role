# setting up the bot
## 1) Creating the .env file
Create a file in the time bot folder named: .env <br />
In that file you will need to add all of these variable: <br />
```
TOKEN = "Your bot token"
BACKUP_DIR = "The directory used for backup" 
TIMEZONE = "Your timezone" 
```
For the timezones, a complete list is available [here](https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568). You have the put the exact name
## 2) Creating log directory
Create a log directory in the timed_role project

## 3) installing requirements
```
pip install -r requirements.txt
```
## 4) Running the bot
```
python .
```