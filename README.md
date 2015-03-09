# LiveStamps for Sublime Text 3
A Sublime Text 3 Plugin to inject self updating metadata into any document.

Create your own custom stamps! LiveStamps is handy for things like:

  * Inserting metadata in docblock headers, that update automatically.
  * Adding predefined signatures or class header info
  * Tracking file meta no matter where it is moved/renamed
  * The date the document was last modified
  * The user or person who last modified the file.
  * Updating projects with a new email address or URL
  
Stamps can be dynamic (update on save, or key binding) or static, single use values for injection to save time.

----
### INSTALLATION:

Just hit a key combo to inject, after that stamps are auto updated on save !

Keep in mind this plugin is using regex to find and replace the "stamps" so define them here but leave them alone once injected in the document. Changing a stamp format or layout manually once a stamp is in the document will cause the regex to fail ...or worse... insert incorrectly.


####Package Control: 
 * Open Sublime Text 3
 * cmd+shift+p
 * Package Control: Install Package
 * Search for TimeStamps

####Manual: 
Copy this repo to a LiveStamps folder in your ST3 Packages directory. 
 * Open Sublime Text 3
 * Sublime Text Menu -> Preferences -> Browse Packages
 * Create folder called LiveStamps
 * Copy this repo to the folder.

----
### USAGE:

Just hit a key combo to inject, after that stamps are auto updated on save !

Keep in mind this plugin is using regex to find and replace the "stamps" so define them here but leave them alone once injected in the document. Changing a stamp format or layout manually once a stamp is in the document will cause the regex to fail ...or worse... insert incorrectly.
