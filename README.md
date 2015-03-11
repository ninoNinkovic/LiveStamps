# LiveStamps for Sublime Text 3

####A Sublime Text 3 Plugin to inject self updating metadata into any document.

####Features:  

  * Insert self updating tags into docblock headers
  * Background highlighting, outlining, and guttermarking of livestamps. (each one is optional)
  * Go beyond simple metadata, perform conversions, arithmetic or inject code snippets.
  * Timezone support, with DST 
  * Add predefined signatures, ascii art, or class header info
  * Automatically track file metadata no matter where it is moved/renamed
  * Track date the document was last modified
  * Track user or person who last modified the file.
  * Add a checksum to the file
  * Update all your projects with a new email address or URL when it changes
  * Easy static/dynamic custom stamp creation with powerful regex matching
  * Multipart stamps, or stamps made from other stamps. Great for a siggy!
  * Inject stamps via keyboard, command palette, tools, context, or sidebar menus
  * Toggle plugin settings directly from the UI with a keyboard shortcut or context menu
  * Powerful Python format() and strftime() formatting support for each value defined in a stamp
  
####Intall via Package Control: 

```
  1. Open Sublime Text 3
  2. cmd+shift+p
  3. Package Control: Install Package
  4. Search for LiveStamps
```

####Manual Install: 

```
  1. Open Sublime Text 3
  2. Sublime Text Menu -> Preferences -> Browse Packages
  3. Create folder called LiveStamps
  4. Copy this repo to the folder.
```



## USAGE:

LiveStamps will update automatically on save, but can also output the raw value as static data which is useful for things like the current time, filename, path, parent folder etc.

####Keyboard:

```json
# General Usage:
super + alt + letter -> inject a LiveStamp
ctrl  + alt + letter -> inject it's raw value

# Example: All stamps
Inject all stamps: super + alt + a     
Inject all values: ctrl  + alt + a      
```

####Menus:

```
# Context Menu:
Right-click -> LiveStamps -> stamp -> stamptype
Right-click -> LiveStamps -> value -> stampvalue

# Tools Menu:
Tools -> LiveStamps -> stamp -> stamptype
Tools -> LiveStamps -> value -> stampvalue

# Example: Time stamp
Right-click -> LiveStamps -> Stamp -> Time
Right-click -> LiveStamps -> Value -> Time
```

#### Using Command Pallete:

```
super+shift+p -> type in LiveStamps -> select an option
```

## Creating Custom Stamps:

  1. Open Sublime Text 3
  2. Menu: Sublime Text -> Preferences -> Package Settings -> LiveStamps -> Settings - Default
  3. Copy everything to clipboard.
  4. Menu: Sublime Text -> Preferences -> Package Settings -> LiveStamps -> Settings - User
  5. Paste and save.
  6. Modify stamp definitions in the "stamps" array at the bottom.
  7. If you make a mistake just copy from Settings - Default again.

###Anatomy of a LiveStamp:

**LiveStamps are defined as small python dictionaries with the minimum following keys:**

```json
"mystamp": {
  "value": "LiveStamps rule!",
},

Output: LiveStamps rule!
```

**Required Keys:**
```
[value]  : A string literal, or list. Setting as "auto" tries to find the value for you
```

**Optional Keys:**

```
[stamp]  : Formatting string. Cool and recommended 8). See injection flags below. 
[regex]  : Python regex pattern. If empty/excluded, the stamp will be static data.
[strft]  : Python strftime() format to apply to a time value i.e. "%d-%m-%Y"
```


####Stamp Values:

**Values can be defined as single item, or list of values:**

```json
"mystamp1": {
  "value": "zero",
},

Output: zero

"mystamp2": {
  "value": ["zero"],
},

Output: zero

"mystamp3": {
  "value": ["zero", 1, "two", 3],
},

Output: zero 1 two 3
```

**LiveStamps can also pull in some magic values for handy usage:**

```
"user"        : Gets current user
"checksum"    : Gets md5 hash of the current file
"extension"   : Gets current file extension
"base_name"   : Gets current basename
"file_size"   : Gets current filesize
"file_name"   : Gets current filename
"file_path"   : Gets current filepath
"parent_name" : Gets name of parent folder
"parent_path" : Gets path of parent folder

"mystamp": {
  "value": "file_size",
},

Output: 768 (in bytes)

More are planned in the future!
```
**Using Other Stamps as Values:**

Simply set any VALUE as the name of another stamp and PRESTO! The plugin tries to match any value with an existing key in the stamp dictionary before injection. This is great for signatures or other complex stamps.

**Using the "copyright" stamp within "mystamp":**

```json
"copyright": {
  "value": "(c) TundraTech 2015",
},
"mystamp": {
  "value": ["This stamp is", "copyright"],
},

Output: This stamp is (c) TundraTech 2015
```

####Injection flags:

Injection flags allow for POWERFUL formatting and complex stamp designs, but for now we start with the easy stuff 8). If a "stamp" key is defined, each value gets mapped to a corresponding injection flag in the final output. 

**Injection flags are simple markers defined as so:**

```
'stamp': "{0} {1} {2} {3}"
```

**Injecting values into a stamp. The following stamps all provide the exact same output:**

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

# Partial injection
"mystamp": {
  "value": "LiveStamps rule!",
  "stamp": "Have you heard? {0} Thanks TundraTech!",
},

Output: Have you heard? LiveStamps rule! Thanks TundraTech!
```
**Multiple Injection Flags:**

```json
# Various outputs of "mystamp" using different injection flags:

"mystamp": {
  "value": ["zero", "one", "two", "three"],
  "stamp": "@mystamp   {0} {1} {2} {3}",
},

# Normal Output: Each value is mapped to a Python format() flag:
"stamp" : "@mystamp   {0} {1} {2} {3}",
Output  :  @mystamp   zero one two three

# Mixed order is allowed and flags can be injected anywhere:
"stamp" : "@mystamp   {3} hello {1} {2} world {0}",
Output  :  @mystamp   three hello one two world zero

# Not all flags have to be used
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

Because each value defined gets passed through the Python format() function it allows LiveStamps to expand your expression far beyond simple metadata. Code snippets, powerful conversions and arithmetic are quick and easy to implement.

Learn more about available flags at [Python String Format Cookbook](https://mkaz.com/2012/10/10/python-string-format/ "Python String Format Cookbook")

**Convert the number 87 to different bases, decimal, hex, octal, binary:**

```json
"bases": {
  "value": 87,
  "regex": "@bases.+",
  "stamp": "@bases       {0:d} - {0:x} - {0:o} - {0:b}",
},
		
Output: @bases         87 - 57 - 127 - 1010111
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

####Time formatting: 

Time is formatted according to the Python strftime() function and as such requires a special stamp key. Learn about available flags at [www.strftime.org](http://strftime.org "Strftime")

Note the "auto" value, Which tells LiveStamps to grab the current time. 

```json
"date": {
  "value": "auto",
  "strft": "%d-%m-%Y",
  "regex": "@date.+",
  "stamp": "@date        {0}",
},

Output: @date        08-03-2015

"time": {
  "value": "auto",
  "strft": "%c",
  "regex": "@modified.+",
  "stamp": "@modified    {0}",
},

Output: @modified        Fri Mar  6 18:21:57 2015
```

**Adding Time Offsets:**

Time offsets allow creation of mutiple stamps with different timezones! A single offset as a raw string. When enterings offsets as a string, the colon ":" or '=" sign must be used as the delimete between unit and value. Fractional values are automatically handled and negative offsets are allowed.

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
  
**Offset Input Syntax... Highly Flexible!**

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
  "regex": "@plus10hrs.+",
  "stamp": "@plus10hrs        {0}",
},

"Maui time": {
  "value": "America/Honolulu",
  "strft": "%c",
  "regex": "@Maui.+",
  "stamp": "@Maui        {0}",
},

Raw timestamp output.
"ten_minutes_thirty_seconds_ago": {
  "value": "[minutes=-10, seconds=-30]",
},
```

####Regex Patterns

In order to make a stamp 'live' so that is updated whenever the document is saved, a regex pattern must be supplied. LiveStamps uses a simple "flag matching" paradigm which conforms nicely with docblock tags and is fairly safe/easy to implement:

```json
"regex": "@mystamp.+",
```

This regex would inject your stamp values to anything that appears after "@mystamp" until the end of the line. Of course advanced users may use any regex pattern they desire. For instance to match any dates in the document with the pattern dd-mm-yyyy the pattern would be:

```json
"regex": "(\\d\\d-\\d\\d-\\d\\d\\d\\d)",
```

**WARNING!**

Regex patterns are powerful expressions!
    
Test your regex on a separate document before trying it on a master file! An expression that accidentally matches valid code, will instantly replace it. Also, a mistyped pattern that is too "loose" could replace a huge amount of data in a large file, potentially causing data loss...

Test and learn more about REGEX patterns buy visiting [www.regexr.com](https://www.regexr.com "Regexr") or [www.regex101.com](https://regex101.com "Regex 101").






