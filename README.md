# LiveStamps for Sublime Text 3

####A Sublime Text 3 Plugin to inject self updating metadata into any document.

####Features:  

  * Insert self updating tags into docblock headers
  * Add predefined signatures or class header info
  * Track file meta no matter where it is moved/renamed
  * Track date the document was last modified
  * Track user or person who last modified the file.
  * Add a checksum to the file
  * Update all your projects with a new email address or URL when it changes
  * Easy static/dynamic custom stamp creation with powerful regex matching
  * Multipart stamps, or stamps made from other stamps. Great for a siggy!
  * Optional background highlighting, outlining, or guttermarking of livestamps 
  * Inject stamps via keyboard, command palette, tools, context, or sidebar menus
  * Toggle plugin settings directly from the UI with a keyboard shortcut or context menu
  * timezone support, with DST
  * Python format() and strftime() formatting support within stamps
  
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


####Anatomy of a LiveStamp:

Livestamps are defined as a small python dictionary with the following keys:

```
# Required Keys:

[value]  : A string literal, or list. Setting as "auto" tries to find the value for you
[stamp]  : Output string. Value(s) are inserted at defined injection marker(s). See below.

# Optional Keys:

[regex]  : Python regex pattern. If empty/excluded, the stamp is assumed static.
[strft]  : Python strftime() format to apply to a time value i.e. "%d-%m-%Y"
[format] : For advanced users, a Python format() argument to apply to each stamp value
```

Each value that is defined gets mapped to a Python format() flag contained within the "stamp" key. The following example shows how you can get various outputs from the same stamp just by using changing the injection flags.

**Injection flag examples:**

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


**Stamp Values:**

Values can be string literals or a list of string literals. Both of the following examples are valid and provide the exact same output. 

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

**Using other stamps as values:**

The plugin tries to match any value that you define with an existing key in the stamp dictionary before injection: 
```json
To use the "copyright" stamp within "mystamp", set one of the "mystamp" the VALUES as "copyright". 

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

##Regex Patterns: Making a "LIVE" Stamp

In order to make a stamp 'live' so that is updated whenever the document is saved, a regex pattern must be supplied.

WARNING!

Regex patterns are powerful expressions!
    
Test your stamp regex online at a site like [www.regexr.com](https://www.regexr.com "Regexr") first!!! An expression that accidentally matches valid code, will instantly replace it. Also, a mistyped pattern that is too "loose" could replace a huge amount of data in a large file, potentially causing data loss...

To learn more about REGEX patterns visit [www.regexr.com](https://www.regexr.com "Regexr") or [www.regex101.com](https://regex101.com "Regex 101") to learn more.

**The default regex schema used by LiveStamps conforms with docblock tags and is fairly safe/easy to implement:**

```json
"regex": "@mystamp.+",
```

This will inject your stamp values to anything that appears after "@mystamp" until the end of the line. Of course advanced users may use any regex pattern you want such as:

```json
"regex": "(\\d\\d-\\d\\d-\\d\\d\\d\\d)",
```

Which would match any items in the document with the pattern dd-mm-yyyy such as

*18-02-2015
*25-12-1999
*02-03-1979


** MAKE SURE YOU CHOOSE A SAFE REGEX PATTERN PARADIGM! GENERIC REGEX PATTERNS CAN BE RISKY. MUCH BETTER TO USE A FLAG MATCHING REGEX, LIKE THE DEFAULT ONE USED BY LIVESTAMPS**




```json
```

**Time formatting:**

Time is formatted according to the Python strftime() function. If a stamp us defined with a "strft" key, this formatting is automatically applied to each value.
```json
```







## Stamp examples

####Basic Stamp (static data): 

A stamp with a constant output.

```json
"mystamp": {
  "value": "An important value i use often while programming",
  "stamp": "{0}",
},

Output: 

An important value i use often while programming

```




####"Live" Stamp Example (with time formatting): 

A live updating stamp to insert the current date.

Note the "auto" value, Which tells LiveStamps to grab the current time. A constant Python time value could be entered as the value as well, allowing a static time inputs.

```json
"date": {
  "value": "auto",
  "strft": "%d-%m-%Y",
  "regex": "@date.+",
  "stamp": "@date        {0}",
},

Output: 

@date        08-03-2015
```



####Multi-part LiveStamp : 

A multi-value live updating stamp which uses another LiveStamp as one of the components.

This stamp would maintain the date portion automatically for you on save. Note, for this to stamp to auto update the previous "date" example would also have to be defined.

Note: the order of definitions is **NOT** important, you can define parts before or after a multipart stamp.

```json
"copyright": {
  "value": ["(c) TundraTech", "date"],
  "regex": "@copyright.+",
  "stamp": "@copyright   {0} {1}",
},

Output:

@copyright   (c) TundraTech 08-03-2015
```

As an exercise, let's examine what happens if the "date" stamp was NOT defined. The output would be assumed to be two static values as so:

```
@copyright   (c) TundraTech date
```

However, the stamp would still be considered "live" because a regex was supplied. 

Because the stamp is still "live", changing either value in the list would instantly update all existing stamps matching the regex within the document, allowing you to make a document-wide change to a static date or a different company name if desired. 

**Note:**

**Changing the regex would abandon all previously inserted "copyright" stamps, rendering them as static/permanent... Careful!**



