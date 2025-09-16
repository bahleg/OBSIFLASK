OBSIFLASK supports basic naviagation across the vaults and basic file operations.

It also supports wikilinks with the behaviour similar to Obisidian.
# 📁 Navigation
OBSIFLASK supports basic navigation across vaults and basic file operations.  
It also supports wikilinks with behavior similar to Obsidian.

To navigate, use the file tree on the left side of the page.

On each page, you will see the full path to the current file, including its directory. Clicking a directory in the path opens the corresponding folder page.  
For example: [[.|the root folder page]].  
**(This type of link is not supported in Obsidian, since Obsidian does not have folder pages.)**

# 📄 File operations
In the sidebar you can find a button "File operations", which brings you to [this page](/fileop/example). 
The file operations are:

	- New file/folder

	- Delete file/folder

	- Move file/folder

	- Copy file/folder
	
When creating a file, you can optionally select a template, if a template folder is set in the [config](https://github.com/bahleg/OBSIFLASK/blob/main/src/obsiflask/config.py). For example, for this vault you can use a [[digit]] template.
# 🔗 Links
LOBSIDIAN supports both Markdown links and wikilinks.

An example of [markdown link](https://github.com/bahleg/OBSIFLASK/tree/main).
## Wiki links resolution
OBSIFLASK resolves wikilinks according to the following rules:

1. **Full path:**  
    If the link contains the full path to a file, it resolves directly to that file.  
    Example: [[readme]]
    
2. **Relative path:**
    
    - If only one file matches the relative path, it resolves to that file.  
        Example: [[relative path example]]
        
    - If multiple files match the same path, it resolves to the first matching file.  
        Example: [[1.md]]
        

Additionally, OBSIFLASK supports links without file extensions.  
For example, [[1]] resolves to `1.md`.

The broken links are rendered in a special way: [[This is broken link]].


# ⚠️ Notes about file index
The file index is updated periodically (by default, every 5 minutes, configurable in the [config](https://github.com/bahleg/OBSIFLASK/blob/main/src/obsiflask/config.py)). It is also refreshed after each file operation.  This logic will be refactored in the future.

Keep in mind: if you move a file from outside of your vault, it may be temporary hidden in the index.
