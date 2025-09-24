# 📚 Multi-vault support
a
OBSIFLASK is **intended** to work in multi-vault settings: you can configure multiple vaults in your config, each with different settings.

## 📝 Task support

OBSIFLASK supports **periodical shell tasks** that can be configured separately for each vault.  
The messages about successful or unsuccessful task results, along with the program output, will be displayed on the [messages](/messages/example) page.


For example, in this vault, every 2 minutes the task `echo "hello world"` finishes successfully. You can see the corresponding message at the top of the OBSIFLASK page every 2 minutes.

# 🔎Search

OBSIFLASK also supports different **search modes**, which can be found on the [search page](/search/example): 
- Exact search
    
- Regular expression search
    
- Fuzzy search
    
- Tag search
    
- Link search (forward and backward)
    
- Filter search, similar to Bases filters (see [[Bases support]] for details)

# ⌨️ Hotkeys
Currently the only available hotkey is "Ctrl-s", which saves your markdown in editor. More hotkeys are in the plan.

# 🌗 Dark/Light mode

The dark/light mode changing is available. By default OBSIFLASK uses system settings. The dark mode is automatically loaded for the corresponding bootstrap theme, see [config](https://github.com/bahleg/OBSIFLASK/blob/main/obsiflask/config.py)