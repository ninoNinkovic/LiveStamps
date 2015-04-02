import sublime, subprocess, time, sublime_plugin, getpass, shutil, hashlib, re, ntpath, os, sys, json
from datetime import datetime, timedelta
from collections import OrderedDict
from random  import randint


#== GLOBALS =============================================================================

# Settings Object
s = sublime.load_settings("LiveStamps.sublime-settings")

# Stamp Meta
m = s.get("default_stamps")


#== WORKERS =============================================================================


class LiveStampsOpenFolderCommand(sublime_plugin.TextCommand):


  ''' Opens A Folder '''


  def run(self, view, folder=sublime.packages_path()):

    self.view.run_command( "live_stamps_definitions", { "task" : "check_dir" } );

    platform = sublime.platform()

    if platform == "osx":
      subprocess.Popen(['open', folder])
    elif platform == "windows":
      subprocess.Popen(['explorer', folder])
    elif platform == "linux":
      subprocess.Popen(['xdg-open', folder])

    msg = "LiveStamps: Opening folder " + folder
    self.view.run_command( "live_stamps_notify", { "message" : msg, "modes" : "console status" } )


 # def is_visible(self, paths =[]):
 #   return sublime.platform() == 'osx'


class LiveStampsWriteFileCommand(sublime_plugin.TextCommand):


  ''' Save Data To A File '''


  def run(self, view, fname, contents=False):

    ftemp = open(fname, "wb")

    if contents:
      ftemp.write(bytes(contents, 'UTF-8'))
    else:
      ftemp.write(self.get_text())

    ftemp.close

    msg = "LiveStamps: Writing file " + fname
    self.view.run_command( "live_stamps_notify", { "message" : msg, "modes" : "console status" } )

class LiveStampsInjectCommand(sublime_plugin.TextCommand):


  ''' Injects a string into the current view '''


  def run(self, edit, data = ""):

    # Insert the stamp(s) into the document
    for pos in self.view.sel():

      # Insert at each cursor location
      if pos.empty():
        self.view.insert(edit, pos.a, data)

      # Replace selected area(s) with stamp
      else:
        self.view.replace(edit, pos, data)


class LiveStampsNotifyCommand(sublime_plugin.TextCommand):


  ''' Shows Various Sublime Notifications '''


  def run(self, view, message, modes="console status"):

    global s

    # Check init and grab fresh meta if needed
    if s.get("console_events") == None:
      self.view.run_command( "live_stamps_refresh" )

    # Print a console message
    if s.get("console_events") and 'console' in modes:
      if 'clear' in modes or isinstance(s.get("console_events"), str):
        print('\n'*50)
      print (message)

    # Send a popup message
    if s.get("popup_events"):
      if 'error' in modes:
        sublime.error_message(message)
      if 'dialog' in modes:
        sublime.message_dialog(message)

    # Send a statusbar notification
    if s.get("statusbar_events") and 'status' in modes:
      sublime.status_message(message)


class LiveStampsRefreshCommand(sublime_plugin.TextCommand):


  ''' Build LiveStamp & Value Metadata '''


  def run(self, view):

    # Update our global variables
    global s
    global m

    # Load master settings object
    s = sublime.load_settings("LiveStamps.sublime-settings")

    # Load Default settings, initialize metadata dictionary
    if s.get("restore_defaults") == True:
      self.view.run_command( "live_stamps_defaults", { "mode": "settings" } );

    self.view.run_command( "live_stamps_definitions", { "task" : "merge" } );

    # Get current filepath, contents from view and timezones
    self.path      = self.view.file_name()
    self.data      = self.view.substr(sublime.Region(0, self.view.size()))
    self.timezones = self.tzinfo()

    # Get magic values and stamp alignment
    self.magic_values()
    self.docalign  = self.get_docalign()
    self.maxwidth  = len(max(m.keys(), key=len))

    # Let er rip... construct final stamp metadata
    self.refresh_stamps()


  #-- Construct Stamp Meta  -------------------------------------------------------------


  # Gets a valid docalign value
  def get_docalign(self):

    # Check if stamp alignment enabled, and get length of our widest stamp name
    docalign = s.get('doc_align')

    # Try to idiot proof user input by forcing positive int or None
    if docalign != None and isinstance(docalign, int):
      return 0 if docalign < 0 else docalign
    else:
      return None

  # Aligns our docblock stamps nicely
  def doc_align(self, stamp):

    # If alignment is enabled
    if self.docalign != None and ' * @' in stamp:

      # Get the index of our flag
      idx = stamp.index(' * @') + len(' * @')

      # Get our widest stamp
      maxlength = self.maxwidth + self.docalign

      # Trim Excess space and force consistent alignement
      for i, space in enumerate(stamp):
        if space == " " and i > idx:
          formatter = "{0:<"+ str(maxlength) +"s}{1}"
          lead      = stamp[:idx]
          left      = stamp[idx:i].rstrip()
          right     = stamp[i:].strip()
          aligned   = formatter.format(left, right)
          return lead + aligned

    return stamp

  # Recursively get the true value of a stamp.
  def true_values(self, stamp, value_output=True):

    # If a list was passed, dig deeper.
    if isinstance(stamp, list):
      values = []

      # Find the true value for each item in the list
      for part in stamp:
        values.append( self.true_values(part, False) )

      return values

    name = str(stamp).lstrip('_')

    # If the value is another stamp, investigate.
    if name in m :

      value = ""

      # If the stamp is a TimeStamp, get time and format
      if "tflag" in m[name]:
        value = self.time_stamp( m[name]["value"], m[name]["tflag"] )

      # Otherwise, load the stamp and recurse one last time
      else:
        value = self.true_values( m[name]["value"], False )

      # If the stamp has injection flags, load them or use defaults
      layout = m[name]["stamp"] if "stamp" in m[name] else "{0}"

      # Format multiple values
      if isinstance(value, list):

        # Count injection flags
        flag_count = layout.count('{')

        # Add blanks when tuple index out of range,
        while (flag_count > len(value)):
          value.append("")

        layout = self.doc_align(layout.format(*value))

      # Format single value
      else:
        layout = self.doc_align(layout.format(value))

      # Store final values, all recursion has completed.
      if value_output:
        m[name]['stamp_output'] = layout
        m[name]['value_output'] = value

      # Return a recursed and formatted sub-stamp
      else:
        return layout if stamp[0] != "_" else value

    # Only reach here on non stamp base stamp values
    return stamp

  # Build and format final stamp and value outputs
  def refresh_stamps(self):

    # Iterate each stamp definitions...
    for stamp, info in m.items():

      # Check stamp is OK

      check = True

      # Check a value has been define
      if 'value' not in info:
        m[stamp]['value'] = ""

        # Inform the user of the state change, via status bar and console
        msg = "LiveStamps: Stamp '" + stamp + "' has no value defined"
        self.view.run_command( "live_stamps_notify", { "message" : msg, "modes" : "console status" } )

      # Check for self recursion (infinite loop)
      else:
        value = info['value']

        # Cast to list if needed
        if not isinstance(value, list):
          value = [value]

        # Check value(s) for infinite loop
        for item in value:
          if item == stamp:

            # Set the fail condition
            check = False

            # Inform the user of the state change, via status bar and console
            msg = "LiveStamps:\n\n...Infinite Loop!\n\nStamp '" + stamp + "' has a value that refers to self. \n\nA LiveStamp cannot have a value equal to it's own name. Change the name or value to repair."
            self.view.run_command( "live_stamps_notify", { "message" : msg, "modes" : "console status error" } )

      if check:
        # Get the 'true' values of the stamp (other stamps, times and magic values)
        self.true_values(stamp)


  #-- Time Helpers ----------------------------------------------------------------------


  # Get a dictionary of the Olson timezones, offsets, DST offsets and abbreviations
  def tzinfo(self):

    return {
      "Africa/Abidjan"                   : ["+00:00", "+00:00", "GMT"],
      "Africa/Accra"                     : ["+00:00", "+00:00", "GMT"],
      "Africa/Addis_Ababa"               : ["+03:00", "+03:00", "EAT"],
      "Africa/Algiers"                   : ["+01:00", "+01:00", "CET"],
      "Africa/Asmara"                    : ["+03:00", "+03:00", "EAT"],
      "Africa/Bamako"                    : ["+00:00", "+00:00", "GMT"],
      "Africa/Bangui"                    : ["+01:00", "+01:00", "WAT"],
      "Africa/Banjul"                    : ["+00:00", "+00:00", "GMT"],
      "Africa/Bissau"                    : ["+00:00", "+00:00", "GMT"],
      "Africa/Blantyre"                  : ["+02:00", "+02:00", "CAT"],
      "Africa/Brazzaville"               : ["+01:00", "+01:00", "WAT"],
      "Africa/Bujumbura"                 : ["+02:00", "+02:00", "CAT"],
      "Africa/Cairo"                     : ["+02:00", "+02:00", "EET"],
      "Africa/Casablanca"                : ["+00:00", "+00:00", "WET"],
      "Africa/Ceuta"                     : ["+01:00", "+01:00", "CET"],
      "Africa/Conakry"                   : ["+00:00", "+00:00", "GMT"],
      "Africa/Dakar"                     : ["+00:00", "+00:00", "GMT"],
      "Africa/Dar_es_Salaam"             : ["+03:00", "+03:00", "EAT"],
      "Africa/Djibouti"                  : ["+03:00", "+03:00", "EAT"],
      "Africa/Douala"                    : ["+01:00", "+01:00", "WAT"],
      "Africa/El_Aaiun"                  : ["+00:00", "+00:00", "WET"],
      "Africa/Freetown"                  : ["+00:00", "+00:00", "GMT"],
      "Africa/Gaborone"                  : ["+02:00", "+02:00", "CAT"],
      "Africa/Harare"                    : ["+02:00", "+02:00", "CAT"],
      "Africa/Johannesburg"              : ["+02:00", "+02:00", "SAST"],
      "Africa/Juba"                      : ["+03:00", "+03:00", "EAT"],
      "Africa/Kampala"                   : ["+03:00", "+03:00", "EAT"],
      "Africa/Khartoum"                  : ["+03:00", "+03:00", "EAT"],
      "Africa/Kigali"                    : ["+02:00", "+02:00", "CAT"],
      "Africa/Kinshasa"                  : ["+01:00", "+01:00", "WAT"],
      "Africa/Lagos"                     : ["+01:00", "+01:00", "WAT"],
      "Africa/Libreville"                : ["+01:00", "+01:00", "WAT"],
      "Africa/Lome"                      : ["+00:00", "+00:00", "GMT"],
      "Africa/Luanda"                    : ["+01:00", "+01:00", "WAT"],
      "Africa/Lubumbashi"                : ["+02:00", "+02:00", "CAT"],
      "Africa/Lusaka"                    : ["+02:00", "+02:00", "CAT"],
      "Africa/Malabo"                    : ["+01:00", "+01:00", "WAT"],
      "Africa/Maputo"                    : ["+02:00", "+02:00", "CAT"],
      "Africa/Maseru"                    : ["+02:00", "+02:00", "SAST"],
      "Africa/Mbabane"                   : ["+02:00", "+02:00", "SAST"],
      "Africa/Mogadishu"                 : ["+03:00", "+03:00", "EAT"],
      "Africa/Monrovia"                  : ["+00:00", "+00:00", "GMT"],
      "Africa/Nairobi"                   : ["+03:00", "+03:00", "EAT"],
      "Africa/Ndjamena"                  : ["+01:00", "+01:00", "WAT"],
      "Africa/Niamey"                    : ["+01:00", "+01:00", "WAT"],
      "Africa/Nouakchott"                : ["+00:00", "+00:00", "GMT"],
      "Africa/Ouagadougou"               : ["+00:00", "+00:00", "GMT"],
      "Africa/Porto-Novo"                : ["+01:00", "+01:00", "WAT"],
      "Africa/Sao_Tome"                  : ["+00:00", "+00:00", "GMT"],
      "Africa/Timbuktu"                  : ["+00:00", "+00:00", "GMT"],
      "Africa/Tripoli"                   : ["+01:00", "+02:00", "EET"],
      "Africa/Tunis"                     : ["+01:00", "+01:00", "CET"],
      "Africa/Windhoek"                  : ["+01:00", "+02:00", "WAST"],
      "America/Adak"                     : ["−10:00", "-09:00", "HADT"],
      "America/Anchorage"                : ["−09:00", "-08:00", "AKDT"],
      "America/Anguilla"                 : ["−04:00", "-04:00", "AST"],
      "America/Antigua"                  : ["−04:00", "-04:00", "AST"],
      "America/Araguaina"                : ["−03:00", "-03:00", "BRT"],
      "America/Argentina/Buenos_Aires"   : ["−03:00", "-03:00", "ART"],
      "America/Argentina/Catamarca"      : ["−03:00", "-03:00", "ART"],
      "America/Argentina/ComodRivadavia" : ["−03:00", "-03:00", "ART"],
      "America/Argentina/Cordoba"        : ["−03:00", "-03:00", "ART"],
      "America/Argentina/Jujuy"          : ["−03:00", "-03:00", "ART"],
      "America/Argentina/La_Rioja"       : ["−03:00", "-03:00", "ART"],
      "America/Argentina/Mendoza"        : ["−03:00", "-03:00", "ART"],
      "America/Argentina/Rio_Gallegos"   : ["−03:00", "-03:00", "ART"],
      "America/Argentina/Salta"          : ["−03:00", "-03:00", "ART"],
      "America/Argentina/San_Juan"       : ["−03:00", "-03:00", "ART"],
      "America/Argentina/San_Luis"       : ["−03:00", "-03:00", "ART"],
      "America/Argentina/Tucuman"        : ["−03:00", "-03:00", "ART"],
      "America/Argentina/Ushuaia"        : ["−03:00", "-03:00", "ART"],
      "America/Aruba"                    : ["−04:00", "-04:00", "AST"],
      "America/Asuncion"                 : ["−04:00", "-04:00", "PYT"],
      "America/Atikokan"                 : ["−05:00", "-05:00", "EST"],
      "America/Atka"                     : ["−10:00", "-09:00", "HADT"],
      "America/Bahia"                    : ["−03:00", "-03:00", "BRT"],
      "America/Bahia_Banderas"           : ["−06:00", "-06:00", "CST"],
      "America/Barbados"                 : ["−04:00", "-04:00", "AST"],
      "America/Belem"                    : ["−03:00", "-03:00", "BRT"],
      "America/Belize"                   : ["−06:00", "-06:00", "CST"],
      "America/Blanc-Sablon"             : ["−04:00", "-04:00", "AST"],
      "America/Boa_Vista"                : ["−04:00", "-04:00", "AMT"],
      "America/Bogota"                   : ["−05:00", "-05:00", "COT"],
      "America/Boise"                    : ["−07:00", "-06:00", "MDT"],
      "America/Buenos_Aires"             : ["−03:00", "-03:00", "ART"],
      "America/Cambridge_Bay"            : ["−07:00", "-06:00", "MDT"],
      "America/Campo_Grande"             : ["−04:00", "-04:00", "AMT"],
      "America/Cancun"                   : ["−06:00", "-06:00", "CST"],
      "America/Caracas"                  : ["−04:30", "-04:30", "VET"],
      "America/Catamarca"                : ["−03:00", "-03:00", "ART"],
      "America/Cayenne"                  : ["−03:00", "-03:00", "GFT"],
      "America/Cayman"                   : ["−05:00", "-05:00", "EST"],
      "America/Chicago"                  : ["−06:00", "-05:00", "CDT"],
      "America/Chihuahua"                : ["−07:00", "-07:00", "MST"],
      "America/Coral_Harbour"            : ["−05:00", "-05:00", "EST"],
      "America/Cordoba"                  : ["−03:00", "-03:00", "ART"],
      "America/Costa_Rica"               : ["−06:00", "-06:00", "CST"],
      "America/Creston"                  : ["−07:00", "-07:00", "MST"],
      "America/Cuiaba"                   : ["−04:00", "-04:00", "AMT"],
      "America/Curacao"                  : ["−04:00", "-04:00", "AST"],
      "America/Danmarkshavn"             : ["+00:00", "+00:00", "GMT"],
      "America/Dawson"                   : ["−08:00", "-07:00", "PDT"],
      "America/Dawson_Creek"             : ["−07:00", "-07:00", "MST"],
      "America/Denver"                   : ["−07:00", "-06:00", "MDT"],
      "America/Detroit"                  : ["−05:00", "-04:00", "EDT"],
      "America/Dominica"                 : ["−04:00", "-04:00", "AST"],
      "America/Edmonton"                 : ["−07:00", "-06:00", "MDT"],
      "America/Eirunepe"                 : ["−05:00", "-05:00", "ACT"],
      "America/El_Salvador"              : ["−06:00", "-06:00", "CST"],
      "America/Ensenada"                 : ["−08:00", "-07:00", "PDT"],
      "America/Fort_Wayne"               : ["−05:00", "-04:00", "EDT"],
      "America/Fortaleza"                : ["−03:00", "-03:00", "BRT"],
      "America/Glace_Bay"                : ["−04:00", "-03:00", "ADT"],
      "America/Godthab"                  : ["−03:00", "-03:00", "WGT"],
      "America/Goose_Bay"                : ["−04:00", "-03:00", "ADT"],
      "America/Grand_Turk"               : ["−05:00", "-04:00", "EDT"],
      "America/Grenada"                  : ["−04:00", "-04:00", "AST"],
      "America/Guadeloupe"               : ["−04:00", "-04:00", "AST"],
      "America/Guatemala"                : ["−06:00", "-06:00", "CST"],
      "America/Guayaquil"                : ["−05:00", "-05:00", "ECT"],
      "America/Guyana"                   : ["−04:00", "-04:00", "GYT"],
      "America/Halifax"                  : ["−04:00", "-03:00", "ADT"],
      "America/Havana"                   : ["−05:00", "-04:00", "CDT"],
      "America/Hermosillo"               : ["−07:00", "-07:00", "MST"],
      "America/Indiana/Indianapolis"     : ["−05:00", "-04:00", "EDT"],
      "America/Indiana/Knox"             : ["−06:00", "-05:00", "CDT"],
      "America/Indiana/Marengo"          : ["−05:00", "-04:00", "EDT"],
      "America/Indiana/Petersburg"       : ["−05:00", "-04:00", "EDT"],
      "America/Indiana/Tell_City"        : ["−06:00", "-05:00", "CDT"],
      "America/Indiana/Valparaiso"       : ["−06:00", "+00:00", "UTC"],
      "America/Indiana/Vevay"            : ["−05:00", "-04:00", "EDT"],
      "America/Indiana/Vincennes"        : ["−05:00", "-04:00", "EDT"],
      "America/Indiana/Winamac"          : ["−05:00", "-04:00", "EDT"],
      "America/Indianapolis"             : ["−05:00", "-04:00", "EDT"],
      "America/Inuvik"                   : ["−07:00", "-06:00", "MDT"],
      "America/Iqaluit"                  : ["−05:00", "-04:00", "EDT"],
      "America/Jamaica"                  : ["−05:00", "-05:00", "EST"],
      "America/Jujuy"                    : ["−03:00", "-03:00", "ART"],
      "America/Juneau"                   : ["−09:00", "-08:00", "AKDT"],
      "America/Kentucky/Louisville"      : ["−05:00", "-04:00", "EDT"],
      "America/Kentucky/Monticello"      : ["−05:00", "-04:00", "EDT"],
      "America/Knox_IN"                  : ["−06:00", "-05:00", "CDT"],
      "America/Kralendijk"               : ["−04:00", "-04:00", "AST"],
      "America/La_Paz"                   : ["−04:00", "-04:00", "BOT"],
      "America/Lima"                     : ["−05:00", "-05:00", "PET"],
      "America/Los_Angeles"              : ["−08:00", "-07:00", "PDT"],
      "America/Louisville"               : ["−05:00", "-04:00", "EDT"],
      "America/Lower_Princes"            : ["−04:00", "-04:00", "AST"],
      "America/Maceio"                   : ["−03:00", "-03:00", "BRT"],
      "America/Managua"                  : ["−06:00", "-06:00", "CST"],
      "America/Manaus"                   : ["−04:00", "-04:00", "AMT"],
      "America/Marigot"                  : ["−04:00", "-04:00", "AST"],
      "America/Martinique"               : ["−04:00", "-04:00", "AST"],
      "America/Matamoros"                : ["−06:00", "-05:00", "CDT"],
      "America/Mazatlan"                 : ["−07:00", "-07:00", "MST"],
      "America/Mendoza"                  : ["−03:00", "-03:00", "ART"],
      "America/Menominee"                : ["−06:00", "-05:00", "CDT"],
      "America/Merida"                   : ["−06:00", "-06:00", "CST"],
      "America/Metlakatla"               : ["−08:00", "-08:00", "PST"],
      "America/Mexico_City"              : ["−06:00", "-06:00", "CST"],
      "America/Miquelon"                 : ["−03:00", "-02:00", "PMDT"],
      "America/Moncton"                  : ["−04:00", "-03:00", "ADT"],
      "America/Monterrey"                : ["−06:00", "-06:00", "CST"],
      "America/Montevideo"               : ["−03:00", "-03:00", "UYT"],
      "America/Montreal"                 : ["−05:00", "-04:00", "EDT"],
      "America/Montserrat"               : ["−04:00", "-04:00", "AST"],
      "America/Nassau"                   : ["−05:00", "-04:00", "EDT"],
      "America/New_York"                 : ["−05:00", "-04:00", "EDT"],
      "America/Nipigon"                  : ["−05:00", "-04:00", "EDT"],
      "America/Nome"                     : ["−09:00", "-08:00", "AKDT"],
      "America/Noronha"                  : ["−02:00", "-02:00", "FNT"],
      "America/North_Dakota/Beulah"      : ["−06:00", "-05:00", "CDT"],
      "America/North_Dakota/Center"      : ["−06:00", "-05:00", "CDT"],
      "America/North_Dakota/New_Salem"   : ["−06:00", "-05:00", "CDT"],
      "America/Ojinaga"                  : ["−07:00", "-06:00", "MDT"],
      "America/Panama"                   : ["−05:00", "-05:00", "EST"],
      "America/Pangnirtung"              : ["−05:00", "-04:00", "EDT"],
      "America/Paramaribo"               : ["−03:00", "-03:00", "SRT"],
      "America/Phoenix"                  : ["−07:00", "-07:00", "MST"],
      "America/Port-au-Prince"           : ["−05:00", "-04:00", "EDT"],
      "America/Port_of_Spain"            : ["−04:00", "-04:00", "AST"],
      "America/Porto_Acre"               : ["−05:00", "-05:00", "ACT"],
      "America/Porto_Velho"              : ["−04:00", "-04:00", "AMT"],
      "America/Puerto_Rico"              : ["−04:00", "-04:00", "AST"],
      "America/Rainy_River"              : ["−06:00", "-05:00", "CDT"],
      "America/Rankin_Inlet"             : ["−06:00", "-05:00", "CDT"],
      "America/Recife"                   : ["−03:00", "-03:00", "BRT"],
      "America/Regina"                   : ["−06:00", "-06:00", "CST"],
      "America/Resolute"                 : ["−06:00", "-05:00", "CDT"],
      "America/Rio_Branco"               : ["−05:00", "-05:00", "ACT"],
      "America/Rosario"                  : ["−03:00", "-03:00", "ART"],
      "America/Santa_Isabel"             : ["−08:00", "-08:00", "PST"],
      "America/Santarem"                 : ["−03:00", "-03:00", "BRT"],
      "America/Santiago"                 : ["−04:00", "-03:00", "CLST"],
      "America/Santo_Domingo"            : ["−04:00", "-04:00", "AST"],
      "America/Sao_Paulo"                : ["−03:00", "-03:00", "BRT"],
      "America/Scoresbysund"             : ["−01:00", "-01:00", "EGT"],
      "America/Shiprock"                 : ["−07:00", "-06:00", "MDT"],
      "America/Sitka"                    : ["−09:00", "-08:00", "AKDT"],
      "America/St_Barthelemy"            : ["−04:00", "-04:00", "AST"],
      "America/St_Johns"                 : ["−03:30", "-02:30", "NDT"],
      "America/St_Kitts"                 : ["−04:00", "-04:00", "AST"],
      "America/St_Lucia"                 : ["−04:00", "-04:00", "AST"],
      "America/St_Thomas"                : ["−04:00", "-04:00", "AST"],
      "America/St_Vincent"               : ["−04:00", "-04:00", "AST"],
      "America/Swift_Current"            : ["−06:00", "-06:00", "CST"],
      "America/Tegucigalpa"              : ["−06:00", "-06:00", "CST"],
      "America/Thule"                    : ["−04:00", "-03:00", "ADT"],
      "America/Thunder_Bay"              : ["−05:00", "-04:00", "EDT"],
      "America/Tijuana"                  : ["−08:00", "-07:00", "PDT"],
      "America/Toronto"                  : ["−05:00", "-04:00", "EDT"],
      "America/Tortola"                  : ["−04:00", "-04:00", "AST"],
      "America/Vancouver"                : ["−08:00", "-07:00", "PDT"],
      "America/Virgin"                   : ["−04:00", "-04:00", "AST"],
      "America/Whitehorse"               : ["−08:00", "-07:00", "PDT"],
      "America/Winnipeg"                 : ["−06:00", "-05:00", "CDT"],
      "America/Yakutat"                  : ["−09:00", "-08:00", "AKDT"],
      "America/Yellowknife"              : ["−07:00", "-06:00", "MDT"],
      "Antarctica/Casey"                 : ["+11:00", "+08:00", "AWST"],
      "Antarctica/Davis"                 : ["+05:00", "+07:00", "DAVT"],
      "Antarctica/DumontDUrville"        : ["+10:00", "+10:00", "DDUT"],
      "Antarctica/Macquarie"             : ["+11:00", "+11:00", "MIST"],
      "Antarctica/Mawson"                : ["+05:00", "+05:00", "MAWT"],
      "Antarctica/McMurdo"               : ["+12:00", "+13:00", "NZDT"],
      "Antarctica/Palmer"                : ["−04:00", "-03:00", "CLST"],
      "Antarctica/Rothera"               : ["−03:00", "-03:00", "ROTT"],
      "Antarctica/South_Pole"            : ["+12:00", "+13:00", "NZDT"],
      "Antarctica/Syowa"                 : ["+03:00", "+03:00", "SYOT"],
      "Antarctica/Troll"                 : ["+00:00", "+00:00", "UTC"],
      "Antarctica/Vostok"                : ["+06:00", "+06:00", "VOST"],
      "Arctic/Longyearbyen"              : ["+01:00", "+01:00", "CET"],
      "Asia/Aden"                        : ["+03:00", "+03:00", "AST"],
      "Asia/Almaty"                      : ["+06:00", "+06:00", "ALMT"],
      "Asia/Amman"                       : ["+02:00", "+03:00", "EEST"],
      "Asia/Anadyr"                      : ["+12:00", "+12:00", "ANAT"],
      "Asia/Aqtau"                       : ["+05:00", "+05:00", "AQTT"],
      "Asia/Aqtobe"                      : ["+05:00", "+05:00", "AQTT"],
      "Asia/Ashgabat"                    : ["+05:00", "+05:00", "TMT"],
      "Asia/Ashkhabad"                   : ["+05:00", "+05:00", "TMT"],
      "Asia/Baghdad"                     : ["+03:00", "+03:00", "AST"],
      "Asia/Bahrain"                     : ["+03:00", "+03:00", "AST"],
      "Asia/Baku"                        : ["+04:00", "+04:00", "AZT"],
      "Asia/Bangkok"                     : ["+07:00", "+07:00", "ICT"],
      "Asia/Beirut"                      : ["+02:00", "+02:00", "EET"],
      "Asia/Bishkek"                     : ["+06:00", "+06:00", "KGT"],
      "Asia/Brunei"                      : ["+08:00", "+08:00", "BNT"],
      "Asia/Calcutta"                    : ["+05:30", "+05:30", "IST"],
      "Asia/Choibalsan"                  : ["+08:00", "+08:00", "CHOT"],
      "Asia/Chongqing"                   : ["+08:00", "+08:00", "CST"],
      "Asia/Chungking"                   : ["+08:00", "+08:00", "CST"],
      "Asia/Colombo"                     : ["+05:30", "+05:30", "IST"],
      "Asia/Dacca"                       : ["+06:00", "+06:00", "BDT"],
      "Asia/Damascus"                    : ["+02:00", "+03:00", "EEST"],
      "Asia/Dhaka"                       : ["+06:00", "+06:00", "BDT"],
      "Asia/Dili"                        : ["+09:00", "+09:00", "TLT"],
      "Asia/Dubai"                       : ["+04:00", "+04:00", "GST"],
      "Asia/Dushanbe"                    : ["+05:00", "+05:00", "TJT"],
      "Asia/Gaza"                        : ["+02:00", "+03:00", "EEST"],
      "Asia/Harbin"                      : ["+08:00", "+08:00", "CST"],
      "Asia/Hebron"                      : ["+02:00", "+03:00", "EEST"],
      "Asia/Ho_Chi_Minh"                 : ["+07:00", "+07:00", "ICT"],
      "Asia/Hong_Kong"                   : ["+08:00", "+08:00", "HKT"],
      "Asia/Hovd"                        : ["+07:00", "+07:00", "HOVT"],
      "Asia/Irkutsk"                     : ["+08:00", "+08:00", "IRKT"],
      "Asia/Istanbul"                    : ["+02:00", "+02:00", "EET"],
      "Asia/Jakarta"                     : ["+07:00", "+07:00", "WIB"],
      "Asia/Jayapura"                    : ["+09:00", "+09:00", "WIT"],
      "Asia/Jerusalem"                   : ["+02:00", "+03:00", "IDT"],
      "Asia/Kabul"                       : ["+04:30", "+04:30", "AFT"],
      "Asia/Kamchatka"                   : ["+12:00", "+12:00", "PETT"],
      "Asia/Karachi"                     : ["+05:00", "+05:00", "PKT"],
      "Asia/Kashgar"                     : ["+08:00", "+06:00", "XJT"],
      "Asia/Kathmandu"                   : ["+05:45", "+05:45", "NPT"],
      "Asia/Katmandu"                    : ["+05:45", "+05:45", "NPT"],
      "Asia/Khandyga"                    : ["+09:00", "+09:00", "YAKT"],
      "Asia/Kolkata"                     : ["+05:30", "+05:30", "IST"],
      "Asia/Krasnoyarsk"                 : ["+07:00", "+07:00", "KRAT"],
      "Asia/Kuala_Lumpur"                : ["+08:00", "+08:00", "MYT"],
      "Asia/Kuching"                     : ["+08:00", "+08:00", "MYT"],
      "Asia/Kuwait"                      : ["+03:00", "+03:00", "AST"],
      "Asia/Macao"                       : ["+08:00", "+08:00", "CST"],
      "Asia/Macau"                       : ["+08:00", "+08:00", "CST"],
      "Asia/Magadan"                     : ["+10:00", "+10:00", "MAGT"],
      "Asia/Makassar"                    : ["+08:00", "+08:00", "WITA"],
      "Asia/Manila"                      : ["+08:00", "+08:00", "PHT"],
      "Asia/Muscat"                      : ["+04:00", "+04:00", "GST"],
      "Asia/Nicosia"                     : ["+02:00", "+02:00", "EET"],
      "Asia/Novokuznetsk"                : ["+07:00", "+07:00", "KRAT"],
      "Asia/Novosibirsk"                 : ["+06:00", "+06:00", "NOVT"],
      "Asia/Omsk"                        : ["+06:00", "+06:00", "OMST"],
      "Asia/Oral"                        : ["+05:00", "+05:00", "ORAT"],
      "Asia/Phnom_Penh"                  : ["+07:00", "+07:00", "ICT"],
      "Asia/Pontianak"                   : ["+07:00", "+07:00", "WIB"],
      "Asia/Pyongyang"                   : ["+09:00", "+09:00", "KST"],
      "Asia/Qatar"                       : ["+03:00", "+03:00", "AST"],
      "Asia/Qyzylorda"                   : ["+06:00", "+06:00", "QYZT"],
      "Asia/Rangoon"                     : ["+06:30", "+06:30", "MMT"],
      "Asia/Riyadh"                      : ["+03:00", "+03:00", "AST"],
      "Asia/Saigon"                      : ["+07:00", "+07:00", "ICT"],
      "Asia/Sakhalin"                    : ["+11:00", "+10:00", "SAKT"],
      "Asia/Samarkand"                   : ["+05:00", "+05:00", "UZT"],
      "Asia/Seoul"                       : ["+09:00", "+09:00", "KST"],
      "Asia/Shanghai"                    : ["+08:00", "+08:00", "CST"],
      "Asia/Singapore"                   : ["+08:00", "+08:00", "SGT"],
      "Asia/Taipei"                      : ["+08:00", "+08:00", "CST"],
      "Asia/Tashkent"                    : ["+05:00", "+05:00", "UZT"],
      "Asia/Tbilisi"                     : ["+04:00", "+04:00", "GET"],
      "Asia/Tehran"                      : ["+03:30", "+04:30", "IRDT"],
      "Asia/Tel_Aviv"                    : ["+02:00", "+03:00", "IDT"],
      "Asia/Thimbu"                      : ["+06:00", "+06:00", "BTT"],
      "Asia/Thimphu"                     : ["+06:00", "+06:00", "BTT"],
      "Asia/Tokyo"                       : ["+09:00", "+09:00", "JST"],
      "Asia/Ujung_Pandang"               : ["+08:00", "+08:00", "WITA"],
      "Asia/Ulaanbaatar"                 : ["+08:00", "+08:00", "ULAT"],
      "Asia/Ulan_Bator"                  : ["+08:00", "+08:00", "ULAT"],
      "Asia/Urumqi"                      : ["+08:00", "+06:00", "XJT"],
      "Asia/Ust-Nera"                    : ["+10:00", "+10:00", "VLAT"],
      "Asia/Vientiane"                   : ["+07:00", "+07:00", "ICT"],
      "Asia/Vladivostok"                 : ["+10:00", "+10:00", "VLAT"],
      "Asia/Yakutsk"                     : ["+09:00", "+09:00", "YAKT"],
      "Asia/Yekaterinburg"               : ["+05:00", "+05:00", "YEKT"],
      "Asia/Yerevan"                     : ["+04:00", "+04:00", "AMT"],
      "Atlantic/Azores"                  : ["−01:00", "-01:00", "AZOT"],
      "Atlantic/Bermuda"                 : ["−04:00", "-03:00", "ADT"],
      "Atlantic/Canary"                  : ["+00:00", "+00:00", "WET"],
      "Atlantic/Cape_Verde"              : ["−01:00", "-01:00", "CVT"],
      "Atlantic/Faeroe"                  : ["+00:00", "+00:00", "WET"],
      "Atlantic/Faroe"                   : ["+00:00", "+00:00", "WET"],
      "Atlantic/Jan_Mayen"               : ["+01:00", "+01:00", "CET"],
      "Atlantic/Madeira"                 : ["+00:00", "+00:00", "WET"],
      "Atlantic/Reykjavik"               : ["+00:00", "+00:00", "GMT"],
      "Atlantic/South_Georgia"           : ["−02:00", "-02:00", "GST"],
      "Atlantic/St_Helena"               : ["+00:00", "+00:00", "GMT"],
      "Atlantic/Stanley"                 : ["−03:00", "-03:00", "FKST"],
      "Australia/ACT"                    : ["+10:00", "+11:00", "AEDT"],
      "Australia/Adelaide"               : ["+09:30", "+10:30", "ACDT"],
      "Australia/Brisbane"               : ["+10:00", "+10:00", "AEST"],
      "Australia/Broken_Hill"            : ["+09:30", "+10:30", "ACDT"],
      "Australia/Canberra"               : ["+10:00", "+11:00", "AEDT"],
      "Australia/Currie"                 : ["+10:00", "+11:00", "AEDT"],
      "Australia/Darwin"                 : ["+09:30", "+09:30", "ACST"],
      "Australia/Eucla"                  : ["+08:45", "+08:45", "ACWST"],
      "Australia/Hobart"                 : ["+10:00", "+11:00", "AEDT"],
      "Australia/LHI"                    : ["+10:30", "+11:00", "LHDT"],
      "Australia/Lindeman"               : ["+10:00", "+10:00", "AEST"],
      "Australia/Lord_Howe"              : ["+10:30", "+11:00", "LHDT"],
      "Australia/Melbourne"              : ["+10:00", "+11:00", "AEDT"],
      "Australia/NSW"                    : ["+10:00", "+11:00", "AEDT"],
      "Australia/North"                  : ["+09:30", "+09:30", "ACST"],
      "Australia/Perth"                  : ["+08:00", "+08:00", "AWST"],
      "Australia/Queensland"             : ["+10:00", "+10:00", "AEST"],
      "Australia/South"                  : ["+09:30", "+10:30", "ACDT"],
      "Australia/Sydney"                 : ["+10:00", "+11:00", "AEDT"],
      "Australia/Tasmania"               : ["+10:00", "+11:00", "AEDT"],
      "Australia/Victoria"               : ["+10:00", "+11:00", "AEDT"],
      "Australia/West"                   : ["+08:00", "+08:00", "AWST"],
      "Australia/Yancowinna"             : ["+09:30", "+10:30", "ACDT"],
      "Brazil/Acre"                      : ["−05:00", "-05:00", "ACT"],
      "Brazil/DeNoronha"                 : ["−02:00", "-02:00", "FNT"],
      "Brazil/East"                      : ["−03:00", "-03:00", "BRT"],
      "Brazil/West"                      : ["−04:00", "-04:00", "AMT"],
      "Canada/Atlantic"                  : ["−04:00", "-03:00", "ADT"],
      "Canada/Central"                   : ["−06:00", "-05:00", "CDT"],
      "Canada/East-Saskatchewan"         : ["−06:00", "-06:00", "CST"],
      "Canada/Eastern"                   : ["−05:00", "-04:00", "EDT"],
      "Canada/Mountain"                  : ["−07:00", "-06:00", "MDT"],
      "Canada/Newfoundland"              : ["−03:30", "-02:30", "NDT"],
      "Canada/Pacific"                   : ["−08:00", "-07:00", "PDT"],
      "Canada/Saskatchewan"              : ["−06:00", "-06:00", "CST"],
      "Canada/Yukon"                     : ["−08:00", "-07:00", "PDT"],
      "Chile/Continental"                : ["−04:00", "-03:00", "CLST"],
      "Chile/EasterIsland"               : ["−06:00", "-05:00", "EASST"],
      "Cuba"                             : ["−05:00", "-04:00", "CDT"],
      "Egypt"                            : ["+02:00", "+02:00", "EET"],
      "Eire"                             : ["+00:00", "+00:00", "GMT"],
      "Etc/GMT"                          : ["+00:00", "+00:00", "GMT"],
      "Etc/GMT+0"                        : ["+00:00", "+00:00", "GMT"],
      "Etc/UCT"                          : ["+00:00", "+00:00", "UCT"],
      "Etc/UTC"                          : ["+00:00", "+00:00", "UTC"],
      "Etc/Universal"                    : ["+00:00", "+00:00", "UTC"],
      "Etc/Zulu"                         : ["+00:00", "+00:00", "UTC"],
      "Europe/Amsterdam"                 : ["+01:00", "+01:00", "CET"],
      "Europe/Andorra"                   : ["+01:00", "+01:00", "CET"],
      "Europe/Athens"                    : ["+02:00", "+02:00", "EET"],
      "Europe/Belfast"                   : ["+00:00", "+00:00", "GMT"],
      "Europe/Belgrade"                  : ["+01:00", "+01:00", "CET"],
      "Europe/Berlin"                    : ["+01:00", "+01:00", "CET"],
      "Europe/Bratislava"                : ["+01:00", "+01:00", "CET"],
      "Europe/Brussels"                  : ["+01:00", "+01:00", "CET"],
      "Europe/Bucharest"                 : ["+02:00", "+02:00", "EET"],
      "Europe/Budapest"                  : ["+01:00", "+01:00", "CET"],
      "Europe/Busingen"                  : ["+01:00", "+01:00", "CET"],
      "Europe/Chisinau"                  : ["+02:00", "+02:00", "EET"],
      "Europe/Copenhagen"                : ["+01:00", "+01:00", "CET"],
      "Europe/Dublin"                    : ["+00:00", "+00:00", "GMT"],
      "Europe/Gibraltar"                 : ["+01:00", "+01:00", "CET"],
      "Europe/Guernsey"                  : ["+00:00", "+00:00", "GMT"],
      "Europe/Helsinki"                  : ["+02:00", "+02:00", "EET"],
      "Europe/Isle_of_Man"               : ["+00:00", "+00:00", "GMT"],
      "Europe/Istanbul"                  : ["+02:00", "+02:00", "EET"],
      "Europe/Jersey"                    : ["+00:00", "+00:00", "GMT"],
      "Europe/Kaliningrad"               : ["+02:00", "+02:00", "EET"],
      "Europe/Kiev"                      : ["+02:00", "+02:00", "EET"],
      "Europe/Lisbon"                    : ["+00:00", "+00:00", "WET"],
      "Europe/Ljubljana"                 : ["+01:00", "+01:00", "CET"],
      "Europe/London"                    : ["+00:00", "+00:00", "GMT"],
      "Europe/Luxembourg"                : ["+01:00", "+01:00", "CET"],
      "Europe/Madrid"                    : ["+01:00", "+01:00", "CET"],
      "Europe/Malta"                     : ["+01:00", "+01:00", "CET"],
      "Europe/Mariehamn"                 : ["+02:00", "+02:00", "EET"],
      "Europe/Minsk"                     : ["+03:00", "+03:00", "MSK"],
      "Europe/Monaco"                    : ["+01:00", "+01:00", "CET"],
      "Europe/Moscow"                    : ["+03:00", "+03:00", "MSK"],
      "Europe/Nicosia"                   : ["+02:00", "+02:00", "EET"],
      "Europe/Oslo"                      : ["+01:00", "+01:00", "CET"],
      "Europe/Paris"                     : ["+01:00", "+01:00", "CET"],
      "Europe/Podgorica"                 : ["+01:00", "+01:00", "CET"],
      "Europe/Prague"                    : ["+01:00", "+01:00", "CET"],
      "Europe/Riga"                      : ["+02:00", "+02:00", "EET"],
      "Europe/Rome"                      : ["+01:00", "+01:00", "CET"],
      "Europe/Samara"                    : ["+04:00", "+04:00", "SAMT"],
      "Europe/San_Marino"                : ["+01:00", "+01:00", "CET"],
      "Europe/Sarajevo"                  : ["+01:00", "+01:00", "CET"],
      "Europe/Simferopol"                : ["+03:00", "+03:00", "MSK"],
      "Europe/Skopje"                    : ["+01:00", "+01:00", "CET"],
      "Europe/Sofia"                     : ["+02:00", "+02:00", "EET"],
      "Europe/Stockholm"                 : ["+01:00", "+01:00", "CET"],
      "Europe/Tallinn"                   : ["+02:00", "+02:00", "EET"],
      "Europe/Tirane"                    : ["+01:00", "+01:00", "CET"],
      "Europe/Tiraspol"                  : ["+02:00", "+02:00", "EET"],
      "Europe/Uzhgorod"                  : ["+02:00", "+02:00", "EET"],
      "Europe/Vaduz"                     : ["+01:00", "+01:00", "CET"],
      "Europe/Vatican"                   : ["+01:00", "+01:00", "CET"],
      "Europe/Vienna"                    : ["+01:00", "+01:00", "CET"],
      "Europe/Vilnius"                   : ["+02:00", "+02:00", "EET"],
      "Europe/Volgograd"                 : ["+03:00", "+03:00", "MSK"],
      "Europe/Warsaw"                    : ["+01:00", "+01:00", "CET"],
      "Europe/Zagreb"                    : ["+01:00", "+01:00", "CET"],
      "Europe/Zaporozhye"                : ["+02:00", "+02:00", "EET"],
      "Europe/Zurich"                    : ["+01:00", "+01:00", "CET"],
      "GB"                               : ["+00:00", "+00:00", "GMT"],
      "GB-Eire"                          : ["+00:00", "+00:00", "GMT"],
      "GMT"                              : ["+00:00", "+00:00", "GMT"],
      "GMT+0"                            : ["+00:00", "+00:00", "GMT"],
      "GMT-0"                            : ["+00:00", "+00:00", "GMT"],
      "GMT0"                             : ["+00:00", "+00:00", "GMT"],
      "Greenwich"                        : ["+00:00", "+00:00", "GMT"],
      "Hongkong"                         : ["+08:00", "+08:00", "HKT"],
      "Iceland"                          : ["+00:00", "+00:00", "GMT"],
      "Indian/Antananarivo"              : ["+03:00", "+03:00", "EAT"],
      "Indian/Chagos"                    : ["+06:00", "+06:00", "IOT"],
      "Indian/Christmas"                 : ["+07:00", "+07:00", "CXT"],
      "Indian/Cocos"                     : ["+06:30", "+06:30", "CCT"],
      "Indian/Comoro"                    : ["+03:00", "+03:00", "EAT"],
      "Indian/Kerguelen"                 : ["+05:00", "+05:00", "TFT"],
      "Indian/Mahe"                      : ["+04:00", "+04:00", "SCT"],
      "Indian/Maldives"                  : ["+05:00", "+05:00", "MVT"],
      "Indian/Mauritius"                 : ["+04:00", "+04:00", "MUT"],
      "Indian/Mayotte"                   : ["+03:00", "+03:00", "EAT"],
      "Indian/Reunion"                   : ["+04:00", "+04:00", "RET"],
      "Iran"                             : ["+03:30", "+04:30", "IRDT"],
      "Israel"                           : ["+02:00", "+03:00", "IDT"],
      "Jamaica"                          : ["−05:00", "-05:00", "EST"],
      "Japan"                            : ["+09:00", "+09:00", "JST"],
      "Kwajalein"                        : ["+12:00", "+12:00", "MHT"],
      "Libya"                            : ["+02:00", "+02:00", "EET"],
      "Mexico/BajaNorte"                 : ["−08:00", "-07:00", "PDT"],
      "Mexico/BajaSur"                   : ["−07:00", "-07:00", "MST"],
      "Mexico/General"                   : ["−06:00", "-06:00", "CST"],
      "NZ"                               : ["+12:00", "+13:00", "NZDT"],
      "NZ-CHAT"                          : ["+12:45", "+13:45", "CHADT"],
      "Navajo"                           : ["−07:00", "-06:00", "MDT"],
      "PRC"                              : ["+08:00", "+08:00", "CST"],
      "Pacific/Apia"                     : ["+13:00", "+14:00", "WSDT"],
      "Pacific/Auckland"                 : ["+12:00", "+13:00", "NZDT"],
      "Pacific/Chatham"                  : ["+12:45", "+13:45", "CHADT"],
      "Pacific/Chuuk"                    : ["+10:00", "+10:00", "CHUT"],
      "Pacific/Easter"                   : ["−06:00", "-05:00", "EASST"],
      "Pacific/Efate"                    : ["+11:00", "+11:00", "VUT"],
      "Pacific/Enderbury"                : ["+13:00", "+13:00", "PHOT"],
      "Pacific/Fakaofo"                  : ["+13:00", "+13:00", "TKT"],
      "Pacific/Fiji"                     : ["+12:00", "+12:00", "FJT"],
      "Pacific/Funafuti"                 : ["+12:00", "+12:00", "TVT"],
      "Pacific/Galapagos"                : ["−06:00", "-06:00", "GALT"],
      "Pacific/Gambier"                  : ["−09:00", "-09:00", "GAMT"],
      "Pacific/Guadalcanal"              : ["+11:00", "+11:00", "SBT"],
      "Pacific/Guam"                     : ["+10:00", "+10:00", "ChST"],
      "Pacific/Honolulu"                 : ["−10:00", "-10:00", "HST"],
      "Pacific/Johnston"                 : ["−10:00", "-10:00", "HST"],
      "Pacific/Kiritimati"               : ["+14:00", "+14:00", "LINT"],
      "Pacific/Kosrae"                   : ["+11:00", "+11:00", "KOST"],
      "Pacific/Kwajalein"                : ["+12:00", "+12:00", "MHT"],
      "Pacific/Majuro"                   : ["+12:00", "+12:00", "MHT"],
      "Pacific/Marquesas"                : ["−09:30", "-09:30", "MART"],
      "Pacific/Midway"                   : ["−11:00", "-11:00", "SST"],
      "Pacific/Nauru"                    : ["+12:00", "+12:00", "NRT"],
      "Pacific/Niue"                     : ["−11:00", "-11:00", "NUT"],
      "Pacific/Norfolk"                  : ["+11:30", "+11:30", "NFT"],
      "Pacific/Noumea"                   : ["+11:00", "+11:00", "NCT"],
      "Pacific/Pago_Pago"                : ["−11:00", "-11:00", "SST"],
      "Pacific/Palau"                    : ["+09:00", "+09:00", "PWT"],
      "Pacific/Pitcairn"                 : ["−08:00", "-08:00", "PST"],
      "Pacific/Pohnpei"                  : ["+11:00", "+11:00", "PONT"],
      "Pacific/Ponape"                   : ["+11:00", "+11:00", "PONT"],
      "Pacific/Port_Moresby"             : ["+10:00", "+10:00", "PGT"],
      "Pacific/Rarotonga"                : ["−10:00", "-10:00", "CKT"],
      "Pacific/Saipan"                   : ["+10:00", "+10:00", "ChST"],
      "Pacific/Samoa"                    : ["−11:00", "-11:00", "SST"],
      "Pacific/Tahiti"                   : ["−10:00", "-10:00", "TAHT"],
      "Pacific/Tarawa"                   : ["+12:00", "+12:00", "GILT"],
      "Pacific/Tongatapu"                : ["+13:00", "+13:00", "TOT"],
      "Pacific/Truk"                     : ["+10:00", "+10:00", "CHUT"],
      "Pacific/Wake"                     : ["+12:00", "+12:00", "WAKT"],
      "Pacific/Wallis"                   : ["+12:00", "+12:00", "WFT"],
      "Pacific/Yap"                      : ["+10:00", "+10:00", "CHUT"],
      "Poland"                           : ["+01:00", "+01:00", "CET"],
      "Portugal"                         : ["+00:00", "+00:00", "WET"],
      "ROC"                              : ["+08:00", "+08:00", "CST"],
      "ROK"                              : ["+09:00", "+09:00", "KST"],
      "Singapore"                        : ["+08:00", "+08:00", "SGT"],
      "Turkey"                           : ["+02:00", "+02:00", "EET"],
      "UCT"                              : ["+00:00", "+00:00", "UCT"],
      "US/Alaska"                        : ["−09:00", "-08:00", "AKDT"],
      "US/Aleutian"                      : ["−10:00", "-09:00", "HADT"],
      "US/Arizona"                       : ["−07:00", "-07:00", "MST"],
      "US/Central"                       : ["−06:00", "-05:00", "CDT"],
      "US/East-Indiana"                  : ["−05:00", "-04:00", "EDT"],
      "US/Eastern"                       : ["−05:00", "-04:00", "EDT"],
      "US/Hawaii"                        : ["−10:00", "-10:00", "HST"],
      "US/Indiana-Starke"                : ["−06:00", "-05:00", "CDT"],
      "US/Michigan"                      : ["−05:00", "-04:00", "EDT"],
      "US/Mountain"                      : ["−07:00", "-06:00", "MDT"],
      "US/Pacific"                       : ["−08:00", "-07:00", "PDT"],
      "US/Samoa"                         : ["−11:00", "-11:00", "SST"],
      "UTC"                              : ["+00:00", "+00:00", "UTC"],
      "Universal"                        : ["+00:00", "+00:00", "UTC"],
      "W-SU"                             : ["+03:00", "+03:00", "MSK"],
      "Zulu"                             : ["+00:00", "+00:00", "UTC"],
      "Africa/Abidjan"                   : ["+00:00", "+00:00", "GMT"],
      "Africa/Accra"                     : ["+00:00", "+00:00", "GMT"],
      "Africa/Addis_Ababa"               : ["+03:00", "+03:00", "EAT"],
      "Africa/Algiers"                   : ["+01:00", "+01:00", "CET"],
      "Africa/Asmara"                    : ["+03:00", "+03:00", "EAT"],
      "Africa/Bamako"                    : ["+00:00", "+00:00", "GMT"],
      "Africa/Bangui"                    : ["+01:00", "+01:00", "WAT"],
      "Africa/Banjul"                    : ["+00:00", "+00:00", "GMT"],
      "Africa/Bissau"                    : ["+00:00", "+00:00", "GMT"],
      "Africa/Blantyre"                  : ["+02:00", "+02:00", "CAT"],
      "Africa/Brazzaville"               : ["+01:00", "+01:00", "WAT"],
      "Africa/Bujumbura"                 : ["+02:00", "+02:00", "CAT"],
      "Africa/Cairo"                     : ["+02:00", "+02:00", "EET"],
      "Africa/Casablanca"                : ["+00:00", "+00:00", "WET"],
      "Africa/Ceuta"                     : ["+01:00", "+01:00", "CET"],
      "Africa/Conakry"                   : ["+00:00", "+00:00", "GMT"],
      "Africa/Dakar"                     : ["+00:00", "+00:00", "GMT"],
      "Africa/Dar_es_Salaam"             : ["+03:00", "+03:00", "EAT"],
      "Africa/Djibouti"                  : ["+03:00", "+03:00", "EAT"],
      "Africa/Douala"                    : ["+01:00", "+01:00", "WAT"],
      "Africa/El_Aaiun"                  : ["+00:00", "+00:00", "WET"],
      "Africa/Freetown"                  : ["+00:00", "+00:00", "GMT"],
      "Africa/Gaborone"                  : ["+02:00", "+02:00", "CAT"],
      "Africa/Harare"                    : ["+02:00", "+02:00", "CAT"],
      "Africa/Johannesburg"              : ["+02:00", "+02:00", "SAST"],
      "Africa/Juba"                      : ["+03:00", "+03:00", "EAT"],
      "Africa/Kampala"                   : ["+03:00", "+03:00", "EAT"],
      "Africa/Khartoum"                  : ["+03:00", "+03:00", "EAT"],
      "Africa/Kigali"                    : ["+02:00", "+02:00", "CAT"],
      "Africa/Kinshasa"                  : ["+01:00", "+01:00", "WAT"],
      "Africa/Lagos"                     : ["+01:00", "+01:00", "WAT"],
      "Africa/Libreville"                : ["+01:00", "+01:00", "WAT"],
      "Africa/Lome"                      : ["+00:00", "+00:00", "GMT"],
      "Africa/Luanda"                    : ["+01:00", "+01:00", "WAT"],
      "Africa/Lubumbashi"                : ["+02:00", "+02:00", "CAT"],
      "Africa/Lusaka"                    : ["+02:00", "+02:00", "CAT"],
      "Africa/Malabo"                    : ["+01:00", "+01:00", "WAT"],
      "Africa/Maputo"                    : ["+02:00", "+02:00", "CAT"],
      "Africa/Maseru"                    : ["+02:00", "+02:00", "SAST"],
      "Africa/Mbabane"                   : ["+02:00", "+02:00", "SAST"],
      "Africa/Mogadishu"                 : ["+03:00", "+03:00", "EAT"],
      "Africa/Monrovia"                  : ["+00:00", "+00:00", "GMT"],
      "Africa/Nairobi"                   : ["+03:00", "+03:00", "EAT"],
      "Africa/Ndjamena"                  : ["+01:00", "+01:00", "WAT"],
      "Africa/Niamey"                    : ["+01:00", "+01:00", "WAT"],
      "Africa/Nouakchott"                : ["+00:00", "+00:00", "GMT"],
      "Africa/Ouagadougou"               : ["+00:00", "+00:00", "GMT"],
      "Africa/Porto-Novo"                : ["+01:00", "+01:00", "WAT"],
      "Africa/Sao_Tome"                  : ["+00:00", "+00:00", "GMT"],
      "Africa/Timbuktu"                  : ["+00:00", "+00:00", "GMT"],
      "Africa/Tripoli"                   : ["+01:00", "+02:00", "EET"],
      "Africa/Tunis"                     : ["+01:00", "+01:00", "CET"],
      "Africa/Windhoek"                  : ["+01:00", "+02:00", "WAST"],
      "America/Adak"                     : ["−10:00", "-09:00", "HADT"],
      "America/Anchorage"                : ["−09:00", "-08:00", "AKDT"],
      "America/Anguilla"                 : ["−04:00", "-04:00", "AST"],
      "America/Antigua"                  : ["−04:00", "-04:00", "AST"],
      "America/Araguaina"                : ["−03:00", "-03:00", "BRT"],
      "America/Argentina/Buenos_Aires"   : ["−03:00", "-03:00", "ART"],
      "America/Argentina/Catamarca"      : ["−03:00", "-03:00", "ART"],
      "America/Argentina/ComodRivadavia" : ["−03:00", "-03:00", "ART"],
      "America/Argentina/Cordoba"        : ["−03:00", "-03:00", "ART"],
      "America/Argentina/Jujuy"          : ["−03:00", "-03:00", "ART"],
      "America/Argentina/La_Rioja"       : ["−03:00", "-03:00", "ART"],
      "America/Argentina/Mendoza"        : ["−03:00", "-03:00", "ART"],
      "America/Argentina/Rio_Gallegos"   : ["−03:00", "-03:00", "ART"],
      "America/Argentina/Salta"          : ["−03:00", "-03:00", "ART"],
      "America/Argentina/San_Juan"       : ["−03:00", "-03:00", "ART"],
      "America/Argentina/San_Luis"       : ["−03:00", "-03:00", "ART"],
      "America/Argentina/Tucuman"        : ["−03:00", "-03:00", "ART"],
      "America/Argentina/Ushuaia"        : ["−03:00", "-03:00", "ART"],
      "America/Aruba"                    : ["−04:00", "-04:00", "AST"],
      "America/Asuncion"                 : ["−04:00", "-04:00", "PYT"],
      "America/Atikokan"                 : ["−05:00", "-05:00", "EST"],
      "America/Atka"                     : ["−10:00", "-09:00", "HADT"],
      "America/Bahia"                    : ["−03:00", "-03:00", "BRT"],
      "America/Bahia_Banderas"           : ["−06:00", "-06:00", "CST"],
      "America/Barbados"                 : ["−04:00", "-04:00", "AST"],
      "America/Belem"                    : ["−03:00", "-03:00", "BRT"],
      "America/Belize"                   : ["−06:00", "-06:00", "CST"],
      "America/Blanc-Sablon"             : ["−04:00", "-04:00", "AST"],
      "America/Boa_Vista"                : ["−04:00", "-04:00", "AMT"],
      "America/Bogota"                   : ["−05:00", "-05:00", "COT"],
      "America/Boise"                    : ["−07:00", "-06:00", "MDT"],
      "America/Buenos_Aires"             : ["−03:00", "-03:00", "ART"],
      "America/Cambridge_Bay"            : ["−07:00", "-06:00", "MDT"],
      "America/Campo_Grande"             : ["−04:00", "-04:00", "AMT"],
      "America/Cancun"                   : ["−06:00", "-06:00", "CST"],
      "America/Caracas"                  : ["−04:30", "-04:30", "VET"],
      "America/Catamarca"                : ["−03:00", "-03:00", "ART"],
      "America/Cayenne"                  : ["−03:00", "-03:00", "GFT"],
      "America/Cayman"                   : ["−05:00", "-05:00", "EST"],
      "America/Chicago"                  : ["−06:00", "-05:00", "CDT"],
      "America/Chihuahua"                : ["−07:00", "-07:00", "MST"],
      "America/Coral_Harbour"            : ["−05:00", "-05:00", "EST"],
      "America/Cordoba"                  : ["−03:00", "-03:00", "ART"],
      "America/Costa_Rica"               : ["−06:00", "-06:00", "CST"],
      "America/Creston"                  : ["−07:00", "-07:00", "MST"],
      "America/Cuiaba"                   : ["−04:00", "-04:00", "AMT"],
      "America/Curacao"                  : ["−04:00", "-04:00", "AST"],
      "America/Danmarkshavn"             : ["+00:00", "+00:00", "GMT"],
      "America/Dawson"                   : ["−08:00", "-07:00", "PDT"],
      "America/Dawson_Creek"             : ["−07:00", "-07:00", "MST"],
      "America/Denver"                   : ["−07:00", "-06:00", "MDT"],
      "America/Detroit"                  : ["−05:00", "-04:00", "EDT"],
      "America/Dominica"                 : ["−04:00", "-04:00", "AST"],
      "America/Edmonton"                 : ["−07:00", "-06:00", "MDT"],
      "America/Eirunepe"                 : ["−05:00", "-05:00", "ACT"],
      "America/El_Salvador"              : ["−06:00", "-06:00", "CST"],
      "America/Ensenada"                 : ["−08:00", "-07:00", "PDT"],
      "America/Fort_Wayne"               : ["−05:00", "-04:00", "EDT"],
      "America/Fortaleza"                : ["−03:00", "-03:00", "BRT"],
      "America/Glace_Bay"                : ["−04:00", "-03:00", "ADT"],
      "America/Godthab"                  : ["−03:00", "-03:00", "WGT"],
      "America/Goose_Bay"                : ["−04:00", "-03:00", "ADT"],
      "America/Grand_Turk"               : ["−05:00", "-04:00", "EDT"],
      "America/Grenada"                  : ["−04:00", "-04:00", "AST"],
      "America/Guadeloupe"               : ["−04:00", "-04:00", "AST"],
      "America/Guatemala"                : ["−06:00", "-06:00", "CST"],
      "America/Guayaquil"                : ["−05:00", "-05:00", "ECT"],
      "America/Guyana"                   : ["−04:00", "-04:00", "GYT"],
      "America/Halifax"                  : ["−04:00", "-03:00", "ADT"],
      "America/Havana"                   : ["−05:00", "-04:00", "CDT"],
      "America/Hermosillo"               : ["−07:00", "-07:00", "MST"],
      "America/Indiana/Indianapolis"     : ["−05:00", "-04:00", "EDT"],
      "America/Indiana/Knox"             : ["−06:00", "-05:00", "CDT"],
      "America/Indiana/Marengo"          : ["−05:00", "-04:00", "EDT"],
      "America/Indiana/Petersburg"       : ["−05:00", "-04:00", "EDT"],
      "America/Indiana/Tell_City"        : ["−06:00", "-05:00", "CDT"],
      "America/Indiana/Valparaiso"       : ["−06:00", "+00:00", "UTC"],
      "America/Indiana/Vevay"            : ["−05:00", "-04:00", "EDT"],
      "America/Indiana/Vincennes"        : ["−05:00", "-04:00", "EDT"],
      "America/Indiana/Winamac"          : ["−05:00", "-04:00", "EDT"],
      "America/Indianapolis"             : ["−05:00", "-04:00", "EDT"],
      "America/Inuvik"                   : ["−07:00", "-06:00", "MDT"],
      "America/Iqaluit"                  : ["−05:00", "-04:00", "EDT"],
      "America/Jamaica"                  : ["−05:00", "-05:00", "EST"],
      "America/Jujuy"                    : ["−03:00", "-03:00", "ART"],
      "America/Juneau"                   : ["−09:00", "-08:00", "AKDT"],
      "America/Kentucky/Louisville"      : ["−05:00", "-04:00", "EDT"],
      "America/Kentucky/Monticello"      : ["−05:00", "-04:00", "EDT"],
      "America/Knox_IN"                  : ["−06:00", "-05:00", "CDT"],
      "America/Kralendijk"               : ["−04:00", "-04:00", "AST"],
      "America/La_Paz"                   : ["−04:00", "-04:00", "BOT"],
      "America/Lima"                     : ["−05:00", "-05:00", "PET"],
      "America/Los_Angeles"              : ["−08:00", "-07:00", "PDT"],
      "America/Louisville"               : ["−05:00", "-04:00", "EDT"],
      "America/Lower_Princes"            : ["−04:00", "-04:00", "AST"],
      "America/Maceio"                   : ["−03:00", "-03:00", "BRT"],
      "America/Managua"                  : ["−06:00", "-06:00", "CST"],
      "America/Manaus"                   : ["−04:00", "-04:00", "AMT"],
      "America/Marigot"                  : ["−04:00", "-04:00", "AST"],
      "America/Martinique"               : ["−04:00", "-04:00", "AST"],
      "America/Matamoros"                : ["−06:00", "-05:00", "CDT"],
      "America/Mazatlan"                 : ["−07:00", "-07:00", "MST"],
      "America/Mendoza"                  : ["−03:00", "-03:00", "ART"],
      "America/Menominee"                : ["−06:00", "-05:00", "CDT"],
      "America/Merida"                   : ["−06:00", "-06:00", "CST"],
      "America/Metlakatla"               : ["−08:00", "-08:00", "PST"],
      "America/Mexico_City"              : ["−06:00", "-06:00", "CST"],
      "America/Miquelon"                 : ["−03:00", "-02:00", "PMDT"],
      "America/Moncton"                  : ["−04:00", "-03:00", "ADT"],
      "America/Monterrey"                : ["−06:00", "-06:00", "CST"],
      "America/Montevideo"               : ["−03:00", "-03:00", "UYT"],
      "America/Montreal"                 : ["−05:00", "-04:00", "EDT"],
      "America/Montserrat"               : ["−04:00", "-04:00", "AST"],
      "America/Nassau"                   : ["−05:00", "-04:00", "EDT"],
      "America/New_York"                 : ["−05:00", "-04:00", "EDT"],
      "America/Nipigon"                  : ["−05:00", "-04:00", "EDT"],
      "America/Nome"                     : ["−09:00", "-08:00", "AKDT"],
      "America/Noronha"                  : ["−02:00", "-02:00", "FNT"],
      "America/North_Dakota/Beulah"      : ["−06:00", "-05:00", "CDT"],
      "America/North_Dakota/Center"      : ["−06:00", "-05:00", "CDT"],
      "America/North_Dakota/New_Salem"   : ["−06:00", "-05:00", "CDT"],
      "America/Ojinaga"                  : ["−07:00", "-06:00", "MDT"],
      "America/Panama"                   : ["−05:00", "-05:00", "EST"],
      "America/Pangnirtung"              : ["−05:00", "-04:00", "EDT"],
      "America/Paramaribo"               : ["−03:00", "-03:00", "SRT"],
      "America/Phoenix"                  : ["−07:00", "-07:00", "MST"],
      "America/Port-au-Prince"           : ["−05:00", "-04:00", "EDT"],
      "America/Port_of_Spain"            : ["−04:00", "-04:00", "AST"],
      "America/Porto_Acre"               : ["−05:00", "-05:00", "ACT"],
      "America/Porto_Velho"              : ["−04:00", "-04:00", "AMT"],
      "America/Puerto_Rico"              : ["−04:00", "-04:00", "AST"],
      "America/Rainy_River"              : ["−06:00", "-05:00", "CDT"],
      "America/Rankin_Inlet"             : ["−06:00", "-05:00", "CDT"],
      "America/Recife"                   : ["−03:00", "-03:00", "BRT"],
      "America/Regina"                   : ["−06:00", "-06:00", "CST"],
      "America/Resolute"                 : ["−06:00", "-05:00", "CDT"],
      "America/Rio_Branco"               : ["−05:00", "-05:00", "ACT"],
      "America/Rosario"                  : ["−03:00", "-03:00", "ART"],
      "America/Santa_Isabel"             : ["−08:00", "-08:00", "PST"],
      "America/Santarem"                 : ["−03:00", "-03:00", "BRT"],
      "America/Santiago"                 : ["−04:00", "-03:00", "CLST"],
      "America/Santo_Domingo"            : ["−04:00", "-04:00", "AST"],
      "America/Sao_Paulo"                : ["−03:00", "-03:00", "BRT"],
      "America/Scoresbysund"             : ["−01:00", "-01:00", "EGT"],
      "America/Shiprock"                 : ["−07:00", "-06:00", "MDT"],
      "America/Sitka"                    : ["−09:00", "-08:00", "AKDT"],
      "America/St_Barthelemy"            : ["−04:00", "-04:00", "AST"],
      "America/St_Johns"                 : ["−03:30", "-02:30", "NDT"],
      "America/St_Kitts"                 : ["−04:00", "-04:00", "AST"],
      "America/St_Lucia"                 : ["−04:00", "-04:00", "AST"],
      "America/St_Thomas"                : ["−04:00", "-04:00", "AST"],
      "America/St_Vincent"               : ["−04:00", "-04:00", "AST"],
      "America/Swift_Current"            : ["−06:00", "-06:00", "CST"],
      "America/Tegucigalpa"              : ["−06:00", "-06:00", "CST"],
      "America/Thule"                    : ["−04:00", "-03:00", "ADT"],
      "America/Thunder_Bay"              : ["−05:00", "-04:00", "EDT"],
      "America/Tijuana"                  : ["−08:00", "-07:00", "PDT"],
      "America/Toronto"                  : ["−05:00", "-04:00", "EDT"],
      "America/Tortola"                  : ["−04:00", "-04:00", "AST"],
      "America/Vancouver"                : ["−08:00", "-07:00", "PDT"],
      "America/Virgin"                   : ["−04:00", "-04:00", "AST"],
      "America/Whitehorse"               : ["−08:00", "-07:00", "PDT"],
      "America/Winnipeg"                 : ["−06:00", "-05:00", "CDT"],
      "America/Yakutat"                  : ["−09:00", "-08:00", "AKDT"],
      "America/Yellowknife"              : ["−07:00", "-06:00", "MDT"],
      "Antarctica/Casey"                 : ["+11:00", "+08:00", "AWST"],
      "Antarctica/Davis"                 : ["+05:00", "+07:00", "DAVT"],
      "Antarctica/DumontDUrville"        : ["+10:00", "+10:00", "DDUT"],
      "Antarctica/Macquarie"             : ["+11:00", "+11:00", "MIST"],
      "Antarctica/Mawson"                : ["+05:00", "+05:00", "MAWT"],
      "Antarctica/McMurdo"               : ["+12:00", "+13:00", "NZDT"],
      "Antarctica/Palmer"                : ["−04:00", "-03:00", "CLST"],
      "Antarctica/Rothera"               : ["−03:00", "-03:00", "ROTT"],
      "Antarctica/South_Pole"            : ["+12:00", "+13:00", "NZDT"],
      "Antarctica/Syowa"                 : ["+03:00", "+03:00", "SYOT"],
      "Antarctica/Troll"                 : ["+00:00", "+00:00", "UTC"],
      "Antarctica/Vostok"                : ["+06:00", "+06:00", "VOST"],
      "Arctic/Longyearbyen"              : ["+01:00", "+01:00", "CET"],
      "Asia/Aden"                        : ["+03:00", "+03:00", "AST"],
      "Asia/Almaty"                      : ["+06:00", "+06:00", "ALMT"],
      "Asia/Amman"                       : ["+02:00", "+03:00", "EEST"],
      "Asia/Anadyr"                      : ["+12:00", "+12:00", "ANAT"],
      "Asia/Aqtau"                       : ["+05:00", "+05:00", "AQTT"],
      "Asia/Aqtobe"                      : ["+05:00", "+05:00", "AQTT"],
      "Asia/Ashgabat"                    : ["+05:00", "+05:00", "TMT"],
      "Asia/Ashkhabad"                   : ["+05:00", "+05:00", "TMT"],
      "Asia/Baghdad"                     : ["+03:00", "+03:00", "AST"],
      "Asia/Bahrain"                     : ["+03:00", "+03:00", "AST"],
      "Asia/Baku"                        : ["+04:00", "+04:00", "AZT"],
      "Asia/Bangkok"                     : ["+07:00", "+07:00", "ICT"],
      "Asia/Beirut"                      : ["+02:00", "+02:00", "EET"],
      "Asia/Bishkek"                     : ["+06:00", "+06:00", "KGT"],
      "Asia/Brunei"                      : ["+08:00", "+08:00", "BNT"],
      "Asia/Calcutta"                    : ["+05:30", "+05:30", "IST"],
      "Asia/Choibalsan"                  : ["+08:00", "+08:00", "CHOT"],
      "Asia/Chongqing"                   : ["+08:00", "+08:00", "CST"],
      "Asia/Chungking"                   : ["+08:00", "+08:00", "CST"],
      "Asia/Colombo"                     : ["+05:30", "+05:30", "IST"],
      "Asia/Dacca"                       : ["+06:00", "+06:00", "BDT"],
      "Asia/Damascus"                    : ["+02:00", "+03:00", "EEST"],
      "Asia/Dhaka"                       : ["+06:00", "+06:00", "BDT"],
      "Asia/Dili"                        : ["+09:00", "+09:00", "TLT"],
      "Asia/Dubai"                       : ["+04:00", "+04:00", "GST"],
      "Asia/Dushanbe"                    : ["+05:00", "+05:00", "TJT"],
      "Asia/Gaza"                        : ["+02:00", "+03:00", "EEST"],
      "Asia/Harbin"                      : ["+08:00", "+08:00", "CST"],
      "Asia/Hebron"                      : ["+02:00", "+03:00", "EEST"],
      "Asia/Ho_Chi_Minh"                 : ["+07:00", "+07:00", "ICT"],
      "Asia/Hong_Kong"                   : ["+08:00", "+08:00", "HKT"],
      "Asia/Hovd"                        : ["+07:00", "+07:00", "HOVT"],
      "Asia/Irkutsk"                     : ["+08:00", "+08:00", "IRKT"],
      "Asia/Istanbul"                    : ["+02:00", "+02:00", "EET"],
      "Asia/Jakarta"                     : ["+07:00", "+07:00", "WIB"],
      "Asia/Jayapura"                    : ["+09:00", "+09:00", "WIT"],
      "Asia/Jerusalem"                   : ["+02:00", "+03:00", "IDT"],
      "Asia/Kabul"                       : ["+04:30", "+04:30", "AFT"],
      "Asia/Kamchatka"                   : ["+12:00", "+12:00", "PETT"],
      "Asia/Karachi"                     : ["+05:00", "+05:00", "PKT"],
      "Asia/Kashgar"                     : ["+08:00", "+06:00", "XJT"],
      "Asia/Kathmandu"                   : ["+05:45", "+05:45", "NPT"],
      "Asia/Katmandu"                    : ["+05:45", "+05:45", "NPT"],
      "Asia/Khandyga"                    : ["+09:00", "+09:00", "YAKT"],
      "Asia/Kolkata"                     : ["+05:30", "+05:30", "IST"],
      "Asia/Krasnoyarsk"                 : ["+07:00", "+07:00", "KRAT"],
      "Asia/Kuala_Lumpur"                : ["+08:00", "+08:00", "MYT"],
      "Asia/Kuching"                     : ["+08:00", "+08:00", "MYT"],
      "Asia/Kuwait"                      : ["+03:00", "+03:00", "AST"],
      "Asia/Macao"                       : ["+08:00", "+08:00", "CST"],
      "Asia/Macau"                       : ["+08:00", "+08:00", "CST"],
      "Asia/Magadan"                     : ["+10:00", "+10:00", "MAGT"],
      "Asia/Makassar"                    : ["+08:00", "+08:00", "WITA"],
      "Asia/Manila"                      : ["+08:00", "+08:00", "PHT"],
      "Asia/Muscat"                      : ["+04:00", "+04:00", "GST"],
      "Asia/Nicosia"                     : ["+02:00", "+02:00", "EET"],
      "Asia/Novokuznetsk"                : ["+07:00", "+07:00", "KRAT"],
      "Asia/Novosibirsk"                 : ["+06:00", "+06:00", "NOVT"],
      "Asia/Omsk"                        : ["+06:00", "+06:00", "OMST"],
      "Asia/Oral"                        : ["+05:00", "+05:00", "ORAT"],
      "Asia/Phnom_Penh"                  : ["+07:00", "+07:00", "ICT"],
      "Asia/Pontianak"                   : ["+07:00", "+07:00", "WIB"],
      "Asia/Pyongyang"                   : ["+09:00", "+09:00", "KST"],
      "Asia/Qatar"                       : ["+03:00", "+03:00", "AST"],
      "Asia/Qyzylorda"                   : ["+06:00", "+06:00", "QYZT"],
      "Asia/Rangoon"                     : ["+06:30", "+06:30", "MMT"],
      "Asia/Riyadh"                      : ["+03:00", "+03:00", "AST"],
      "Asia/Saigon"                      : ["+07:00", "+07:00", "ICT"],
      "Asia/Sakhalin"                    : ["+11:00", "+10:00", "SAKT"],
      "Asia/Samarkand"                   : ["+05:00", "+05:00", "UZT"],
      "Asia/Seoul"                       : ["+09:00", "+09:00", "KST"],
      "Asia/Shanghai"                    : ["+08:00", "+08:00", "CST"],
      "Asia/Singapore"                   : ["+08:00", "+08:00", "SGT"],
      "Asia/Taipei"                      : ["+08:00", "+08:00", "CST"],
      "Asia/Tashkent"                    : ["+05:00", "+05:00", "UZT"],
      "Asia/Tbilisi"                     : ["+04:00", "+04:00", "GET"],
      "Asia/Tehran"                      : ["+03:30", "+04:30", "IRDT"],
      "Asia/Tel_Aviv"                    : ["+02:00", "+03:00", "IDT"],
      "Asia/Thimbu"                      : ["+06:00", "+06:00", "BTT"],
      "Asia/Thimphu"                     : ["+06:00", "+06:00", "BTT"],
      "Asia/Tokyo"                       : ["+09:00", "+09:00", "JST"],
      "Asia/Ujung_Pandang"               : ["+08:00", "+08:00", "WITA"],
      "Asia/Ulaanbaatar"                 : ["+08:00", "+08:00", "ULAT"],
      "Asia/Ulan_Bator"                  : ["+08:00", "+08:00", "ULAT"],
      "Asia/Urumqi"                      : ["+08:00", "+06:00", "XJT"],
      "Asia/Ust-Nera"                    : ["+10:00", "+10:00", "VLAT"],
      "Asia/Vientiane"                   : ["+07:00", "+07:00", "ICT"],
      "Asia/Vladivostok"                 : ["+10:00", "+10:00", "VLAT"],
      "Asia/Yakutsk"                     : ["+09:00", "+09:00", "YAKT"],
      "Asia/Yekaterinburg"               : ["+05:00", "+05:00", "YEKT"],
      "Asia/Yerevan"                     : ["+04:00", "+04:00", "AMT"],
      "Atlantic/Azores"                  : ["−01:00", "-01:00", "AZOT"],
      "Atlantic/Bermuda"                 : ["−04:00", "-03:00", "ADT"],
      "Atlantic/Canary"                  : ["+00:00", "+00:00", "WET"],
      "Atlantic/Cape_Verde"              : ["−01:00", "-01:00", "CVT"],
      "Atlantic/Faeroe"                  : ["+00:00", "+00:00", "WET"],
      "Atlantic/Faroe"                   : ["+00:00", "+00:00", "WET"],
      "Atlantic/Jan_Mayen"               : ["+01:00", "+01:00", "CET"],
      "Atlantic/Madeira"                 : ["+00:00", "+00:00", "WET"],
      "Atlantic/Reykjavik"               : ["+00:00", "+00:00", "GMT"],
      "Atlantic/South_Georgia"           : ["−02:00", "-02:00", "GST"],
      "Atlantic/St_Helena"               : ["+00:00", "+00:00", "GMT"],
      "Atlantic/Stanley"                 : ["−03:00", "-03:00", "FKST"],
      "Australia/ACT"                    : ["+10:00", "+11:00", "AEDT"],
      "Australia/Adelaide"               : ["+09:30", "+10:30", "ACDT"],
      "Australia/Brisbane"               : ["+10:00", "+10:00", "AEST"],
      "Australia/Broken_Hill"            : ["+09:30", "+10:30", "ACDT"],
      "Australia/Canberra"               : ["+10:00", "+11:00", "AEDT"],
      "Australia/Currie"                 : ["+10:00", "+11:00", "AEDT"],
      "Australia/Darwin"                 : ["+09:30", "+09:30", "ACST"],
      "Australia/Eucla"                  : ["+08:45", "+08:45", "ACWST"],
      "Australia/Hobart"                 : ["+10:00", "+11:00", "AEDT"],
      "Australia/LHI"                    : ["+10:30", "+11:00", "LHDT"],
      "Australia/Lindeman"               : ["+10:00", "+10:00", "AEST"],
      "Australia/Lord_Howe"              : ["+10:30", "+11:00", "LHDT"],
      "Australia/Melbourne"              : ["+10:00", "+11:00", "AEDT"],
      "Australia/NSW"                    : ["+10:00", "+11:00", "AEDT"],
      "Australia/North"                  : ["+09:30", "+09:30", "ACST"],
      "Australia/Perth"                  : ["+08:00", "+08:00", "AWST"],
      "Australia/Queensland"             : ["+10:00", "+10:00", "AEST"],
      "Australia/South"                  : ["+09:30", "+10:30", "ACDT"],
      "Australia/Sydney"                 : ["+10:00", "+11:00", "AEDT"],
      "Australia/Tasmania"               : ["+10:00", "+11:00", "AEDT"],
      "Australia/Victoria"               : ["+10:00", "+11:00", "AEDT"],
      "Australia/West"                   : ["+08:00", "+08:00", "AWST"],
      "Australia/Yancowinna"             : ["+09:30", "+10:30", "ACDT"],
      "Brazil/Acre"                      : ["−05:00", "-05:00", "ACT"],
      "Brazil/DeNoronha"                 : ["−02:00", "-02:00", "FNT"],
      "Brazil/East"                      : ["−03:00", "-03:00", "BRT"],
      "Brazil/West"                      : ["−04:00", "-04:00", "AMT"],
      "Canada/Atlantic"                  : ["−04:00", "-03:00", "ADT"],
      "Canada/Central"                   : ["−06:00", "-05:00", "CDT"],
      "Canada/East-Saskatchewan"         : ["−06:00", "-06:00", "CST"],
      "Canada/Eastern"                   : ["−05:00", "-04:00", "EDT"],
      "Canada/Mountain"                  : ["−07:00", "-06:00", "MDT"],
      "Canada/Newfoundland"              : ["−03:30", "-02:30", "NDT"],
      "Canada/Pacific"                   : ["−08:00", "-07:00", "PDT"],
      "Canada/Saskatchewan"              : ["−06:00", "-06:00", "CST"],
      "Canada/Yukon"                     : ["−08:00", "-07:00", "PDT"],
      "Chile/Continental"                : ["−04:00", "-03:00", "CLST"],
      "Chile/EasterIsland"               : ["−06:00", "-05:00", "EASST"],
      "Cuba"                             : ["−05:00", "-04:00", "CDT"],
      "Egypt"                            : ["+02:00", "+02:00", "EET"],
      "Eire"                             : ["+00:00", "+00:00", "GMT"],
      "Etc/GMT"                          : ["+00:00", "+00:00", "GMT"],
      "Etc/GMT+0"                        : ["+00:00", "+00:00", "GMT"],
      "Etc/UCT"                          : ["+00:00", "+00:00", "UCT"],
      "Etc/UTC"                          : ["+00:00", "+00:00", "UTC"],
      "Etc/Universal"                    : ["+00:00", "+00:00", "UTC"],
      "Etc/Zulu"                         : ["+00:00", "+00:00", "UTC"],
      "Europe/Amsterdam"                 : ["+01:00", "+01:00", "CET"],
      "Europe/Andorra"                   : ["+01:00", "+01:00", "CET"],
      "Europe/Athens"                    : ["+02:00", "+02:00", "EET"],
      "Europe/Belfast"                   : ["+00:00", "+00:00", "GMT"],
      "Europe/Belgrade"                  : ["+01:00", "+01:00", "CET"],
      "Europe/Berlin"                    : ["+01:00", "+01:00", "CET"],
      "Europe/Bratislava"                : ["+01:00", "+01:00", "CET"],
      "Europe/Brussels"                  : ["+01:00", "+01:00", "CET"],
      "Europe/Bucharest"                 : ["+02:00", "+02:00", "EET"],
      "Europe/Budapest"                  : ["+01:00", "+01:00", "CET"],
      "Europe/Busingen"                  : ["+01:00", "+01:00", "CET"],
      "Europe/Chisinau"                  : ["+02:00", "+02:00", "EET"],
      "Europe/Copenhagen"                : ["+01:00", "+01:00", "CET"],
      "Europe/Dublin"                    : ["+00:00", "+00:00", "GMT"],
      "Europe/Gibraltar"                 : ["+01:00", "+01:00", "CET"],
      "Europe/Guernsey"                  : ["+00:00", "+00:00", "GMT"],
      "Europe/Helsinki"                  : ["+02:00", "+02:00", "EET"],
      "Europe/Isle_of_Man"               : ["+00:00", "+00:00", "GMT"],
      "Europe/Istanbul"                  : ["+02:00", "+02:00", "EET"],
      "Europe/Jersey"                    : ["+00:00", "+00:00", "GMT"],
      "Europe/Kaliningrad"               : ["+02:00", "+02:00", "EET"],
      "Europe/Kiev"                      : ["+02:00", "+02:00", "EET"],
      "Europe/Lisbon"                    : ["+00:00", "+00:00", "WET"],
      "Europe/Ljubljana"                 : ["+01:00", "+01:00", "CET"],
      "Europe/London"                    : ["+00:00", "+00:00", "GMT"],
      "Europe/Luxembourg"                : ["+01:00", "+01:00", "CET"],
      "Europe/Madrid"                    : ["+01:00", "+01:00", "CET"],
      "Europe/Malta"                     : ["+01:00", "+01:00", "CET"],
      "Europe/Mariehamn"                 : ["+02:00", "+02:00", "EET"],
      "Europe/Minsk"                     : ["+03:00", "+03:00", "MSK"],
      "Europe/Monaco"                    : ["+01:00", "+01:00", "CET"],
      "Europe/Moscow"                    : ["+03:00", "+03:00", "MSK"],
      "Europe/Nicosia"                   : ["+02:00", "+02:00", "EET"],
      "Europe/Oslo"                      : ["+01:00", "+01:00", "CET"],
      "Europe/Paris"                     : ["+01:00", "+01:00", "CET"],
      "Europe/Podgorica"                 : ["+01:00", "+01:00", "CET"],
      "Europe/Prague"                    : ["+01:00", "+01:00", "CET"],
      "Europe/Riga"                      : ["+02:00", "+02:00", "EET"],
      "Europe/Rome"                      : ["+01:00", "+01:00", "CET"],
      "Europe/Samara"                    : ["+04:00", "+04:00", "SAMT"],
      "Europe/San_Marino"                : ["+01:00", "+01:00", "CET"],
      "Europe/Sarajevo"                  : ["+01:00", "+01:00", "CET"],
      "Europe/Simferopol"                : ["+03:00", "+03:00", "MSK"],
      "Europe/Skopje"                    : ["+01:00", "+01:00", "CET"],
      "Europe/Sofia"                     : ["+02:00", "+02:00", "EET"],
      "Europe/Stockholm"                 : ["+01:00", "+01:00", "CET"],
      "Europe/Tallinn"                   : ["+02:00", "+02:00", "EET"],
      "Europe/Tirane"                    : ["+01:00", "+01:00", "CET"],
      "Europe/Tiraspol"                  : ["+02:00", "+02:00", "EET"],
      "Europe/Uzhgorod"                  : ["+02:00", "+02:00", "EET"],
      "Europe/Vaduz"                     : ["+01:00", "+01:00", "CET"],
      "Europe/Vatican"                   : ["+01:00", "+01:00", "CET"],
      "Europe/Vienna"                    : ["+01:00", "+01:00", "CET"],
      "Europe/Vilnius"                   : ["+02:00", "+02:00", "EET"],
      "Europe/Volgograd"                 : ["+03:00", "+03:00", "MSK"],
      "Europe/Warsaw"                    : ["+01:00", "+01:00", "CET"],
      "Europe/Zagreb"                    : ["+01:00", "+01:00", "CET"],
      "Europe/Zaporozhye"                : ["+02:00", "+02:00", "EET"],
      "Europe/Zurich"                    : ["+01:00", "+01:00", "CET"],
      "GB"                               : ["+00:00", "+00:00", "GMT"],
      "GB-Eire"                          : ["+00:00", "+00:00", "GMT"],
      "GMT"                              : ["+00:00", "+00:00", "GMT"],
      "GMT+0"                            : ["+00:00", "+00:00", "GMT"],
      "GMT-0"                            : ["+00:00", "+00:00", "GMT"],
      "GMT0"                             : ["+00:00", "+00:00", "GMT"],
      "Greenwich"                        : ["+00:00", "+00:00", "GMT"],
      "Hongkong"                         : ["+08:00", "+08:00", "HKT"],
      "Iceland"                          : ["+00:00", "+00:00", "GMT"],
      "Indian/Antananarivo"              : ["+03:00", "+03:00", "EAT"],
      "Indian/Chagos"                    : ["+06:00", "+06:00", "IOT"],
      "Indian/Christmas"                 : ["+07:00", "+07:00", "CXT"],
      "Indian/Cocos"                     : ["+06:30", "+06:30", "CCT"],
      "Indian/Comoro"                    : ["+03:00", "+03:00", "EAT"],
      "Indian/Kerguelen"                 : ["+05:00", "+05:00", "TFT"],
      "Indian/Mahe"                      : ["+04:00", "+04:00", "SCT"],
      "Indian/Maldives"                  : ["+05:00", "+05:00", "MVT"],
      "Indian/Mauritius"                 : ["+04:00", "+04:00", "MUT"],
      "Indian/Mayotte"                   : ["+03:00", "+03:00", "EAT"],
      "Indian/Reunion"                   : ["+04:00", "+04:00", "RET"],
      "Iran"                             : ["+03:30", "+04:30", "IRDT"],
      "Israel"                           : ["+02:00", "+03:00", "IDT"],
      "Jamaica"                          : ["−05:00", "-05:00", "EST"],
      "Japan"                            : ["+09:00", "+09:00", "JST"],
      "Kwajalein"                        : ["+12:00", "+12:00", "MHT"],
      "Libya"                            : ["+02:00", "+02:00", "EET"],
      "Mexico/BajaNorte"                 : ["−08:00", "-07:00", "PDT"],
      "Mexico/BajaSur"                   : ["−07:00", "-07:00", "MST"],
      "Mexico/General"                   : ["−06:00", "-06:00", "CST"],
      "NZ"                               : ["+12:00", "+13:00", "NZDT"],
      "NZ-CHAT"                          : ["+12:45", "+13:45", "CHADT"],
      "Navajo"                           : ["−07:00", "-06:00", "MDT"],
      "PRC"                              : ["+08:00", "+08:00", "CST"],
      "Pacific/Apia"                     : ["+13:00", "+14:00", "WSDT"],
      "Pacific/Auckland"                 : ["+12:00", "+13:00", "NZDT"],
      "Pacific/Chatham"                  : ["+12:45", "+13:45", "CHADT"],
      "Pacific/Chuuk"                    : ["+10:00", "+10:00", "CHUT"],
      "Pacific/Easter"                   : ["−06:00", "-05:00", "EASST"],
      "Pacific/Efate"                    : ["+11:00", "+11:00", "VUT"],
      "Pacific/Enderbury"                : ["+13:00", "+13:00", "PHOT"],
      "Pacific/Fakaofo"                  : ["+13:00", "+13:00", "TKT"],
      "Pacific/Fiji"                     : ["+12:00", "+12:00", "FJT"],
      "Pacific/Funafuti"                 : ["+12:00", "+12:00", "TVT"],
      "Pacific/Galapagos"                : ["−06:00", "-06:00", "GALT"],
      "Pacific/Gambier"                  : ["−09:00", "-09:00", "GAMT"],
      "Pacific/Guadalcanal"              : ["+11:00", "+11:00", "SBT"],
      "Pacific/Guam"                     : ["+10:00", "+10:00", "ChST"],
      "Pacific/Honolulu"                 : ["−10:00", "-10:00", "HST"],
      "Pacific/Johnston"                 : ["−10:00", "-10:00", "HST"],
      "Pacific/Kiritimati"               : ["+14:00", "+14:00", "LINT"],
      "Pacific/Kosrae"                   : ["+11:00", "+11:00", "KOST"],
      "Pacific/Kwajalein"                : ["+12:00", "+12:00", "MHT"],
      "Pacific/Majuro"                   : ["+12:00", "+12:00", "MHT"],
      "Pacific/Marquesas"                : ["−09:30", "-09:30", "MART"],
      "Pacific/Midway"                   : ["−11:00", "-11:00", "SST"],
      "Pacific/Nauru"                    : ["+12:00", "+12:00", "NRT"],
      "Pacific/Niue"                     : ["−11:00", "-11:00", "NUT"],
      "Pacific/Norfolk"                  : ["+11:30", "+11:30", "NFT"],
      "Pacific/Noumea"                   : ["+11:00", "+11:00", "NCT"],
      "Pacific/Pago_Pago"                : ["−11:00", "-11:00", "SST"],
      "Pacific/Palau"                    : ["+09:00", "+09:00", "PWT"],
      "Pacific/Pitcairn"                 : ["−08:00", "-08:00", "PST"],
      "Pacific/Pohnpei"                  : ["+11:00", "+11:00", "PONT"],
      "Pacific/Ponape"                   : ["+11:00", "+11:00", "PONT"],
      "Pacific/Port_Moresby"             : ["+10:00", "+10:00", "PGT"],
      "Pacific/Rarotonga"                : ["−10:00", "-10:00", "CKT"],
      "Pacific/Saipan"                   : ["+10:00", "+10:00", "ChST"],
      "Pacific/Samoa"                    : ["−11:00", "-11:00", "SST"],
      "Pacific/Tahiti"                   : ["−10:00", "-10:00", "TAHT"],
      "Pacific/Tarawa"                   : ["+12:00", "+12:00", "GILT"],
      "Pacific/Tongatapu"                : ["+13:00", "+13:00", "TOT"],
      "Pacific/Truk"                     : ["+10:00", "+10:00", "CHUT"],
      "Pacific/Wake"                     : ["+12:00", "+12:00", "WAKT"],
      "Pacific/Wallis"                   : ["+12:00", "+12:00", "WFT"],
      "Pacific/Yap"                      : ["+10:00", "+10:00", "CHUT"],
      "Poland"                           : ["+01:00", "+01:00", "CET"],
      "Portugal"                         : ["+00:00", "+00:00", "WET"],
      "ROC"                              : ["+08:00", "+08:00", "CST"],
      "ROK"                              : ["+09:00", "+09:00", "KST"],
      "Singapore"                        : ["+08:00", "+08:00", "SGT"],
      "Turkey"                           : ["+02:00", "+02:00", "EET"],
      "UCT"                              : ["+00:00", "+00:00", "UCT"],
      "US/Alaska"                        : ["−09:00", "-08:00", "AKDT"],
      "US/Aleutian"                      : ["−10:00", "-09:00", "HADT"],
      "US/Arizona"                       : ["−07:00", "-07:00", "MST"],
      "US/Central"                       : ["−06:00", "-05:00", "CDT"],
      "US/East-Indiana"                  : ["−05:00", "-04:00", "EDT"],
      "US/Eastern"                       : ["−05:00", "-04:00", "EDT"],
      "US/Hawaii"                        : ["−10:00", "-10:00", "HST"],
      "US/Indiana-Starke"                : ["−06:00", "-05:00", "CDT"],
      "US/Michigan"                      : ["−05:00", "-04:00", "EDT"],
      "US/Mountain"                      : ["−07:00", "-06:00", "MDT"],
      "US/Pacific"                       : ["−08:00", "-07:00", "PDT"],
      "US/Samoa"                         : ["−11:00", "-11:00", "SST"],
      "UTC"                              : ["+00:00", "+00:00", "UTC"],
      "Universal"                        : ["+00:00", "+00:00", "UTC"],
      "W-SU"                             : ["+03:00", "+03:00", "MSK"],
      "Zulu"                             : ["+00:00", "+00:00", "UTC"],
    }

  # Get a +ve or -ve human readable timestamp based off the local time
  def time_stamp(self, value="auto", tflags = ''):

    if isinstance(value, str) and value in self.timezones:
      # Set env to specified timezone
      os.environ['TZ'] = value
      # Reset time conversion rules
      time.tzset()
      # Return formatted timestring
      return time.strftime(tflags)

    else:
      # Use default timezone or UTC at worst
      os.environ['TZ'] = s.get("timezone") if s.get("timezone") in self.timezones else 'UTC'
      # Reset time conversion rules
      time.tzset()
      # Grab datetime object for arithmetic
      now = datetime.now()

    # A time offset was specified
    if value != "auto":

      offset = value

      # If a dictionary of offsets was not passed in
      if not isinstance(offset, dict):

        offset = {}

        # Cast to list if a single offset was passed as a string
        if not isinstance(value, list):
          value = [value]

        # Safely cast the list to a dictionary
        for items in value:
          if ":" in items:
            val = items.split(":")
            offset[val[0].strip()] = val[1].strip()
          elif "=" in items:
            val = items.split("=")
            offset[val[0].strip()] = val[1].strip()

          # Cool one liner cast... but not safe!
          # offset = dict(items.split("=") for items in value)

      # Apply each offset to the current time
      if "microseconds" in offset:
        now += timedelta(microseconds = float(offset["microseconds"]))

      if "milliseconds" in offset:
        now += timedelta(milliseconds = float(offset["milliseconds"]))

      if "seconds" in offset:
        now += timedelta(seconds      = float(offset["seconds"]))

      if "minutes" in offset:
        now += timedelta(minutes      = float(offset["minutes"]))

      if "hours" in offset:
        now += timedelta(hours        = float(offset["hours"]))

      if "days" in offset:
        now += timedelta(days         = float(offset["days"]))

      if "weeks" in offset:
        now += timedelta(weeks        = float(offset["weeks"]))

      if "months" in offset:

        # Get current date info
        months = float(offset["months"])
        today  = datetime.today()
        year   = today.year

        # Check for leap year
        year = 366 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 365

        # Get the future or past date
        date = today + timedelta(months*year/12)

        # Calculate difference in days
        days = (date - today).days

        # Add the offset
        now += timedelta(days = days)

      if "years" in offset:

        # Get current year
        year = datetime.today().year

        # Check for leap year
        year = 366 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 365

        # Convert years to days
        days = float(offset["years"]) * year

        # Add the offset
        now += timedelta(days = days)

    # Convert datetime object to epoch timestamp
    totalsecs = (now - datetime.fromtimestamp(0)).total_seconds()

    # Convert back to time object for consistent formatting (%Z %z)
    return time.strftime(tflags, time.localtime(totalsecs))


  #-- Regex Helpers ---------------------------------------------------------------------


  # Build the auto regex pattern
  def regexify(self, stamp):

    return s.get("autoregex").format(stamp)

    # Experimental auto time regex builder, not ready yet
    if "tflag" in m[stamp]:
      return self.timexify(m[stamp]["tflag"])
    else:
      return s.get("autoregex").format(stamp)

  # *** WARNING *** DANGEROUS REGEX PATTERNS IN HERE...NOT READY FOR USE YET!
  def timexify(self, regex):
    # Experimental build for auto strftime() patterns.

    swaps = {
      "%a": "(Mon|Tue|Wed|Thu|Fri|Sat|Sun)",
      "%A": "(Monday|Tueday|Wednesday|Thursday|Friday|Saturday|Sunday)",
      "%b": "(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",
      "%B": "(January|February|March|April|May|June|July|August|September|October|November|December)",
      "%C": "([0-2][0-1])",
      "%c": "(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\s|\s\s)(\d|\d\d)\s(\d\d:\d\d:\d\d)\s\d\d\d\d",
      "%D": "([0-1]\d/[0-3]\d/\d\d)",
      "%d": "([0-3]\d)",
      "%e": "([1-3]\d)",
      #"%E": "",
      "%F": "([0-2]\d\d\d-[0-1]\d-[0-3]\d)",
      #"%f": "",
      "%g": "(\d\d)",
      "%G": "([0-2]\d\d\d)",
      "%H": "([0-2]\d)",
      "%h": "(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",
      "%I": "([0-1]\d)",
      #"%i": "",
      "%j": "([0-3]\d\d)",
      #"%J": "",
      "%k": "([0-2]\d)",
      #"%K": "",
      "%l": "([1-9]|11|12])",
      "%L": "",
      "%M": "([0-5]\d)",
      "%m": "([0-1]\d)",
      #"%n": "(\n)",
      #"%N": "",
      #"%O": "",
      #"%o": "",
      #"%P": "",
      "%p": "(AM|PM)",
      #"%Q": "",
      #"%q": "",
      "%r": "([0-1]\d:[0-5]\d:[0-5]\d\s(AM|PM))",
      "%R": "([0-2]\d):([0-5]\d)",
      "%S": "([0-5]\d)",
      "%s": "(1\d\d\d\d\d\d\d\d\d)",
      "%T": "([0-2]\d:[0-5]\d:[0-5]\d)",
      #"%t": "(\t)",
      "%U": "([0-5]\d)",
      "%u": "([1-7])",
      "%V": "([0-5]\d)",
      "%v": "([0-3]\d)-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-([0-2]\d\d\d)",
      "%W": "([0-5]\d)",
      "%w": "([0-6])",
      "%x": "([0-1]\d/[0-3]\d/\d\d)",
      "%X": "([0-2]\d:[0-5]\d:[0-5]\d)",
      "%y": "(\d\d)",
      "%Y": "([0-2]\d\d\d)",
      "%z": "((\+|-)[0-2]\d[0-5]\d)",
      "%Z": "([A-Z]([A-Z]|h)[A-Z]{1,3})",
    }

    for rgx, val in swaps.items():
      regex = re.sub(rgx, val, regex)

    return regex


  #-- Stamp Helpers ---------------------------------------------------------------------


  # Builds the auto stamp pattern
  def stampify(self, stamp, values):

    injection_flags = ""
    i = 0

    # Add an injection flag for each item
    if isinstance(values, list):
      for value in values:
        injection_flags += "{" + str(i) + "} "
        i += 1

    # Add an injection flag for single item
    else:
      injection_flags = "{0}"

    # Format injection string
    return s.get("autostamp").format(stamp, injection_flags)

  # Generate clean checksum of the file contents
  def checksum(self):

    mode = s.get("hash_mode")

    hashes = {
      'sha512': '[a-h0-9]{128}',
      'sha384': '[a-h0-9]{96}',
      'sha256': '[a-h0-9]{64}',
      'sha224': '[a-h0-9]{56}',
      'sha1'  : '[a-h0-9]{40}',
      'md5'   : '[a-h0-9]{32}',
    }

    # Remove existing checksums from contents and recalculate
    nohash = re.sub(hashes[mode], '', self.data)

    # Convert string to bytes
    encode = nohash.encode(encoding='UTF-8')

    # Generate a hash of the document
    if   mode == 'sha512':
      return hashlib.sha51(encode).hexdigest()

    elif mode == 'sha384':
      return hashlib.sha384(encode).hexdigest()

    elif mode == 'sha256':
      return hashlib.sha256(encode).hexdigest()

    elif mode == 'sha224':
      return hashlib.sha224(encode).hexdigest()

    elif mode == 'sha1':
      return hashlib.sha1(encode).hexdigest()

    elif mode == 'md5':
      return hashlib.md5(encode).hexdigest()

  # Grabs file and path meta
  def get_file(self, prop="file_name", filepath=os.getcwd()):

    # If file is currently unsaved and has no path
    if filepath == None:
      return "unknown"

    # Something was passed, so try to get the basename and extension
    else:
      (basename, ext) = os.path.splitext(filepath)

      # File name without extension
      if prop == "file_name":
        return os.path.basename(basename)

      # File name with extension
      if prop == "file_extname":
        return os.path.basename(filepath)

      # File path
      elif prop == "file_path":
        return filepath

      # File size
      elif prop == "file_size":
        return os.stat(filepath).st_size

      # File extension
      elif prop == "extension":
        return ext.strip('.')

      # Basename of the current file
      elif prop == "base_name":
        return basename

      # Parent folder's name
      elif prop == "parent_name":
        return os.path.split(os.path.dirname(filepath))[1]

      # Parent folder's path, nothing if unsaved file
      elif prop == "parent_path":
        return os.path.abspath(os.path.join(filepath, os.pardir))

    # Couldn't find what user was looking for
    return False

  # Builds a single stamp key
  def build_stamp(self, name, value, menu=None, tflag=None):

    stamp = {
      "value": value,
      "stamp": self.stampify(name, "auto"),
      "regex": self.regexify(name),
    }

    if menu != None:
      stamp["menu"] = menu

    if tflag != None:
      stamp["tflag"] = tflag

    return stamp

  # Query magic values and add to global stamp meta if missing
  def magic_values(self):

    # Add default all values stamp
    m["all"] = {"menu" : "root", "value": "auto"}

    # Add a default last modified key
    m["modified"] = {
      "menu"  : "Time",
      "value" : "auto",
      "regex" : "auto",
      "stamp" : "auto",
      "tflag" : "%c",
    }

    # Grab user info
    userinfo             = s.get("user_info")
    userinfo["username"] = getpass.getuser()

    # Get available magic values
    magic_values = {
      "checksum"     : self.checksum(),
      "extension"    : self.get_file("extension", self.path),
      "base_name"    : self.get_file("base_name", self.path),
      "file_size"    : self.get_file("file_size", self.path),
      "file_name"    : self.get_file("file_name", self.path),
      "file_path"    : self.get_file("file_path", self.path),
      "parent_name"  : self.get_file("parent_name", self.path),
      "parent_path"  : self.get_file("parent_path", self.path),
      "file_extname" : self.get_file("file_extname", self.path),
    }

    # experminetal time regex matching not used yet
    #for letter in map(chr, range(97, 123)):
    #  m[letter] = {
    #    "value": "auto",
    #    "tflag": "%" + letter,
    #    "regex": self.timexify("%" + letter),
    #    "stamp": "auto",
    #  }
    #  m[letter.upper()] = {
    #    "value": "auto",
    #    "tflag": "%" + letter.upper(),
    #    "regex": self.timexify("%" + letter.upper()),
    #    "stamp": "auto",
    #  }

    # Build user defined "auto" regexes and stamps
    for stamp, info in m.items():
      if "stamp" in info and info['stamp'] == 'auto':
        m[stamp]['stamp'] = self.stampify(stamp, info['value'] )
      if "regex" in info and info['regex'] == 'auto':
        m[stamp]['regex'] = self.regexify(stamp)

    # Build magic value stamps
    for stamp, value in magic_values.items():
      if stamp not in m:
        m[stamp] = self.build_stamp(stamp, value, 'File')

    # Build user info stamps
    for stamp, value in userinfo.items():
      if stamp not in m:
        m[stamp] = self.build_stamp(stamp, value, 'User')


#== USER COMMANDS =======================================================================


class LiveStampsInsertCommand(sublime_plugin.TextCommand):


  ''' Wrapper Class For Stamp & Value Injection '''


  def run(self, view, name="username", kind="stamp"):

    global m

    # Grab fresh file, user, document and checksum meta
    self.view.run_command( "live_stamps_refresh" )

    # Inject a stamp
    if kind == "stamp":
      result = self.insert_stamp(name)

    # Inject a value
    else:
      result = self.insert_value(name)

    # Inject results into the current view
    self.view.run_command( "live_stamps_inject", { "data": result } )

    # Add plural to event msg
    if kind == "all":
      kind += "s"

    # Inform the user of the state change, via status bar and console
    msg = "LiveStamps: Inserted " + name + " " + kind
    self.view.run_command( "live_stamps_notify", { "message" : msg, "modes": "console status" } )


  def insert_stamp(self, name):

    # Final output string
    result = ""

    # Inject all values at once, alphabetically
    if name == "all":

      # Sort stamps alphabetically
      sortedKeys = sorted(m.keys())

      # Build the output string piece by piece
      for stamp_name in sortedKeys:
        if "stamp" in m[stamp_name]:
          result += m[stamp_name]["stamp_output"] + "\n"

    # Inject a single stamp
    else:
      result += m[name]["stamp_output"]

    return result


  def insert_value(self, name):

    # Final output string
    result = ""

    # Inject all values at once, alphabetically
    if name == "all":

      # Sort stamps alphabetically
      sortedKeys = sorted(m.keys())

      # Get the length of the longest key
      maxlength = len(max(sortedKeys, key=len))
      formatter = "{0:<"+ str(maxlength) +"s} : {1}\n"

      # Concatenate all stamps and format
      for stamp_name in sortedKeys:
        # Build the output string piece by piece
        details = m[stamp_name]["value_output"]
        # Mimic PHP sprintf for neat output
        result += formatter.format(stamp_name, details)

    # Inject a single stamp
    else:
      result = m[name]["value_output"]

    return result


class LiveStampsHelpCommand(sublime_plugin.TextCommand):


  ''' Quick References For Stamp Creation'''


  def run(self, view, info="time_flags"):

    information = {
      'time_flags'   : self.strftime_reference(),
      'format_flags' : self.format_reference(),
    }

    info = information[info] if info in information else False

    if info != False:
      self.view.run_command( "live_stamps_inject", { "data": info } )

  # Output a quick reference for the Python format() function with live formatting
  def format_reference(self):

    flags = {
      "b" : "| (int)    | Format Binary    | Outputs a number in base 2",
      "c" : "| (int)    | Format Unicode   | Converts an integer to the corresponding unicode character",
      "d" : "| (int)    | Format Decimal   | Outputs the number in base 10",
      "e" : "| (float)  | Format [e]xp.    | Prints the number in scientific notation using the letter ‘e’ to indicate the exponent. The default precision is 6.",
      "E" : "| (float)  | Format [E]xp.    | Same as 'e' except uses an upper case ‘E’ as the separator character",
      "f" : "| (float)  | Format Fixed Pt. | Displays the number as a fixed-point number. The default precision is 6",
      "F" : "| (float)  | Format Fixed Pt. | Same as 'f'. Displays the number as a fixed-point number. The default precision is 6",
      "g" : "| (float)  | Format G(e)neral | Formats numbers to fixed point or scientific depending on size",
      "G" : "| (float)  | Format G(E)neral | Same as 'g' except switches to 'E' as the separator character",
      "n" : "| (float)  | Format Local     | Same as 'g', except uses locale specific number separators.",
      "o" : "| (int)    | Format Octal     | Outputs the number in base 8",
      "s" : "| (string) | Format Format    | This is the default type for strings and may be omitted",
      "x" : "| (int)    | Format Hex       | Outputs the number in base 16, using lowercase letters for the digits above 9",
      "X" : "| (int)    | Format HEX       | Same as 'x' using uppercase letters for the digits above 9",
      "%" : "| (float)  | Format Percent   | Multiplies the number by 100 followed by a percent sign",
      ">" : "| (string) | Justify Right    | Right justifies the field within the designated space",
      "<" : "| (string) | Justify Left     | Left justifies the field within the designated space",
      "^" : "| (string) | Justify Center   | Center justifies the field within the designated space",
      "=" : "| (string) | Justify Number   | Forces padding to be placed after the sign (if any) but before the digits, only valid for numeric types",
      "," : "| (int)    | Comma Separator  | Signals the use of a comma for a thousands separator. For a locale aware separator, use 'n' instead",
      "+" : "| (number) | Positive Flag    | Indicates a sign should be used for both positive and negative numbers",
      "-" : "| (number) | Negative Flag    | Indicates a sign should only be used for negative numbers (default behavior)",
      "#" : "| (int)    | Base Prefix      | Prefixes number system base numbers (0b, 0o, 0x) for integers in binary, octal, or hexadecimal",
      "." : "| (float)  | Precision        | Decimal dot followed by a number specifies (non-zero) precision (default 6)",
    }

    # Generate A random number
    random = randint(10000,11000)

    # Get the longest line length
    lidx = len(max(flags.values(), key=len))

    # Build the header
    header  = "| Usage   | Output ("+str(random)+")  | Works On | Name             | Format Spec: { [ [fill] align] [sign] [#] [0] [width] [,] [.precision] [type] } "
    border  = "|---------|-----------------|"
    headstr = "{:<" + str(lidx + len(border)) +"}"
    bordstr = "{:-<"+ str(lidx + len(border)) +"}"

    # Add the header, use punctiona keys to make appear at top
    result = {
      " " : headstr.format(header) + "|",
      "!" : bordstr.format(border) + "|",
    }

    idx = 15

    # Iterate all possible format flags
    for flag in flags:

      # Logic gauntlet for special case flags
      if flag in "<>^":
        injection_flag = "{:"+flag+str(idx)+"}"

      elif flag is "=":
        injection_flag = "{:"+flag+"+"+str(idx)+"}"

      elif flag is "#":
        injection_flag = "{:"+flag+"x}"

      elif flag is ".":
        injection_flag = "{:"+flag+"10}"

      else:
        injection_flag = "{:"+flag+"}"

      # Make sure our value is valid for special cases
      value = random if flag != "s" else str(random)
      value = (10/value) if flag == "." else value

      # Calculate and concatenate
      result[flag] = "| " +injection_flag.ljust(7) + " | " + injection_flag.format(value).ljust(idx) + " " + flags[flag].ljust(lidx) + " |"

    # Format the info nicely
    return json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False )

  # Output a quick reference for the Python strftime() function with live formatting
  def strftime_reference(self):

    flags = {
      'a' : "Abbreviated weekday name",
      'A' : "Full weekday name",
      'b' : "Abbreviated month name",
      'B' : "Full month name",
      'C' : "Century number [00-99]",
      'c' : "Preferred date and time representation",
      'D' : "Current date, equal to %m/%d/%y",
      'd' : "Day of the month with leading zeros [01 to 31]",
      'e' : "Day of the month [1 to 31]",
      'E' : "",
      'f' : "",
      'F' : "Current date, equal to %Y-%m-%d",
      'G' : "Four-digit year based off the ISO 8601 week number[0-9999]",
      'g' : "Two-digit year based off the ISO 8601 week number [00-99]",
      'h' : "Abbreviated month name",
      'H' : "Hour using 24-hour notation [00-23]",
      'I' : "Hour using 12-hour notation [01-12]",
      'i' : "",
      'j' : "Day of the year [001-366]",
      'J' : "",
      'k' : "Hour using 24-hour notation without leading zeros [0-23]",
      'K' : "",
      'l' : "Month number without leading zeros [1-12]",
      'L' : "",
      'M' : "Minutes with leading zeros [00-59]",
      'm' : "Month number with leading zeros [01-12]",
      'n' : "Literal newline character",
      'N' : "",
      'o' : "",
      'O' : "",
      'p' : "AM|PM",
      'P' : "",
      'q' : "",
      'Q' : "",
      'r' : "Time in 12 hour notation",
      'R' : "Time in 24 hour notation",
      's' : "Number of seconds since the UNIX epoch",
      'S' : "Seconds with leading zeros [00-59]",
      'T' : "Current time in 24 hour notation with seconds, equal to %H:%M:%S",
      't' : "Literal tab character",
      'U' : "Week number, based off the first sunday of the year",
      'u' : "Weekday as a number [1-7] where Mon=1. Note: In Sun Solaris Sun=1",
      'v' : "Current date, equal to %d-%b-%Y",
      'V' : "ISO 8601 week: Year starts Monday of 1st week with 4 days [01-53]",
      'w' : "Day of the week as a decimal, Sunday=0 [0-6]",
      'W' : "Week number: Year starting first Monday of the year [01-53]",
      'x' : "Preferred DATE representation",
      'X' : "Preferred TIME representation",
      'Y' : "Four-digit year including century",
      'y' : "Two-digit year without century [00-99]",
      'Z' : "Timezone abbreviation, blank on naive objects",
      'z' : "UTC offset in hours: +HHMM or -HHMM results in blank on naive timezone objects",
      '%' : "Literal percent character"
    }

    # Get the longest line length
    idx = len(max(flags.values(), key=len))

    # Build the header
    header  = "| Flag | Output                   | "+s.get("timezone")+": "+str(datetime.now())
    border  = "|------|--------------------------|"
    headstr = "{:<" + str(idx + len(border) + 2) +"}"
    bordstr = "{:-<"+ str(idx + len(border) + 2) +"}"

    # Add the header
    result = {
      " " : headstr.format(header) + "|",
      "!" : bordstr.format(border) + "|",
    }

    tidx = len(time.strftime("%c"))

    # Calculate and concatenate
    for dn in map(chr, range(97, 123)):
      result[dn] = "|  %" + dn + "  | " + time.strftime("%"+dn).ljust(tidx) + " | " + str(flags[dn]).ljust(idx) + " |"

      if dn != "%":
        up = dn.upper()
        result[up] = "|  %" + up + "  | " + time.strftime("%"+up).ljust(tidx) + " | " + str(flags[up]).ljust(idx) + " |"

    # Format the info nicely
    return json.dumps(result, sort_keys=True, indent=2 )


class LiveStampsMenuCommand(sublime_plugin.TextCommand):


  ''' Generates Plugin Menus '''


  def run(self, edit, menu="context"):

    global m


    self.package_path = sublime.packages_path() + "/LiveStamps/"

    # Build every menu, one by one
    if menu == "all":
      self.view.run_command( "live_stamps_menu", { "menu" : "context" } )
      self.view.run_command( "live_stamps_menu", { "menu" : "toolbar" } )
      self.view.run_command( "live_stamps_menu", { "menu" : "sidebar" } )
      self.view.run_command( "live_stamps_menu", { "menu" : "command" } )

    # Build a single menu
    else:

      # Get latest stamp definitions
      self.view.run_command( "live_stamps_refresh" )

      # Sort them
      self.stamp_keys = self.sort_stamps()

      # Figure out menu and filename
      if menu == "context":
        menujson = self.get_context_menu()
        menuname = "Context.sublime-menu"

      elif menu == "toolbar":
        menujson = self.get_toolbar_menu()
        menuname = "Main.sublime-menu"

      elif menu == "sidebar":
        menujson = self.get_sidebar_menu()
        menuname = "Side Bar.sublime-menu"

      elif menu == "command":
        menujson = self.get_command_menu()
        menuname = "LiveStamps.sublime-commands"

      else:
        self.refresh()
        return



      # Concatenate the appropriate filename
      menuname = self.package_path + menuname

      # Make sure menu is a list for sublime
      if not isinstance(menujson, list):
        menujson = [menujson]

      # Write the new menu
      self.view.run_command( "live_stamps_write_file", { "fname" : menuname, "contents" : json.dumps( menujson, sort_keys=False, indent=2 ) })

      # Inform the user of the state change, via status bar and console
      msg = "LiveStamps: Generating " + menu + " menu"
      self.view.run_command( "live_stamps_notify", { "message" : msg, "modes" : "console status" })


  # Refreshes existing menus
  def refresh(self):

    menus = self.get_current_menus()

    # Look for backups
    for menu in menus:
      self.view.run_command( "live_stamps_menu", { "menu" : menu } )

  # Get currently active menus
  def get_current_menus(self):

    result = {}

    menus = {
      "context" : "Context.sublime-menu",
      "sidebar" : "Side Bar.sublime-menu",
      "toolbar" : "Main.sublime-menu",
      "command" : "LiveStamps.sublime-commands"
    }

    files = os.listdir(self.package_path)

    for menu, fname in menus.items():
      if fname in files:
        result[menu] = fname

    return result

  #-- I/O Helpers -----------------------------------------------------------------------


  # Write the menu to file
  def write_menu(self, fname, contents=False):

    ftemp = open(fname, "wb")

    if contents:
      ftemp.write(bytes(contents, 'UTF-8'))
    else:
      ftemp.write(self.get_text())

    ftemp.close

  # Insert the menu into the current view
  def paste_menu(self, menu):
    self.view.run_command( "live_stamps_inject", { "data": menu } )


  #-- Menu Constructors -----------------------------------------------------------------


  # Sort user defined stamps into submenus
  def sort_stamps(self):

    # Create our menu dictionary with a root menu by default
    menus = {'root': []}

    # Iterate the dictionary alphebetically
    for stamp in sorted(m.keys()):

      # If a stamp has a menu key defined...
      if "menu" in m[stamp]:

        # Get the submenu name
        submenu = m[stamp]["menu"]

        # Append the command to the submenu, create on first instance
        if submenu not in menus:
          menus[submenu] = [stamp]
        else:
          menus[submenu].append(stamp)

      # Otherwise add to the root menu
      else:
        menus['root'].append(stamp)

    # Sort subkeys for consistent reading when debugging
    for menu in menus:
      menus[menu] = sorted(menus[menu])

    return menus

  # Build an ordered menu key
  def build_key(self, caption, command, args = None):

    # Build a menu key with arguments
    if isinstance(args, dict):
      return  OrderedDict([
                ("caption", caption.title().replace("_", " ")),
                ("command", command),
                ("args"   , args),
              ])

    # Otherwise, build a menu key with no arguments
    return  OrderedDict([
              ("caption", caption.title().replace("_", " ")),
              ("command", command),
            ])

  # Create an empty menu with headers
  def build_menu(self, caption="Submenu", ID=False, mnemonic=False):

    # Top level menu with ID and mnemonic key
    if ID and mnemonic:
      return OrderedDict([
          ("caption", caption),
          ("id", ID),
          ("mnemonic", mnemonic),
          ("children"   , []),
        ])

    # Top level menu with ID
    elif ID:
      return OrderedDict([
          ("caption", caption),
          ("id", ID),
          ("children"   , []),
        ])

    # Just a submenu
    return OrderedDict([
        ("caption", caption),
        ("children"   , []),
      ])

  # Add a menu divider
  def add_divider(self, parent):

    parent['children'].append( {"caption" : '-'} )

    return parent

  # Add a menu to another menu
  def add_submenu(self, parent, child):

    parent["children"].append(child)

    return parent

  # Check caption/argument pairs are formatted as a valid dictionary
  def cap_check(self, command, argkeys, cap_args):

    result = {}

    # A dict was passed, all good
    if isinstance(cap_args, dict):
      result = cap_args

    # If a list of captions was passed use them as captions
    elif isinstance(cap_args, list):
      for caption in cap_args:
        result[caption] = caption if argkeys else None

    # If a string was passed use as the caption
    elif isinstance(cap_args, str):
      result = {
        cap_args : cap_args if argkeys else None
      }

    # No cap_args specified, use command as the caption
    else:
      result = {
        command : command
      }

    return result #OrderedDict(sorted(result.items()))

  # Add keys to a parent menu with a common command
  def add_keys(self, parent, keymap, sort = False):
    '''
      If no arg_keys and no cap_args specified, the command is used as the caption
      If arg_keys but no cap_args are specified, arg_keys are used for each caption
      If a string is specified as cap_args, it is used as the caption
      If a list is specified as cap_args, each item is used as the caption
      If a dict is specified as cap_args, each key is used as the caption
    '''

    # Assign some vars for clarity
    command = keymap['command']
    argkeys = keymap['arg_keys'] if 'arg_keys' in keymap else None
    capargs = keymap['cap_args'] if 'cap_args' in keymap else None

    keymap = self.cap_check(command, argkeys, capargs)

    # Build each key
    for caption, argument in keymap.items():

      # When the command has no arguments, save some work
      if argkeys == None:
        parent['children'].append( self.build_key(caption, command) )

      # Otherwise, format the arguments
      else:

        # Reset our argument formatter
        arg_result = {}

        # If a string was passed, inject our values into it and convert to dict
        if isinstance(argkeys, str):

          if isinstance(argument, list):
            key = argkeys % tuple(argument)
          else:
            key = argkeys % argument

          arg_result = json.loads(key)

        # If a dict was passed, reassign base keys, based on specified integer
        elif isinstance(argkeys, dict):

          # If a single string is passed, convert to a list
          if not isinstance(argument, list):
            argument = [argument]

          # Iterate and assign
          for key in argkeys:

            # When an int is found, assign the dict key to the apprpriate list index
            if isinstance(argkeys[key], int):
              arg_result[key] = argument[ argkeys[key] ]
            else:
              arg_result[key] = argkeys[key]

        # Finally, add our formatted menu key to the parent menu
        parent['children'].append( self.build_key(caption, command, arg_result) )


    # Sort commands by caption key if specified
    if sort:
      parent['children'] = sorted(parent['children'], key=lambda k: k['caption'])

    # All done! Return the menu with the appended keys
    return parent

  # Recursively flatten all submenus to a single list of commands
  def get_commands(self, menu):

    result = []

    # Iterate top dictionary keys
    for item in menu:

      # If the menu is a dictionary and contains children, recurse
      if item == 'children':
        children = self.get_commands( menu[item] )
        for command in children:
          result.append( command )

      # If the menu is a list and an item has children, recurse
      elif 'children' in item:
        children = self.get_commands( item )
        for command in children:
          result.append( command )

      # Finally, if an item contains a command we store it
      elif 'command' in item:
        result.append( item )

    return result


  #-- Submenu Macros --------------------------------------------------------------------


  # Submenu: Insert Stamps
  def get_stamp_menu(self, header='Insert Stamp', ID=False, mnemonic=False):

    # Define the submenu
    menu = self.build_menu(header, ID, mnemonic)

    # Iterate the sorted stamp commands
    for submenu in self.stamp_keys:

      key = {
        "command"  : "live_stamps_insert",
        "arg_keys" : {"kind" : "stamp", "name": 0},
        "cap_args" : self.stamp_keys[submenu],
      }

      # Add to root commands
      if submenu == 'root':
        self.add_keys(menu, key)

      # Add to submenu
      else:
        self.add_submenu(menu, self.add_keys( self.build_menu( submenu ), key ) )

    # Sort stamps by caption key
    menu['children'] = sorted(menu['children'], key=lambda k: k['caption'])

    return menu

  # Submenu: Insert Values
  def get_value_menu(self, header='Insert Value', ID=False, mnemonic=False):

    # Define the submenu
    menu = self.build_menu(header, ID, mnemonic)

    # Iterate the sorted stamp commands
    for submenu in self.stamp_keys:

      key = {
        "command"  : "live_stamps_insert",
        "arg_keys" : {"kind" : "value", "name": 0},
        "cap_args" : self.stamp_keys[submenu],
      }

      # Add to root commands
      if submenu == 'root':
        self.add_keys(menu, key)

      # Add to submenu
      else:
        self.add_submenu(menu, self.add_keys( self.build_menu( submenu ), key ) )

    # Sort commands by caption key
    menu['children'] = sorted(menu['children'], key=lambda k: k['caption'])

    return menu

  # Submenu: Highlighting Options
  def get_hilite_menu(self, header='Highlighting', ID=False, mnemonic=False):

    # Define the menu
    menu = self.build_menu(header, ID, mnemonic)

    # Add root commands
    self.add_keys(menu, {
      "command"  : "live_stamps_toggle",
      "arg_keys" : {"mode": 0},
      "cap_args" : ["enabled"],
    })

    self.add_divider(menu)

    # Add root commands
    self.add_keys(menu, {
      "command"  : "live_stamps_toggle",
      "arg_keys" : {"mode": 0},
      "cap_args" : ["outline", "shading"],
    }, True)

    # Create Marker submenu
    markers = self.add_keys(self.build_menu("Markers"), {
      "command"  : "live_stamps_toggle",
      "arg_keys" : {"mode": "markers", "value": 0},
      "cap_args" : ["none", "dot", "circle", "bookmark", "cross"],
    }, True)

    # Create Marker submenu
    underlines = self.add_keys(self.build_menu("Underline"), {
      "command"  : "live_stamps_toggle",
      "arg_keys" : {"mode": "underline", "value": 0},
      "cap_args" : ["none", "stippled", "squiggly", "solid"],
    }, True)

    # Add menu marker and underline submenus
    self.add_submenu( menu, markers )
    self.add_submenu( menu, underlines )

    return menu

  # Submenu: Checksum Mode
  def get_checksum_menu(self, header='Checksum Mode', ID=False, mnemonic=False):

    # Define the menu
    menu = self.build_menu(header, ID, mnemonic)

    # Add Checksum submenu
    return self.add_keys(menu, {
      "command"  : "live_stamps_toggle",
      "arg_keys" : {"mode": "hash_mode", "value": 0},
      "cap_args" : ["md5", "sha1", "sha224", "sha256", "sha384", "sha512"],
    }, True)

  # Submenu: Help
  def get_help_menu(self, header='Help', ID=False, mnemonic=False):

    # Define the menu
    menu = self.build_menu(header, ID, mnemonic)

    self.add_keys(menu, {
      "command"  : "open_file",
      "arg_keys" : '{"file" : "${packages}/LiveStamps/%s"}',
      "cap_args" : { "README.md" : "README.md" }
    })

    # Add format submenu
    return self.add_keys(menu, {
      "command"  : "live_stamps_help",
      "arg_keys" : '{"info": "%s"}',
      "cap_args" : {
        'Format() Reference'   : "format_flags",
        'Strftime() Reference' : "time_flags",
      },
    })

  # Submenu: Definitions
  def get_definitions_menu(self, header='Definitions', ID=False, mnemonic=False):

    # Define the menu
    menu = self.build_menu(header, ID, mnemonic)

    # Create the restore submenu from a list of current backup files
    capargs = {}

    # Check definitions directory exists
    self.view.run_command( "live_stamps_definitions", { "task" : "check_dir" } );

    # Look for backups
    for fname in os.listdir(s.get("backup_dir")):
      if ".sublime-settings" in fname:
        capargs[fname.replace(".sublime-settings", "")] = fname

    self.add_keys(menu, {
      "command"  : "open_file",
      "arg_keys" : '{"file" : "${packages}/User/%s"}',
      "cap_args" : { "Open" : "LiveStampsDefinitions.sublime-settings" }
    })

    self.add_divider(menu)

    self.add_keys(menu, {
      "command"  : "live_stamps_definitions",
      "arg_keys" : {"task": 0},
      "cap_args" : "backup"
    })

    # Deep call for submenu! (just for fun)
    backup = self.add_keys(self.build_menu("Restore"), {
      "command"  : "live_stamps_definitions",
      "arg_keys" : '{"task": "restore", "file_name": "%s"}',
      "cap_args" : capargs
    }, True)

    self.add_divider(backup)

    self.add_keys(backup, {
      "command"  : "live_stamps_definitions",
      "arg_keys" : {"task": 0},
      "cap_args" : {"browse..." : "browse"}
    })

    self.add_submenu(menu, backup)

    self.add_divider(menu)


    # Add root keys and return
    return self.add_keys(menu, {
      "command"  : "live_stamps_definitions",
      "arg_keys" : {"task": 0},
      "cap_args" : ["dump", "flush"]
    })

  # Submenu: Menu Generation
  def get_menugen_menu(self, header='Menus', ID=False, mnemonic=False):

    # Define the menu
    menu = self.build_menu(header, ID, mnemonic)

    # Add sorted launch submenu
    launch = self.add_keys(self.build_menu("Open"), {
      "command"  : "open_file",
      "arg_keys" : '{"file" : "${packages}/LiveStamps/%s"}',
      "cap_args" : self.get_current_menus()
    }, True)

    # Add sorted build submenu
    build = self.add_keys(self.build_menu("Build"), {
      "command"  : "live_stamps_menu",
      "arg_keys" : {"menu": 0},
      "cap_args" : ["all", "command", "context", "sidebar", "toolbar"],
    }, True)

    # Add sorted build submenu
    self.add_keys(menu, {
      "command"  : "live_stamps_menu",
      "arg_keys" : {"menu": 0},
      "cap_args" : ["refresh"],
    })

    # Add submenus
    self.add_divider( menu )
    self.add_submenu( menu, build )
    self.add_submenu( menu, launch )

    return menu

  # Submenu: Plugin Preferences
  def get_preference_menu(self, header='Preferences', ID=False, mnemonic=False):

    # Define the menu
    menu = self.build_menu(header, ID, mnemonic)

    # Add hilite,and checksum submenus
    self.add_submenu( menu, self.get_hilite_menu() )
    self.add_submenu( menu, self.get_checksum_menu() )

    # add reset submenu, ..deep call!
    self.add_submenu(menu, self.add_keys(self.build_menu("Reset"), {
      "command"  : "live_stamps_defaults",
      "arg_keys" : {"mode" : 0},
      "cap_args" : ["stamps", "settings"]
    }))

    # Add single root key
    self.add_submenu( menu, self.build_key("Update On Save", "live_stamps_toggle", {"mode": "auto_update"}) )

    # Add Menu Generation, hilite, menu_generation, and checksum submenus
    self.add_divider( menu )

    # Add divider and default settings commands
    self.add_divider( menu )
    self.add_keys(menu, {
      "command"  : "open_file",
      "arg_keys" : '{"file" : "${packages}/%s/LiveStamps.sublime-settings"}',
      "cap_args" : {
        'Settings – Default' : "LiveStamps",
        'Settings – User'    : "User",
      },
    })

    # Add divider and default keybindings commands, Special case: we create cap_args programatically
    self.add_divider( menu )
    for platform in ['Windows', 'OSX', 'Linux']:
      self.add_keys( menu, {
        "command"  : "open_file",
        "arg_keys" : '{"file":"${packages}/%s/Default (%s).sublime-keymap", "platform":"%s"}',
        "cap_args" : {
          'Key Bindings – Default' : ['LiveStamps', platform, platform],
          'Key Bindings – User'    : ['User',       platform, platform],
        },
      })

    self.add_divider( menu )

    self.add_keys( menu, {
      "command"  : "open_file",
      "arg_keys" : '{"file":"${packages}/%s/LiveStampsDefinitions.sublime-settings"}',
      "cap_args" : {
        'Stamp Definitions  – Default' : "LiveStamps",
        'Stamp Definitions  – User'    : "User",
      },
    })

    return menu


  #-- Main Menu Macros ----------------------------------------------------------------


  # Context Menu
  def get_context_menu(self, header='LiveStamps', ID='timestamps-context-menu', mnemonic=False):

    # Define the menu
    menu = self.build_menu(header, ID, mnemonic)

    # Add submenus and dividers
    self.add_submenu( menu, self.build_key("Update Now", "live_stamps_update") )
    self.add_divider( menu )
    self.add_submenu( menu, self.get_stamp_menu() )
    self.add_submenu( menu, self.get_value_menu() )
    self.add_divider( menu )
    self.add_submenu( menu, self.get_preference_menu() )
    self.add_submenu( menu, self.get_definitions_menu() )
    self.add_submenu( menu, self.get_menugen_menu() )
    self.add_submenu( menu, self.get_help_menu() )

    return menu

  # Toolbar Menu
  def get_toolbar_menu(self):

    # Get all submenus of the final menu
    tools_menu = self.build_menu('Tools', 'tools')
    prefs_menu = self.build_menu('Preferences', 'preferences')
    package_settings_menu = self.build_menu('Package Settings', 'package-settings', 'P')
    livestamps_tools_menu = self.get_context_menu('LiveStamps', 'livestamps-tools-menu')
    livestamps_prefs_menu = self.get_preference_menu('LiveStamps', 'livestamps-preferences-menu')

    # Merge submenus
    package_settings_menu = self.add_submenu(package_settings_menu, livestamps_prefs_menu)
    prefs_menu = self.add_submenu(prefs_menu, package_settings_menu)
    tools_menu = self.add_submenu(tools_menu, livestamps_tools_menu)

    # Append top level menus
    return [tools_menu, prefs_menu]

  # Sidebar Menu
  def get_sidebar_menu(self):

    # Reuse context menu with different ID
    return self.get_context_menu('LiveStamps', 'livestamps-sidebar-menu')

  # Command Pallete Menu
  def get_command_menu(self):

    # Get menu of all commands and flatten
    context = self.get_context_menu()
    commands = self.get_commands(context)

    result = []

    # Iterate and modify captions to ensure unique commands
    for command in commands:

      # Get the command title
      command_name = command['command'].replace('live_stamps_', '').title().replace("_", " ")

      # Special case for values and stamps which have same caption, differentiate by argument
      if 'args' in command and 'stamptype' in command['args']:

        # Un-snake and title case
        name = command['args']['kind'].title().replace("_", " ")
        kind = command['args']['stamptype'].title()

        # Append plugin name, command and arguments to caption
        command['caption'] = 'LiveStamps ' + command_name + ': ' + name + ' ' + kind

      # Otherwise, append plugin name and command to caption
      else:
        command['caption'] = 'LiveStamps ' + command_name + ': ' + command['caption']

      # Store command with modified caption
      result.append( command )

    # Sort modified dictionaries by caption key
    result = sorted(result, key=lambda k: k['caption'])

    return result


class LiveStampsUpdateCommand(sublime_plugin.TextCommand):


  ''' Updates Stamps In The Current View '''


  def run(self, edit):

    global m

    # Grab fresh file, user, document and checksum meta
    self.view.run_command( "live_stamps_refresh" )

    # Update any stamp, except those in a sublime settings files
    if "sublime" not in m["extension"]["value"] and m["file_extname"]["value"] != "LiveStamps.py":

      # Check each stamp for a regex key and discover the regions
      for stamp, info in m.items():
        if 'regex' in info and info['regex'] != 'auto':

          # Find each stamp and replace
          for region in self.view.find_all(info['regex'] , 0):
            self.view.replace(edit, region, info['stamp_output'])

      # Success notifaction
      msg = "LiveStamps: Updated all stamps"

    else:
      # Prevent notifaction
      msg = "LiveStamps: Auto update disabled while editing plugin files."

    # Inform the user of the state change, via status bar and console
    self.view.run_command( "live_stamps_notify", { "message" : msg, "modes": "console status" } )


class LiveStampsToggleCommand(sublime_plugin.TextCommand):


  ''' Toggles Plugin Settings & Menu Status '''


  def run(self, edit, mode, value=None):

    self.value = value

    # Assume boolean True/False by default
    if value == None:

      # Get current State and toggle it
      value = False if s.get(mode) == True else True

      self.value = value

      # Save settings and hange to state to semantic output
      s.set(mode, value)
      sublime.save_settings("LiveStamps.sublime-settings")
      value = "ON" if value else "OFF"

    # Allow explicit values
    else:
      s.set(mode, value)
      sublime.save_settings("LiveStamps.sublime-settings")

    # Inform the user of the value change, via status bar and console
    msg = "LiveStamps: Set " + mode + " to " + str(value)
    self.view.run_command( "live_stamps_notify", { "message" : msg, "modes" : "console status" })

    # Refresh highlighter
    self.view.run_command( "live_stamps_highlight", { "clear" : True } )
    self.view.run_command( "live_stamps_highlight" )


  #-- Menu Actions ----------------------------------------------------------------------


  # Enable menu status checkmarks
  def is_checked(self, **args):

    mode = args['mode']

    # Check for non-boolean values
    if mode in ["markers", "underline", "hash_mode"] and "value" in args:
      return args['value'] == s.get(mode)

    return s.get(mode) != False

  # Hide/Show menu items
  def is_visible(self, **args):

    mode = args['mode']

    # Check for non-boolean values
    if mode in ["markers", "underline", "hash_mode"] and "value" in args:
      return args['value'] != None

    return s.get(mode) != None

  # Enable/Disable menu items
  def is_enabled(self, **args):

    mode = args['mode']

    # Check for non-boolean values
    if mode in ["markers", "underline", "hash_mode"] and "value" in args:
      return args['value'] != 'disabled'

    return s.get(mode) != 'disabled'


class LiveStampsDefaultsCommand(sublime_plugin.TextCommand):


  ''' Restores To Various Default States '''


  def run(self, view, mode="all"):

    global s

    # Stop infinite loop
    s.set("restore_defaults", False)

    # Get user confirmation
    if sublime.ok_cancel_dialog("LiveStamps:\n\nReset all "+ mode +" to defaults?\n\n THIS CAN'T BE UNDONE.\n\n(If this is first load you can safely ignore)"):

      # Reset user stamps
      if mode == "stamps":
        self.view.run_command( "live_stamps_backup" )
        s.erase("stamps")

      # Reset all settings
      else:
        self.view.run_command( "live_stamps_backup" )

        default = [
          "auto_update",
          "autoregex",
          "autostamp",
          "console_events",
          "doc_align",
          "enabled",
          "hash_mode",
          "marker_color",
          "markers",
          "maxsize",
          "outline",
          "outline_color",
          "popup_events",
          "restore_defaults",
          "separator"
          "shading",
          "shading_color",
          "stamps",
          "statusbar_events",
          "timeout",
          "timezone",
          "underline",
          "underline_color",
          "user_info",
        ]

        for key in default:
          s.erase(key)

      # Stop infinite loop
      s.set("restore_defaults", False)
      sublime.save_settings("LiveStamps.sublime-settings")

      # Bring default definitions file
      self.default_defs()

      # Load user info and definitions
      self.view.run_command( "live_stamps_definitions", { "task" : "merge" } );

      # Rebuild the menu with latest definitions
      self.view.run_command( "live_stamps_menu", { "menu": "context" } );

    else:
      # Action aborted, stop infinite loop
      sublime.save_settings("LiveStamps.sublime-settings")

  # Create default definitions file
  def default_defs(self):
    defdir = sublime.packages_path() + "/User/LiveStampDefs"
    source = sublime.packages_path() + "/Livestamps/LiveStampsDefinitions.sublime-settings"
    target = sublime.packages_path() + "/User/LiveStampsDefinitions.sublime-settings"

    if not os.path.exists(defdir):
      os.makedirs(defdir)

    contents = open(source, 'rb')
    contents = contents.read().decode("utf-8")
    self.view.run_command( "live_stamps_write_file", { "fname" : target, "contents" : contents } )


class LiveStampsHighlightCommand(sublime_plugin.TextCommand):


  ''' LiveStamp View Highlighting '''


  def run(self, view, clear=False):

    global s

    # Check settings init
    if s.get("stamps") == None:
      self.view.run_command( "live_stamps_refresh" )

    # Enable highlighting
    if (s.get("enabled") and self.view.size() <= s.get("maxsize")):
      self.highlight()

    # Disable highlighting
    else:
      self.clear()


  #-- Region Helpers --------------------------------------------------------------------


  # Get all matching stamp patterns
  def find(self):

    result = [];

    # Iterate the stamp list
    for stamp, info in m.items():

      # Check if a regex is supplied
      if 'regex' in info:

        regex = info['regex']

        # Final initialization check
        if regex == 'auto':
          self.view.run_command( "live_stamps_refresh" )
          return self.find()

        if regex != '':
          # Find each stamp location
          matches = self.view.find_all(info['regex'], 0)

        # Append the locations to the master list
        for items in matches:
          result.append(items)

    return result

  # Clear all highlighting
  def clear(self):
    self.view.erase_regions("LiveStampsShading")
    self.view.erase_regions("LiveStampsOutline")
    self.view.erase_regions("LiveStampsMarkers")
    self.view.erase_regions("LiveStampsUnderline")

  # Enable highlighting
  def highlight(self):

    # Logic gauntlet to ensure refresh after a mode is enabled/disabled

    # Get user modes
    self.marker_mode     = self.get_marker_mode()
    self.underline_mode  = self.get_underline_mode()

    # Find highlighting regions
    self.regions = self.find()

    # Check if background shading enabled
    if s.get("shading"):
      self.shading()
    else:
      self.view.erase_regions("LiveStampsShading")

    # Check if outlining enabled
    if s.get("outline"):
      self.outline()
    else:
      self.view.erase_regions("LiveStampsOutline")

    # Check if underlining enabled
    if self.underline_mode:
      self.underline()
    else:
      self.view.erase_regions("LiveStampsUnderline")

    # Check if markers enabled
    if self.marker_mode:
      self.markers()
    else:
      self.view.erase_regions("LiveStampsMarkers")

  # Marker mode check
  def get_marker_mode(self):

    mode   = s.get("markers");
    marker = ["dot", "circle", "bookmark", "cross"]

    if mode == True:
      return "dot"
    elif mode in marker:
      return mode
    else:
      return False

  # Underline mode check
  def get_underline_mode(self):

    mode = s.get("underline");

    underline = {
     "solid"    : sublime.DRAW_SOLID_UNDERLINE,
     "stippled" : sublime.DRAW_STIPPLED_UNDERLINE,
     "squiggly" : sublime.DRAW_SQUIGGLY_UNDERLINE,
    }

    if mode == True:
      return sublime.DRAW_SOLID_UNDERLINE
    elif mode in underline:
      return underline[mode]
    else:
      return False


  #-- Highlight Modes -------------------------------------------------------------------


  # Enable gutter markers
  def markers(self):
    self.view.add_regions(
      'LiveStampsMarkers',
      self.regions,
      str(s.get('marker_color')),
      self.marker_mode,
      sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE
    )

  # Enable background highlighting
  def shading(self):
    self.view.add_regions(
      'LiveStampsShading',
      self.regions,
      str(s.get('shading_color')),
      "",
      sublime.DRAW_EMPTY
    )

  # Enable outline/underline
  def outline(self):
    self.view.add_regions(
      'LiveStampsOutline',
      self.regions,
      str(s.get('outline_color')),
      "",
      sublime.DRAW_NO_FILL
    )

  # Enable gutter markers
  def underline(self):
    self.view.add_regions(
      'LiveStampsUnderline',
      self.regions,
      str(s.get('underline_color')),
      "",
      self.underline_mode | sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE
    )


class LiveStampsDefinitionsCommand(sublime_plugin.TextCommand):


  ''' Backup, Restore & Merge Stamp Definitions'''


  def run(self, view, task="merge", file_name=None):

    global s
    global m

    # Get a filename from the current time if non specified
    if not isinstance(file_name, str):
      file_name = time.strftime("%d_%b_%Y_%I_%M_%S_%p")

    # Build paths for variious functions
    self.directory = file_name + ".sublime-settings"
    self.stampdefs = sublime.packages_path() + "/User/LiveStampsDefinitions.sublime-settings"
    self.backupdir = sublime.packages_path() + "/User/LiveStampDefs/"

    # Task decision tree...
    if task == "backup":
      self.backup(file_name)
      msg = "LiveStamps: Created stamp definition backup " + file_name

    elif task == "flush":
      self.flush()
      msg = "LiveStamps: All definition backups flushed from disk"

    elif task == "restore":
      self.restore(file_name)
      msg = "LiveStamps: Restored definitions from " + file_name

    elif task == "dump":
      self.view.run_command( "live_stamps_inject", { "data": self.dump_meta() } )
      msg = "LiveStamps: Dumping stamp metadata"

    elif task == "browse":
      self.view.run_command( "live_stamps_open_folder", { "folder": self.backupdir } )
      msg = False

    elif task == "check_dir":
      self.check_backup_dir()
      msg = False

    else:
      self.merge()
      msg = False


    # Inform the user of the state change, via status bar and console
    if msg != False:
      self.view.run_command( "live_stamps_notify", { "message" : msg, "modes" : "console status" } )

  # Merge user info and definitions into global meta object
  def merge(self):

    global s
    global m

    # Load user defined settings
    u = sublime.load_settings("LiveStampsDefinitions.sublime-settings")

    # Get Stamp definitions & user info
    ddefs = s.get("stamps") if isinstance(s.get("stamps"), dict) else {}
    udefs = u.get("stamps") if isinstance(u.get("stamps"), dict) else {}
    uinfo = u.get("user_info") if isinstance(u.get("user_info"), dict) else {}

    # Merge and store
    m = dict(udefs, **ddefs)
    s.set("user_info", uinfo)
    s.set("backup_dir", self.backupdir)

  # Delete all stamp definitions backups from disk
  def flush(self):

    if sublime.ok_cancel_dialog("Delete all definition backups?\n\n WARNING... This can't be undone."):

      if os.path.exists(self.backupdir):
        shutil.rmtree(self.backupdir)

      self.view.run_command( "live_stamps_menu", { "menu": "context" } );

  # Restore a definition backup from disk
  def restore(self, fname):

    self.check_backup_dir()

    shutil.copy(self.backupdir + fname, self.stampdefs)

  # Backup current stamp definitions to disk
  def backup(self, fname):

    self.check_backup_dir()

    self.view.run_command( "live_stamps_refresh" )

    shutil.copy(self.stampdefs, self.backupdir + self.directory)

    self.view.run_command( "live_stamps_menu", { "menu": "context" } );

  # Output all current stamp metadata
  def dump_meta(self):

    self.view.run_command( "live_stamps_refresh" )

    sortedKeys = sorted(m.keys())

    result = ""

    maxwidth = len(max(m.keys(), key=len))

    for stamp in sortedKeys:
      result += ("\n\n" + stamp.upper() +"\n-----------------------------------------------------------------------------------------\n")
      for name, value in sorted(m[stamp].items()):
        layout = "{0:<"+ str(maxwidth) +"s} : {1}"
        result += layout.format( name, value ) + "\n"

    return result

  # Make sure backup directory exists
  def check_backup_dir(self):

    if not os.path.exists(self.backupdir):

      os.makedirs(self.backupdir)


#== EVENTS ==============================================================================


class LiveStampsListener(sublime_plugin.EventListener):


  ''' Highlight & Autosave Event Listener '''


  def __init__(self):

    # Initialize queue tracker
    self.queue = 0


  #-- Helpers ---------------------------------------------------------------------------


  # Determine if the view is a find results view.
  def is_find_results(view):
    return view.settings().get('syntax') and "Find Results" in view.settings().get('syntax')

  # On first load check for setting initialization
  def check_init(self, view):
    if s.get("stamps") == None:
      view.run_command( "refresh" )

  # If the queue is empty, call the highlighter. Otherwise wait for queue to clear
  def queue_highlighter(self, view):
    # Decrement queue
    self.queue -= 1
    # If nothing queued, do some work
    if self.queue == 0:
      view.run_command( "live_stamps_highlight" )


  #-- Events ----------------------------------------------------------------------------


  # Launch the highlighter on view load, if enabled
  def on_load(self, view):
    view.run_command( "live_stamps_highlight" )
    view.run_command( "refresh" )

  # Listen for save event
  def on_pre_save(self, view):

    # Check settings init
    self.check_init(view)

    if s.get("auto_update"):
      view.run_command( "live_stamps_update" )

  # When the view is changed, queue the highlighter and set the timeout
  def on_modified(self, view):

    # Check settings init
    self.check_init(view)

    # Increment queue
    self.queue += 1

    # Queue asynchronous worker thread
    sublime.set_timeout_async(lambda: self.queue_highlighter(view), s.get("timeout", 200))

  # Launch the highlighter on view activation
  def on_activated_async(self, view):
    view.run_command( "live_stamps_highlight" )

