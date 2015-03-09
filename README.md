# LiveStamps for Sublime Text 3
####A Sublime Text 3 Plugin to inject self updating metadata into any document.

####Great For:  

  * Inserting self updating metadata into docblock headers
  * Adding predefined signatures or class header info
  * Tracking file meta no matter where it is moved/renamed
  * The date the document was last modified
  * The user or person who last modified the file.
  * Adding a checksum to the file
  * Updating all your projects with a new email address or URL when it changes

####Features:  

  * Easy static/dynamic custom stamp creation with powerful regex matching
  * Multipart stamps, or stamps made from other stamps. Great for a siggy!
  * (any or all of) Background highlighting, outlining, and guttermarking of livestamps 
  * Inject stamps or values via keyboard shortcut, Sublime Command, tools menu, context menu, or sidebar menu
  * Toggle plugin settings directly from the UI with a keyboard shortcut or context menu
  * timezone support, with DST
  * Python format() and strftime() format string support within stamps

### INSTALLATION:
----

####Package Control: 

  * Open Sublime Text 3
  * cmd+shift+p
  * Package Control: Install Package
  * Search for LiveStamps

####Manual: 

  * Open Sublime Text 3
  * Sublime Text Menu -> Preferences -> Browse Packages
  * Create folder called LiveStamps
  * Copy this repo to the folder.

### USAGE:
----

Just hit a key combo to inject a stamp, and it will automagically take care of itself! Each stamp has a "livestamp"  handled by regex for auto updating, and a raw value which is static, useful for things liek the current filename, path, parent folder or time, etc.

####Defaults key combos are:
 * super + alt + letter -> inject the stamp
 * ctrl  + alt + letter -> inject the stamp's raw value

You can see the available default stamps by right clicking and exploring the LiveStamps context menu.


### Creating Custom Stamps:

 Anatomy of a LiveStamp
----------------------------------------------------------------------------------------------------

  LiveStamp key definitions:

  id     : *REQUIRED* Unique identifier for the stamp, i.e. "name", "signature" etc.
  
  value  : *REQUIRED* Can be a static value or "auto". The plugin will try to determin auto stamps for you
  stamp  : *REQUIRED* The format string for the stamp. Stamp value(s) are inserted at tag marker(s) i.e. "{0} {1} {2}"
  regex  : *OPTIONAL* Python regex pattern for livestamps. If empty or excluded, the stamp is injected as a static value.
  parts  : *OPTIONAL* A list to define a stamp from other stamps, or multiple values. i.e. "parts": ["name", "email", "link"]
  format : *OPTIONAL* Python format() string argument to apply to the stamp's value
  strft  : *OPTIONAL* Python strftime() string argument to apply to a time value i.e. "%d-%m-%Y"

	**** WARNING *********************************************************
  * Regex patterns are powerful expressions!
  *
  * Test your stamp regex online at a site like www.regexr.com first!!!
  *
  * An expression that accidentally matches valid code, will instantly
  * replace it. A mistyped pattern that is too "loose" could replace a
  * huge amount of data in a large file, potentially causing a hardlock
  * or data loss...
  **********************************************************************


	Basic Static Example:
  ===================================================================================

 	A basic stamp with a constant output that doesnt auto update.

  	"mystamp": {
		  "value": "An important value i use often while while programming",
		  "stamp": "{0}",
  	},

	Output: An important value i use often while while programming


	Formatted Time LiveStamp Example:
  ===================================================================================

  A stamp which would auto update the current date every day. Note the "auto" value,
  Which tells LiveStamps to grab the current time. A constant Python time value could
  be entered here as well, allowing static time inputs...though I can't see a good
  reason for that lol.

  	"date": {
  		"value": "auto",
  		"strft": "%d-%m-%Y",
  		"regex": "@date.+",
  		"stamp": "@date        {0}",
  	},

   Output: @date        08-03-2015


	Multi-part LiveStamp Example:
  ===================================================================================

  A stamp with a "live" output that would update the year value automatically.
  Note, for this to stamp to auto update the previous "date" stamp would have to be
  defined. If the "date" stamp was NOT defined" the output would be:

  	@copyright   (c) TundraTech date

  However, the stamp would still be "live" because a regex was supplied. A change to
  any of its values would still cause an auto update, allowing you to enter a static
  date if desired, instantly updating all existing stamps in a document automatically.

  Changing the regex however, would abandon all the the previous stamps. Careful!

    "copyright": {
    	"value": "(c) TundraTech",
    	"parts": ["copyright", "date"],
    	"regex": "@copyright.+",
    	"stamp": "@copyright   {0} {1}",
    },

	Output: @copyright   (c) TundraTech 08-03-2015

--------------------------------------------------------------------------------------




