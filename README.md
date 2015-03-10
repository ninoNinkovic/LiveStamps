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

Each "livestamp" is handled by regex and will update whenever the document is saved by default. Stamps can also output their raw value as static data which is useful for things like the current filename, path, parent folder or time, etc.

####Keyboard:

```json
General Usage:
super + alt + letter -> inject a stamp
ctrl  + alt + letter -> inject a stamp's raw value

Example: All stamps
To view all stamps: super + alt + a     
To view all values: ctrl  + alt + a      
```

####Menus:

```
Context Menu:
Right-click -> LiveStamps -> stamp -> stamptype
Right-click -> LiveStamps -> value -> stampvalue

Tools Menu:
Tools       -> LiveStamps -> stamp -> stamptype
Tools       -> LiveStamps -> value -> stampvalue

Example: Inject Time stamp
Right-click -> LiveStamps -> Stamp -> Time
Right-click -> LiveStamps -> Value -> Time
```

#### Using Command Pallete:

```
super+shift+p > type LiveStamps > select a stamp option
```

## Creating Custom Stamps:

  1. Open Sublime Text 3
  2. Menu: Sublime Text -> Preferences -> Package Settings -> LiveStamps -> Settings - Default
  3. Copy everything to clipboard.
  4. Menu: Sublime Text -> Preferences -> Package Settings -> LiveStamps -> Settings - User
  5. Paste and save.
  5. Modify stamp definitions in the "stamps" array at the bottom.
  6. If you make a mistake just copy from Settings - Default again.

###Anatomy of a LiveStamp:

**LiveStamps are defined as a small python dictionary with the minimum following keys:**

```json
"mystamp": {
  "value": "An important value i use often while programming",
  "stamp": "{0}",
},

Output: An important value i use often while programming
```

**Required Keys:**
```
[value]  : A string literal, or list. Setting as "auto" tries to find the value for you
[stamp]  : Output string. Value(s) are inserted at defined injection marker(s). See below.
```
**Optional Keys:**
```
[regex]  : Python regex pattern. If empty/excluded, the stamp is assumed static.
[strft]  : Python strftime() format to apply to a time value i.e. "%d-%m-%Y"
```

####Stamp Values:

Values can be string literals or a list of string literals. Both of the following stamps are valid and provide the exact same output:

```json
"mystamp1": {
  "value": "zero",
  "stamp": "{0} one",
},
"mystamp2": {
  "value": ["zero", "one"],
  "stamp": "{0} {1}",
},

Output: zero one
```

**Using Other Stamps as Values:**

The plugin tries to match any value that you define with an existing key in the stamp dictionary before injection: 
```json
To use the "copyright" stamp within "mystamp", set a "mystamp" VALUE as "copyright". 

"copyright": {
  "value": "(c) TundraTech 2015",
  "stamp": "{0}",
},
"mystamp": {
  "value": ["This stamp is", "copyright"],
  "stamp": "@mystamp   {0} {1}",
},

Output: @mystamp   This stamp is (c) TundraTech 2015
```

####Basic Injection flags:

Each value defined gets mapped to a Python format() flag contained within the "stamp" key.The following example shows how you can get various outputs from the same stamp just by using modifying the injection flags:

```json
# Various outputs of "mystamp" using different injection flags:

"mystamp": {
  "value": ["zero", "one", "two", "three"],
  "regex": "@mystamp.+",
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

Because each value defined actually gets mapped as a Python format() string. This allows for POWERFUL formatting. Learn more about available flags at [Python String Format Cookbook](https://mkaz.com/2012/10/10/python-string-format/ "Python String Format Cookbook")

The following would format convert the number 87 to different bases, decimal, hex, octal, binary

```json
"bases": {
  "value": 87,
  "regex": "@bases.+",
  "stamp": "@bases       {0:d} - {0:x} - {0:o} - {0:b}",
},
		
Output: @bases         87 - 57 - 127 - 1010111

# Getting even trickier: PHP sprintf() like formatting to get nice alignment.

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

**As you can see the potential for LiveStamps to expand your expression goes far beyond simple metadata. Code snippets, powerful conversions and arithmetic are quick and easy to implement.**


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






