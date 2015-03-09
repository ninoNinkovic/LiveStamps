# LiveStamps for Sublime Text 3
A Sublime Text 3 Plugin to inject self updating metadata into any document.

####Great For:  

 * Inserting metadata in docblock headers, that update automatically.
 * Adding predefined signatures or class header info
 * Tracking file meta no matter where it is moved/renamed
 * The date the document was last modified
 * The user or person who last modified the file.
 * Updating projects with a new email address or URL

####Features:  

 * Easy static/dynamic custom stamp creation with powerful regex matching
 * Multipart stamps, or stamps made from other stamps. Great for a siggy!
 * (any or all of) Background highlighting, outlining, and guttermarking of livestamps 
 * Inject stamps or values via keyboard shortcut, Sublime Command, tools menu, context menu, or sidebar menu
 * Toggle plugin settings directly from the UI with a keyboard shortcut or context menu
 * timezone support, with DST
 * Python format() and strftime() format string support within stamps




Stamps can be dynamic (update on save, or key binding) or static, single use values for injection to save time.

####Package Control: 

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

### USAGE:
----

Just hit a key combo to inject a stamp, and it will automagically take care of itself! Each stamp has a "livestamp"  handled by regex for auto updating, and a raw value which can be injected for a static instance.

Defaults key combos are:
 * super + alt + letter -> inject stamp(s)
 * ctrl  + alt + letter -> inject raw value(s)

You can see the available stamps by right clicking





