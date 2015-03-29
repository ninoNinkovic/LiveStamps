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
 
####Installation: 

```
# Via Package Control:

  1. Open Sublime Text 3
  2. cmd+shift+p
  3. Package Control: Install Package
  4. Search for LiveStamps
  
# Manual Install:  

  1. Open Sublime Text 3
  2. Sublime Text Menu -> Preferences -> Browse Packages
  3. Create folder called LiveStamps
  4. Copy this repo to the folder.
```

####Fill In User Info:
```
  1. Right-click -> LiveStamps -> Preferences -> Settings - Default
  2. Fill in "user_info" key accordingly
```

## USAGE:

Each LiveStamp has a formatted output and a raw value accessed in the following ways:

####Keyboard Injection:

```json
# Generic Usage:

super + alt + letter -> inject a LiveStamp
ctrl  + alt + letter -> inject it's raw value

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

By default LiveStamps has a right click context menu defined but the sidebar menu, tools menu and the command pallate can be easily generated if you prefer. This should also be done whenever you add new stamp definitions to avoid using excessive keyboard shortcuts:

```
# To Generate a Menu:

Right-click -> LiveStamps -> Preferences -> Menu Generation -> Build -> menutype
```

## Creating Custom Stamps:

  1. Open Sublime Text 3
  2. Right-click -> LiveStamps -> Preferences -> Settings - Default
  3. Copy everything to clipboard.
  4. Right-click -> LiveStamps -> Preferences -> Settings - User
  5. Paste and save.
  6. Modify stamp definitions in the "stamps" array at the bottom.
  7. If you make a mistake just copy from Settings - Default again.

###Anatomy of a LiveStamp:

LiveStamps are defined as small python dictionaries that let you easily define exact stamp output, regex matching and context menu location.

**A LiveStamp has the minimum following keys:**

```json
"mystamp": {
  "value": "LiveStamps rule!",
},

Output: LiveStamps rule!
```

**Required Keys:**

```
[name]   : Parent key with actual name of the stamp using snake_case
[value]  : A string literal, or list of values to be used for injection.
```

**Optional Keys:**

```
[stamp]  : Formatting string. Python format() flags. See injection flags below. 
[tflag]  : Time Formatting string. Python strftime()format flags i.e. "%d-%m-%Y"
[regex]  : Regex pattern. Set to auto for docblock. Exclude for static data.
[menu]   : Groups a stamp under a submenu in the right-click context menu
```


####Stamp Values:

Values can be defined as a single item, or list of values:

```json

# String Literal:

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

```
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

# Personal data built from "user_info" key in LiveStamps.sublime-settings:

"author"      : Your name here                                  
"vendor"      : Your company here                                     
"email"       : Your email here                              
"website"     : Your website here                     
"quote"       : A quote you like

More are planned in the future!
```

###"Super" Stamps

Simply set any "value" key as the name of another stamp and PRESTO! The plugin will match it with definitions in the existing stamp dictionary and pull in the output. Use a leading _underscore in front of the name to get the raw value instead of the formatted output. This is great for signatures or other complex stamps!

**The leading _underscore grabs a stamp's value instead:**

```
SOURCE:
-------

"tic_tac": {
  "value": "Tic",
  "stamp": "{0} Tac",
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

###Injection flags:

Injection flags allow for POWERFUL formatting and complex stamp designs. If a "stamp" key is defined, each value gets mapped to the corresponding injection flag in the final output. 

**Injection flags are simple markers defined as so:**

```
'stamp': "{0} {1} {2}" // Explicit location (stamp values injected by index)
'stamp': "{} {} {}"    // Implicit location (stamp values injected sequentially
```

**Basic Injection: (all of the following provide the exact same output) **

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

Stamps can easily accept multiple values/stamps. All values are generated recursively so you can build sub dependencies as deep as you wish.

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

Because each value defined gets passed through the Python format() function it allows LiveStamps to expand your expression far beyond simple metadata. Code snippets and powerful conversions are quick and easy to implement. Learn more about available flags at [Python String Format Cookbook](https://mkaz.com/2012/10/10/python-string-format/ "Python String Format Cookbook").

**Refer to the built in format reference for help with building new stamps:**

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

**Refer to the built-in strftime() reference for help with building new TimeStamps:**

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

Output: @modified        Fri Mar  6 18:21:57 2015
```

**Adding Time Offsets:**

Time offsets allow creation of stamps with different timezones or delays/advances. You may enter a single offset as a raw string. When entering offsets as a string, the colon ":" or '=" sign must be used as the delimeter between unit and value. Fractional values are automatically handled and negative offsets are allowed.

Here are the allowed offset units:

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

**Formatted Offset Examples With Regex:**

```json
"ahead_ten_hours": {
  "value": "hours: 10",
  "strft": "%c",
},

"Maui time": {
  "value": "America/Honolulu",
  "strft": "%c",
  "regex": "Maui time is:.+ ",
  "stamp": "Maui time is: {0}",
},

Raw timestamp output.
"ten_minutes_thirty_seconds_ago": {
  "value": "[minutes=-10, seconds=-30]",
},
```

###Regex Patterns

In order to make a stamp 'live' so that is updated whenever the document is modified, a regex pattern must be supplied. Advanced users can feel free to define any regex pattern they wish, however for docblock tags a built-in pattern is supplied. 

### The default Regex/stamp pattern

If you are using a stamp within docblock tags your best bet is to simply use the "auto" value for the regex and stamp keys respectively. This tells LiveStamps to use a simple "flag matching" paradigm which conforms nicely with docblock tags and is fairly safe/easy to implement:

```
# Auto defined stamp regex:
"mystamp": {
  "value": "Is really cool",
  "regex": "auto",
  "stamp": "auto", 
  
Output: * @mystamp        Is really cool

# Which would work great in a header:

/**
 *
 * @mystamp        Is really cool
 */

# Actual values used:
"regex": "* @Maui.+",
"stamp": "* @Maui {0}",
},
```

The default regex will inject your stamp values to anything that appears after:

" * @mystamp" 

**until the end of the line.** 

Of course advanced users may use any regex pattern they desire. For instance to match any dates in the document with the pattern dd-mm-yyyy a possible regex pattern could be:

```json
"regex": "(\\d\\d-\\d\\d-\\d\\d\\d\\d)",
```

Th default regex paradigm can be modified in the settings file by editing the following keys:

```
"autoregex" : " \\* @{0}.+",  // Stamp name is injected into regex pattern at flag {0}
"autostamp" : " * @{0} {1}",  // Stamp name is injected at flag {0}, values at {1}
"separator" : " ",            // Separator used when multiple values are defined
```

**WARNING!**

Regex patterns are powerful expressions!
    
Test your regex on a separate document before trying it on a master file! An expression that accidentally matches valid code, will instantly replace it. Also, a mistyped pattern that is too "loose" could replace a huge amount of data in a large file, potentially causing data loss...

Test and learn more about REGEX patterns buy visiting [www.regexr.com](https://www.regexr.com "Regexr") or [www.regex101.com](https://regex101.com "Regex 101").






