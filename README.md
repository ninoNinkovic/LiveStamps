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

### INSTALLATION:
----
####Package Control: 
 * Open Sublime Text 3
 * cmd+shift+p
 * Package Control: Install Package
 * Search for LiveStamps

####Manual: 
Copy this repo to a LiveStamps folder in your ST3 Packages directory. 
 * Open Sublime Text 3
 * Sublime Text Menu -> Preferences -> Browse Packages
 * Create folder called LiveStamps
 * Copy this repo to the folder.

----
### USAGE:

Just hit a key combo to inject a stamp, and it will automagically take care of itself! Each stamp has a "livestamp"  handled by regex for auto updating, and a raw value which can be injected for a static instance.

Defaults are:
 * super+alt+letter -> inject stamp(s)
 * ctrl+alt+letter  -> inject stamps raw value(s)






