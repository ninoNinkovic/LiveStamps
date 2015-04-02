# LiveStamps for Sublime Text 3

####A Sublime Text 3 Plugin to inject self updating metadata into any document.

**Features:**

  * Insert self updating tags into docblock headers
  * Background highlighting, outlining, and guttermarking of livestamps. (each one is optional)
  * Timezone/DST aware timestamps with custom formatting
  * Track file metadata no matter where it is moved/renamed
  * Track date the document was last modified
  * Track user or person who last modified the file.
  * Add a checksum to the file
  * Update all your projects with a new email address or URL when it changes
  * Easy static/dynamic custom stamp creation with powerful custom/automatic regex matching
  * Inject stamps via keyboard, command palette, or menus
  * Toggle plugin settings directly from the UI with a keyboard shortcut or context menu

**Advanced Features:** 

* Menu generator, define as many stamps as you want and they are only a right click away
* Customize menu layout from the settings file, simply define a menu key to sort your stamps
* Use multiple values or other stamps within larger stamps... Great for a siggy!
* Go beyond simple metadata, perform conversions with powerful Python formatting
* Built-in help: Python format() & srtftime() live reference and data dump to test new designs
* Use powerful custom regexes or define global "auto" regex definitions, its up to you!
 
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

```json
# Generic Usage:

super + alt + letter -> inject a LiveStamp
ctrl  + alt + letter -> inject a raw value

# Example: All Stamps

Inject all stamps: super + alt + a     
Inject all values: ctrl  + alt + a      
```

####Menu Injection:

```
# Context Menu:

Right-click -> LiveStamps -> Insert Stamp -> type
Right-click -> LiveStamps -> Insert Value -> type
```

####Menu Generation:

By default LiveStamps has a right click context menu defined. If you prefer, the sidebar, tools and command pallate menus can be easily generated. **Menu generation should also be refreshed** whenever you add new stamp definitions in order to avoid using excessive keyboard shortcuts:

```
# Refresh Existing Menus:
Right-click -> LiveStamps -> Menus -> Refresh

# Generate a Menu:
Right-click -> LiveStamps -> Menus -> Build -> menutype

# Open Existing Menu To Manually Edit:
Right-click -> LiveStamps -> Menus -> Open -> menutype
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

```json
"mystamp": {
  "value": "LiveStamps rule!",
},

Output: LiveStamps rule!
```

####Key Reference:

```
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
[tflag]  : Time Formatting string. Python strftime() format flags i.e. "%d-%m-%Y"
```

####Stamp Values:

Values are the core meta for the stamp and can be defined as a single item, or list of values:

```json
# A String Literal:

"mystamp1": {
  "value": "zero",
},

Output: zero


# Single List Item:

"mystamp2": {
  "value": ["zero"],
},

Output: zero


# Multiple List Items:

"mystamp3": {
  "value": ["zero", 1, "two", 3],
},

Output: zero 1 two 3
```

####Magic Values:

By default LiveStamps generates some magic values to help get you started. File meta, last modified timestamp and user info gets creted on refresh automatically.

**More are planned in the future!**

```json
# The following stamps are auto generated:

"user"         : Gets current user
"checksum"     : Gets md5 hash of the current file (hash algorithm can be modified)
"extension"    : Gets current file extension
"base_name"    : Gets current basename
"file_size"    : Gets current filesize
"file_name"    : Gets current filename
"file_path"    : Gets current filepath
"parent_name"  : Gets name of parent folder
"parent_path"  : Gets path of parent folder
"file_extname" : Gets current filename with extension
"modified"     : Current timestamp using "%c" flag, as preferred local time.

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

```
SOURCE:
-------

"tic_tac": {
  "value": "Tic",
  "stamp": "{0} Tac",  // Don't worry about the {0}, it's covered next!
},

Output -> Tic Tac


USING THE SOURCE VALUE:
-----------------------

"tic": {
  "value": "_tic_tac",  // Leading underscore gets the "value" key of tic_tac
}

Output -> Tic


USING THE SOURCE STAMP:
-----------------------

"tic_tac_toe": {
  "value": "tic_tac",   // No underscore gets the formattad "stamp" key of tic_tac
  "stamp": "{0} Toe",
}

Output -> Tic Tac Toe
```

###Injection Flags:

Injection flags allow for POWERFUL formatting and complex stamp designs. If a "stamp" key is defined, each value gets mapped to the corresponding injection flag in the final output. 

**Injection flags are simple markers defined as so:**

```
'stamp': "{0} {1} {2}" // Explicit location (stamp values injected by index)
'stamp': "{} {} {}"    // Implicit location (stamp values injected sequentially
```

**Basic Injection: (all examples have the exact same output)**

```
# No injection

  "mystamp": {
    "value": "Have you heard? LiveStamps rule! Thanks TundraTech!",
  },

# Complete injection

  "mystamp": {
    "value": "Have you heard? LiveStamps rule! Thanks TundraTech!",
    "stamp": "{0}",
  },

# Partial injection (explicit)

  "mystamp": {
    "value": "LiveStamps rule!",
    "stamp": "Have you heard? {0} Thanks TundraTech!",
  },

# Partial injection (implicit)

  "mystamp": {
    "value": "LiveStamps rule!",
    "stamp": "Have you heard? {} Thanks TundraTech!",
  },

Output ->  Have you heard? LiveStamps rule! Thanks TundraTech!
```

####Multiple Injection Flags:

Stamps can easily accept multiple values/stamps and all values are generated recursively, allowing you to build sub dependencies as deep as you wish.

**Various outputs of "mystamp" using different injection flags:**

```
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

```json
"bases": {
  "value": 87,
  "stamp": "Base conversion: {0:d} - {0:x} - {0:o} - {0:b}",
},
		
Output: Base conversion:  87 - 57 - 127 - 1010111
```

**Getting even trickier: Getting nice alignment AND converting bases.**

```
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

```json
"date": {
  "value": "auto",
  "tflag": "%d-%m-%Y",
  "regex": "@date.+",
  "stamp": "@date        {0}",
},

Output: @date        08-03-2015

"time": {
  "value": "auto",
  "tflag": "%c",
  "regex": "@modified.+",
  "stamp": "@modified    {0}",
},

Output: @modified    Fri Mar  6 18:21:57 2015
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

```
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

```json
"ahead_ten_hours": {
  "value": "hours: 10",
  "tflag": "%c",
},

Output: Wed Apr  1 22:29:05 2015

"Maui time": {
  "value": "America/Honolulu",
  "tflag": "%c",
  "stamp": "Maui time is: {0}",
},

Output: Maui time is: Wed Apr  1 22:29:05 2015


# For raw timestamp output no format flags are specified.

"ten_minutes_thirty_seconds_ago": {
  "value": "[minutes=-10, seconds=-30]",
  "tflag": ""
},
```

###Regex Patterns

In order to make a stamp 'live' so that is updated whenever the document is modified, a regex pattern must be supplied. For docblock tags a built-in pattern is used. 

**WARNING!**

Regex patterns are powerful expressions!
    
Test your regex on a separate document before trying it on a master file! An expression that accidentally matches valid code, will instantly replace it. Also, a mistyped pattern that is too "loose" could replace a huge amount of data in a large file, potentially causing data loss or hardlock...

Test and learn more about REGEX patterns buy visiting [www.regexr.com](https://www.regexr.com "Regexr") or [www.regex101.com](https://regex101.com "Regex 101").


#### The Default Regex/Stamp Pattern

If you are making a stamp for use within docblock tags your best bet is to simply use the "auto" value for the regex and stamp keys respectively. In the following example, the default regex will inject stamp values to anything that appears after " * @mystamp "

**NOTE: After values are injected, anything is ERASED until the end of the line:** 

```
# Auto defined stamp/value:

"mystamp": {
  "value": "Is really cool",
  "regex": "auto",
  "stamp": "auto", 
 }
  
# Which would work great in a docblock header:

/**
 * @mystamp Is really cool   // But Anything here will always get erased on update
 */
```

**Actual values used after generation:**

```
  "mystamp": {
    "value": "Is really cool",
    "regex": "* @mystamp.+",
    "stamp": "* @mystamp {0}",
  },
```
The default regex paradigm can be modified in the settings file by editing the following keys.

**Careful! Changes will have a big effect:**

```
"autoregex" : " \\* @{0}.+",  // Stamp name injected at flag {0}
"autostamp" : " * @{0} {1}",  // Stamp name injected at flag {0}, values at {1}
"separator" : " ",            // Separator used for "auto" multi value stamps
```

Of course advanced users may use any regex pattern they desire, for instance date matching.

**Custom Regex for dd-mm-yyyy:**

```json

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

```
"tflag": "(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\s|\s\s)(\d|\d\d)\s(\d\d:\d\d:\d\d)\s\d\d\d\d"
```
