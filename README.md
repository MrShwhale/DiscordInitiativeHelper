# DiscordInitiativeHelper
A Discord bot to help manage initiative rounds in Dungeons and Dragons

## Running/installation
To run, download main.py, replace the string "\<TOKEN>" with a discord bot token.

Then, simply run the file.

## Usage
Add to your server, then use the ?set command on the channel you want. 

It will render the chosen channel unusable since it deletes all messages sent in that channel

Command overview is available by using the ?help command


## How to add character macros
Characters allow for macros that make common rolls (such as PCs) very fast, and more intuitive

Create a text file, and add characters in this form: "\<Name> \<Initiative Mod> \<Advantage? (t or f)>"

Only put one character on each line, use _ instead of spaces

Once the file is set up, pass the file path as an argument to the "set_up_character_list()" call
