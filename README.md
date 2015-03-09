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

**Just hit a key combo, or select a stamp from the context menu...  Easy!**

You can see all the default stamps by right clicking and exploring the LiveStamps context menu. Each "livestamp" is handled by regex and will update whenever the document is saved (by default auto_update is set to true). Stamps can also ouput their raw value as static data which is useful for things like the current filename, path, parent folder or time, etc.

####Using keyboard:

```
General Example:
super + alt + letter -> inject a stamp
ctrl  + alt + letter -> inject a stamp's raw value

Example: inject all defined stamps.

super + alt + a                        
ctrl  + alt + a      
```

####Using menu:

```
General:
Right-click > LiveStamps > stamp > stamptype
Right-click > LiveStamps > value > stampvalue
Tools       > LiveStamps > stamp > stamptype
Tools       > LiveStamps > value > stampvalue

Example: inject all available stamps.

Right-click > LiveStamps > stamp > all
Right-click > LiveStamps > value > all
```

#### Using Command Pallete:

```
super+shift+p > type LiveStamps > select a stamp option
```

## Creating Custom Stamps:

Live stamps are defined within the *LiveStamps.sublime-settings* file in JSON format. The best way to learn is by browsing/modifying the default stamp examples.

To view the default examples:

```
  1. Open Sublime Text 3
  2. Sublime Text Menu -> Preferences -> Package Settings -> LiveStamps -> Settings - Default
  3. Scroll down the file and have a look at the stamp definitions
```

**WARNING!**

Regex patterns are powerful expressions!
    
Test your stamp regex online at a site like [www.regexr.com](https://www.regexr.com "Regexr") first!!! An expression that accidentally matches valid code, will instantly replace it. Also, a mistyped pattern that is too "loose" could replace a huge amount of data in a large file, potentially causing data loss...

####Anatomy of a LiveStamp:

```
[value]  : REQUIRED literal string, or list. Setting as "auto" tries to find the value for you

[stamp]  : REQUIRED Injection flag string. Value(s) are inserted at defined tag marker(s)

[regex]  : OPTIONAL Python regex pattern. If empty/excluded, the stamp is assumed static.

[strft]  : OPTIONAL Python strftime() format to apply to a time value i.e. "%d-%m-%Y"

[format] : OPTIONAL For advanced users, a Python format() argument to apply to each stamp value
```

**Stamp Values:**

Stamp values can be string literals or a list of string literals. Both of the following examples are valid and provide the exact same output. 

```json
"mystamp": {
  "value": "zero",
  "stamp": "{0} one",
},

Output: zero one

"mystamp": {
  "value": ["zero", "one"],
  "stamp": "{0} {1}",
},

Output: zero one
```

**Using other stamps as values:**

Other stamps can be used as values. The plugin tries to match any defined value with an existing key in the stamp dictionary before injection. In the following example to use the "copyright" stamp within "mystamp", set one of the values as "copyright". 

```json
"copyright": {
  "value": "(c) TundraTech 2015",
  "stamp": "{0}",
},
"mystamp": {
  "value": ["This stamp is", "copyright"],
  "stamp": "@mystamp   {0} {1}",
},

Output: @mystamp   This stamp is (c) TundraTech 2015

Note: if you need to use the word "copyright" in a stamp, but you also have a "copyright" stamp defined, it is totally fine. Instead of defining "copyright" as a value simply add it it to the injection string literally:

"mystamp": {
  "value": ["This stamp is"],
  "stamp": "@mystamp   {0} copyright",
},

Output: @mystamp   This stamp is copyright

Easy!
```

**Stamp injection flags:**

Each defined value is mapped to a Python format() flag and can be used anywhere within the stamp output. Have a look at some injection flag fun below. The example shows how you can get various outputs from the same stamp just by using different injection flags.

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

# Using a flag more than once is OK. 8)
"stamp" : "@mystamp   {0} {0} {0} {0} {1} {2} {3} {0}",
Output  :  @mystamp   zero zero zero zero one two three zero
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



