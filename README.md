# LiveStamps for Sublime Text 3

####A Sublime Text 3 Plugin to inject self updating metadata into any document.

**Features:**

  * **Metadata** - Insert self updating tags into docblock headers
  * **Highlighting** - Background, outlining, and/or guttermarking.
  * **TimeStamps** - Timezone/DST aware stamps with custom formatting and manual offsets
  * **File metadata** - Automatically keep track of file info whenever it is moved/renamed
  * **Last Modified** - Track the exact moment the document was last updated
  * **User Info** - Sharing a file lets you know who did what and when.
  * **Checksum** - Add an md5 Hash to the file (sha also supported)
  * **Contact Info** - Auto update your projects with a new email address or URL when changed
  * **Custom Stamps** - Easy creation with powerful custom/auto regex matching
  * **Flexible Input** - Inject stamps via keyboard, command palette, or menus
  * **Easy Configuration** - Toggle most plugin settings directly from the UI

**Advanced Features:** 

* **Menu Generator** - Define as many stamps as you want and they are only a right click away
* **Customize Menu** - Simply define a menu key to sort your stamps
* **SuperStamps** - Use multiple values or other stamps within larger stamps... Great for a siggy!
* **Go Beyond Metadata** - Perform conversions with powerful Python formatting
* **Built-in Help** - Python format() & srtftime() live reference and data dump to test new designs
* **Flexible Regexes** - Custom per stamp or global "auto" regex patterns, its up to you!
 
**COMING SOON:**

Language Specific Code Snippets and Definitions

A great potential use for LiveStamps exists in the ability to switch between stamp defenitions depending on the document you are working with. Definition files containing javascript, SASS, PHP snippets will be easily accessible through the menu.

Document type detection/auto menu generation is already implemented, it is for the most part a matter of simply writing the definition files:

**Assistance creating language specific definition files with code snippets would be very much appreciated!**

#### Installation: 

```
# Package Control:

  1. Open Sublime Text 3
  2. cmd+shift+p
  3. Package Control: Install Package
  4. Search for LiveStamps
  
# Manual Install:  

  1. Open Sublime Text 3
  2. Sublime Text Menu -> Preferences -> Browse Packages
  3. Create folder called LiveStamps
  4. Copy the contents of this repo to the folder.
```

#### Setup User Info:
```
  1. Right-Click -> LiveStamps -> Definitions -> Open
  2. Fill in "user_info" key accordingly
  3. You may add custom keys here if you like
```

**Note, By default LiveStamps updates dynamic stamps on save, to disable for safety:**

```
Right-Click -> LiveStamps -> Preferences -> Update On Save
```

## USAGE:

Each LiveStamp has a formatted and raw value. A raw value is usally used as a one-time static injection, i.e. frequently used variables. However, when a regex is added to a stamp definition, matching patterns are updated automatically. For instance, the @modified stamp will update itself whenever the document is saved.

Formatted and raw values are accessed in the following ways:

####Keyboard Injection:

```python
# Generic Usage:

[super] + [alt] + [letter]   # Injects a formatted value
[ctrl]  + [alt] + [letter]   # Injects a raw value

# Example: All Stamps

[super] + [alt] + a          # Injects all formatted values   
[ctrl]  + [alt] + a          # Injects all raw values
```

####Menu Injection:

```python
# Context Menu:

Right-click -> LiveStamps -> Insert Stamp -> type
Right-click -> LiveStamps -> Insert Value -> type
```

####Command Pallate:

```python
1. Right-click -> LiveStamps -> Menu -> Build -> Command      # Only needed first time
2. Command + shift + p
3. Type LiveStamps to see list of commands, enter to execute.
```

####Menu Generation:

The default LiveStamps config uses the right-click context menu only. If you prefer, the sidebar/tools/command pallate menus can be easily generated. Menu generation should also be refreshed when new stamp definitions are added in order to avoid using excessive keyboard shortcuts:

```python
# Refresh Existing Menus:
Right-click -> LiveStamps -> Menus -> Refresh

# Generate a Menu:
Right-click -> LiveStamps -> Menus -> Build -> menutype

# Open Existing Menu To Manually Edit:
Right-click -> LiveStamps -> Menus -> Open -> menutype
```

###Stamp Definition Import/Export & Backup:

Livestamps supports a simple stamp versioning system that allows you to easily share or backup your custom stamp definitions.

**Backup/Import/Export/Rename Definitions:**
```
 # Backup Existing Stamps & User Info:
 Right-Click -> LiveStamps -> Definitions -> Backup

 # Restore Previous Stamp Definitions:
 Right-Click -> LiveStamps -> Definitions -> Restore -> [definition file]

 # To Rename Definitions:
 1. Right-Click -> LiveStamps -> Definitions -> Browse
 2. Rename any files as you wish (keep .sublime-settings extension)
 
 # To Import or Share Definitions:
 1. Right-Click -> LiveStamps -> Definitions -> Browse
 2. Copy any stamp definition files to or from this directory to import/export
```

## Creating Custom Stamps:

```
  1. Right-Click -> LiveStamps -> Definitions -> Open
  2. Custom stamp definitions are defined within the "stamps" key
  3. There are a few examples and instructions to get you started here as well
```

###Anatomy of a LiveStamp:

LiveStamps are defined as small python dictionaries that contain stamp output, regex patterns, formatting flags and menu location. Defining new stamps is extremly simple, but advanced users can get quite complex once they get the hang of it. Let's get started!

**A LiveStamp has the minimum following keys:**

```python
"mystamp": {
  "value": "LiveStamps rule!",
},

# Output: LiveStamps rule!
```

####Key Reference:

```python
# Stamp Keymap:

"[name]": {
  "[menu]"  : string,
  "[value]" : int|string|list *dict can be used for time offsets*
  "[regex]" : string,
  "[stamp]" : string,
  "[tflag]" : string,
},

# Required Keys:

[name]   : The parent key containing the stamp name using snake_case
[value]  : A string/int literal, or list of values to be used for injection.

# Optional Keys:

[menu]   : Groups a stamp under a submenu in the right-click context menu
[regex]  : Regex pattern. Set to auto for docblock. Exclude for static data.
[stamp]  : Formatting string. Python format() flags. See injection flags below. 
[tflag]  : Time Formatting string. Python strftime() flags i.e. "%d-%m-%Y"
```

####Stamp Values:

A value is the core meta for a stamp and can be defined as a single item, or list of values:

```python
"mystamp1": {
  "value": "zero",        # A String Literal
},

# Output: zero

"mystamp2": {
  "value": ["zero"],      # Single List Item
},

# Output: zero

"mystamp3": {
  "value": [1, "two", 3]  # Multiple Item Lis:
},

# Output: 1 two 3
```

####Magic Values:

LiveStamps will generate some magic values to help get you started. File meta, last modified timestamp and user info gets creted on refresh automatically.

**More are planned in the future!**

```python
# The following stamps are auto generated:

"user"         : Gets current user
"checksum"     : Gets checksum of the current file (algorithm can be modified)
"extension"    : Gets current file extension
"base_name"    : Gets current basename
"file_size"    : Gets current filesize
"file_name"    : Gets current filename
"file_path"    : Gets current filepath
"parent_name"  : Gets name of parent folder
"parent_path"  : Gets path of parent folder
"file_extname" : Gets current filename.extension
"modified"     : Current timestamp using "%c" flag, (preferred local time)

# From "user_info" key in LiveStampsDefinitions.sublime-settings:

"author"      : "Your name here"                                  
"vendor"      : "Your company here"                                     
"email"       : "Your email here"                              
"website"     : "Your website here"                     
"quote"       : "A quote you like"

# Custom info may be added to the "user_info" key if you wish:

"location"    : "Whitehorse, Yukon",
"fav_color"   : "Green",
"gender"      : "male"
```

###SuperStamps

SuperStamps are stamps built from other stamps or values. Simply set any "value" key as the name of another stamp and *PRESTO* the plugin will match it with definitions in the stamp dictionary. Use a *leading _underscore* in front of the name to get the raw value instead of the formatted output. This is great for signatures or other complex stamps!

**SuperStamp: Tic Tac Toe**

```python
SOURCE:
-------

"tic_tac": {
  "value": "Tic",
  "stamp": "{0} Tac",  # Don't worry about the {0}, it's covered next!
},

# Output -> Tic Tac


USING THE SOURCE VALUE:
-----------------------

"tic": {
  "value": "_tic_tac",  # Leading underscore gets the "value" key of tic_tac
}

# Output -> Tic


USING THE SOURCE STAMP:
-----------------------

"tic_tac_toe": {
  "value": "tic_tac",   # No underscore gets the formattad "stamp" key of tic_tac
  "stamp": "{0} Toe",
}

# Output -> Tic Tac Toe
```

###Injection Flags:

Injection flags allow for POWERFUL formatting and complex stamp designs. If a "stamp" key is defined, each value gets mapped to the corresponding injection flag in the final output. 

**Injection flags are simple markers defined as so:**

```
'stamp': "{0} {1} {2}" # Explicit location (stamp values injected by index)
'stamp': "{} {} {}"    # Implicit location (stamp values injected sequentially
```

**Basic Injection: (all examples have the exact same output)**

```python
# No injection:

  "mystamp": {
    "value": "Have you heard? LiveStamps rule! Thanks TundraTech!",
  },

# Complete injection:

  "mystamp": {
    "value": "Have you heard? LiveStamps rule! Thanks TundraTech!",
    "stamp": "{0}",
  },

# Partial injection (explicit):

  "mystamp": {
    "value": "LiveStamps rule!",
    "stamp": "Have you heard? {0} Thanks TundraTech!",
  },

# Partial injection (implicit):

  "mystamp": {
    "value": "LiveStamps rule!",
    "stamp": "Have you heard? {} Thanks TundraTech!",
  },

Output ->  Have you heard? LiveStamps rule! Thanks TundraTech!
```

####Multiple Injection Flags:

Stamps can easily accept multiple values/stamps and all values are generated recursively, allowing you to build sub dependencies as deep as you wish.

**Various outputs of "mystamp" using different injection flags:**

```python
SOURCE STAMP
--------------

"mystamp": {
  "value": ["zero", "one", "two", "three"],
  "stamp": "@mystamp   {0} {1} {2} {3}",
},

# Normal Output: Each value is mapped to a Python format() flag:

  "stamp" : "@mystamp   {0} {1} {2} {3}",
  Output  :  @mystamp   zero one two three


# Mixed ordering is allowed and flags can be injected anywhere:

  "stamp" : "@mystamp   {3} hello {1} {2} world {0}",
  Output  :  @mystamp   three hello one two world zero


# Not all values have to be mapped to a flag

  "stamp" : "@mystamp   {0} {1}",
  Output  :  @mystamp   zero one


# It's OK to define more flags used than values to allow for future expansion

  "stamp" : "@mystamp   {0} {1} {2} {3} {4} {5} {6} {7}",
  Output  :  @mystamp   zero one two three


# Using a flag more than once is OK.

  "stamp" : "@mystamp   {0} {0} {0} {0} {1} {2} {3} {0}",
  Output  :  @mystamp   zero zero zero zero one two three zero


# Using no flags is also OK.

  "stamp" : "@mystamp   ",
  Output  :  @mystamp   
```

####Advanced Formatting With Injection Flags: 

Because each value defined gets piped through the Python format() function it allows LiveStamps to expand your expression beyond simple metadata. Code snippets and powerful conversions are quick and easy to implement. Learn more about available flags at [Python String Format Cookbook](https://mkaz.com/2012/10/10/python-string-format/ "Python String Format Cookbook").

**Open the format() quick reference for help when building new stamps:**

```
Right Click -> LiveStamps -> Help -> format() Reference
```

**Example: Convert number 87 to different bases in decimal, hex, octal, binary:**

```python
"bases": {
  "value": 87,
  "stamp": "Base conversion: {0:d} - {0:x} - {0:o} - {0:b}",
},
		
# Output: Base conversion:  87 - 57 - 127 - 1010111
```

**Getting even trickier: Getting nice alignment AND converting bases.**

```python
"formatted_bases": {
  "value": [87, "\nDecimal","\nHex", "\nOctal", "\nBinary"],
  "stamp": "{1:<10}: {0:d} {2:<10}: {0:x} {3:<10}: {0:o} {4:<10}: {0:b}",
},
	
Output:

Decimal  : 87 
Hex      : 57 
Octal    : 127 
Binary   : 1010111

```

###TimeStamps: 

Time is formatted according to the Python strftime() function and as such requires a special "tflag" key. Learn about available formatting flags at [www.strftime.org](http://strftime.org "Strftime")

**Open the strftime() quick reference for help when building new stamps:**

```
Right Click -> LiveStamps -> Help -> strftime() Reference
```

**Note the "auto" value, which grabs the current local time as defined in settings**

```python
"date": {
  "value": "auto",
  "tflag": "%d-%m-%Y",
  "regex": "@date.+",
  "stamp": "@date        {0}",
},

# Output: @date        08-03-2015

"time": {
  "value": "auto",
  "tflag": "%c",
  "regex": "@modified.+",
  "stamp": "@modified    {0}",
},

# Output: @modified    Fri Mar  6 18:21:57 2015
```

**Adding Time Offsets:**

Time offsets allow creation of stamps with different timezones or delays/advances. You may enter a single offset as a raw string. When entering offsets as a string, the colon ":" or '=" sign must be used as the delimiter between unit and value. *Fractional values are automatically handled and negative offsets are allowed.*

Allowed offset units:

  * "microseconds"
  * "milliseconds"
  * "seconds"
  * "minutes"
  * "hours"
  * "days"
  * "weeks"
  * "months"
  * "years"
  
**Offset Input Syntax is Highly Flexible!**

```python
# String literal
"value": "microseconds: -21709870.5",

# Timezone support
"value": "America/Whitehorse",

# Multiple offsets in a list
"value": ["years: 10", "weeks: 3"],

# Multiple offsets in a dictionary
"value": {"months": -1.5, "seconds" :30},
```

**Formatted Offset Examples:**

```python
"ahead_ten_hours": {
  "value": "hours: 10",
  "tflag": "%c",
},

# Output: Wed Apr  1 22:29:05 2015

"Maui time": {
  "value": "America/Honolulu",
  "tflag": "%c",
  "stamp": "Maui time is: {0}",
},

# Output: Maui time is: Wed Apr  1 22:29:05 2015
```

**For Raw Timestamp No Flags Are Specified:**

```python
"ten_minutes_thirty_seconds_ago": {
  "value": "[minutes=-10, seconds=-30]",
  "tflag": ""
},
```

###Regex Patterns: Default DocBlock Regex

In order to make a stamp 'live' so that is updated whenever the document is modified, a regex pattern must be supplied. For docblock tags a built-in pattern can be used for convenience with one caveat: 

**Anything appearing after a docblock stamp is ERASED until a newline occurs**

If you are making a stamp for use within docblock tags your best bet is to simply use the "auto" value for the regex and stamp keys respectively. In the following example, the default regex will inject stamp values to anything that appears after " * @mystamp "

**Default Docblock Example:**

```python
# Auto defined stamp/value:

"mystamp": {
  "value": "Is really cool",
  "regex": "auto",
  "stamp": "auto", 
 }
  
# Which would work great in a docblock header:

/**
 * # Anything here is safe
 * @mystamp Is really cool   # Anything over here is always erased on update
 * # Anything here is safe
 */
```

**Actual values used after generation: (for reference)**

```python
  "mystamp": {
    "value": "Is really cool",
    "regex": "* @mystamp.+",
    "stamp": "* @mystamp {0}",
  },
```

###Custom Regex Definitions

**WARNING!**

Regex patterns are powerful expressions!
    
Test your regex on a separate document before trying it on a master file! An expression that accidentally matches valid code, will instantly replace it. Also, a mistyped pattern that is too "loose" could replace a huge amount of data in a large file, potentially causing data loss or hardlock...

Test and learn more about REGEX patterns buy visiting [www.regexr.com](https://www.regexr.com "Regexr") or [www.regex101.com](https://regex101.com "Regex 101").


**Modifying The Default Regex Pattern:**

```python
Right-Click -> LiveStamps -> Preferences -> Settings - User

# CAUTION!!! Changes here will have a big, potentially dangerous effect:

"autoregex" : " \\* @{0}.+",  # Stamp name injected at flag {0}
"autostamp" : " * @{0} {1}",  # Stamp name injected at flag {0}, values at {1}
"separator" : " ",            # Separator used for "auto" multi value stamps
```

Of course advanced users may use any regex pattern they desire, for instance date matching. You must be extra careful not to make your patterns too loose and remember to escape slashes and other regex sensitive characters because the input is in JSON format.

**Custom Regex for dd-mm-yyyy:**

```python

# Note the escaped backslashes because input is in JSON.

  "date": {
    "value": "Date is: ",
    "tflag": "%d-%m-%Y",
    "regex": "Date is (\\d\\d-\\d\\d-\\d\\d\\d\\d)",
    "stamp": "{0}",
  },

# Output: Date is 28-03-2015  
```

**Custom Regex for "Sat Mar 28 21:11:31 2015"**

```python

# Matches "%c" format flag

"tflag": "(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\s|\s\s)(\d|\d\d)\s(\d\d:\d\d:\d\d)\s\d\d\d\d"
```
