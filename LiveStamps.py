import sublime, time, sublime_plugin, getpass, hashlib, re, ntpath, os, sys
from datetime import datetime, timedelta
from calendar import monthrange

# Global settings, meta and timezones vars
s = sublime.load_settings("LiveStamps.sublime-settings")
z = sublime.load_settings("TimeZones.sublime-settings")
m = s.get("stamps")

class LiveStampsMenuGenCommand(sublime_plugin.TextCommand):
	'''
		Auto builds ST3 menu arrays to easily update livestamp definitions
	'''
	def run(self, edit, menutype="context"):

		global m
		self.view.run_command('refresh_meta')

		self.sortedKeys = sorted(m.keys())

		# figure out which type of menu is being generated
		if menutype == "context":
			menutype = self.get_context_menu()
		elif menutype == "toolbar":
			menutype = self.get_toolbar_menu()
		elif menutype == "sidebar":
			menutype = self.get_sidebar_menu()
		elif menutype == "command":
			menutype = self.get_command_menu()

		# Insert the menu into the document
		for pos in self.view.sel():

			# Insert at each cursor location
			if pos.empty():
				self.view.insert(edit, pos.a, menutype)

			# Replace selected area(s) with menu
			else:
				self.view.replace(edit, pos, menutype)

	# Add header to a set of keys, making a submenu
	def add_header(self, menustring, caption = "Submenu", identifier = False):

		# A highlevel menu, requiring an ID
		if identifier:
			result = """
				{
					"caption"   : "%s",
					"id"        : "%s",
					"children"  :
					[""" % (caption, identifier)

		# Just a submenu
		else:
			result = """
				{
					"caption"   : "%s",
					"children"  :
					[""" % (caption)

		# Concatenate and close the submenu
		return result + menustring + """
					]
				},"""

	# Add menu separator
	def add_divider(self):
		return"""
					{
						"caption" : "-"
					},"""

	# Build menu keys for all currently defined stamps
	def get_stamp_keys(self, header = "Insert Stamp", captiontag = ""):

		result = """
					{
						"caption" : "All Stamps",
						"command" : "insert_stamp",
						"args"    : {"kind": "all"},
					},"""

		for stamp in self.sortedKeys:
			result += """
					{
						"caption" : "%s",
						"command" : "insert_stamp",
						"args"    : {"kind": "%s"},
					},""" % (stamp.title().replace("_", " ") + captiontag, stamp)

		if header:
			result = self.add_header(result, header)

		return result

	# Build menu keys for all currently defined values
	def get_value_keys(self, header = "Insert Value", captiontag = ""):

		result = """
					{
						"caption" : "All Values",
						"command" : "insert_stamp",
						"args"    : {"stamptype": "value", "kind": "all"},
					},"""

		for stamp in self.sortedKeys:
			result += """
					{
						"caption" : "%s",
						"command" : "insert_stamp",
						"args"    : {"stamptype": "value", "kind": "%s"},
					},""" % (stamp.title().replace("_", " ") + captiontag, stamp)

		if header:
			result = self.add_header(result, header)

		return result

	# Build menu keys for highlighting options
	def get_hilite_keys(self, header = "Highlighting"):

		result = """
					{
						"caption" : "ON/OFF",
						"command" : "live_stamps_toggle",
						"args"    : {"mode": "highlighter"},
					},
					{
						"caption" : "Outline",
						"command" : "live_stamps_toggle",
						"args"    : {"mode": "outline"},
					},
					{
						"caption" : "Markers",
						"command" : "live_stamps_toggle",
						"args"    : {"mode": "markers"},
					},
					{
						"caption" : "Background",
						"command" : "live_stamps_toggle",
						"args"    : {"mode": "shading"},
					},"""

		if header:
			result = self.add_header(result, header)

		return result

	# Build menu keys for menu generation
	def get_menugen_keys(self, header = "Menu Gen"):

		result = """
					{
						"caption" : "Context Menu",
						"command" : "live_stamps_menu_gen",
						"args"    : {"menutype": "context"},
					},
					{
						"caption" : "Toolbar Menu",
						"command" : "live_stamps_menu_gen",
						"args"    : {"menutype": "toolbar"},
					},
					{
						"caption" : "Sidebar Menu",
						"command" : "live_stamps_menu_gen",
						"args"    : {"menutype": "sidebar"},
					},
					{
						"caption" : "Command Menu",
						"command" : "live_stamps_menu_gen",
						"args"    : {"menutype": "command"},
					},"""

		if header:
			result = self.add_header(result, header)

		return result

	# Build menu keys for plugin options
	def get_plugin_keys(self, header = False):

		result = """
					{
						"caption" : "Update Now",
						"command" : "update_stamps",
					},
					{
						"caption" : "Update On Save",
						"command" : "live_stamps_toggle",
						"args"    : {"mode": "auto_update"},
					},"""

		if header:
			result = self.add_header(result, header)

		return result

	# Build menu keys for plugin preferences
	def get_pref_keys(self, header = "Preferences"):

		result = """
					{
						"caption" : "Time Zones",
						"command" : "open_file",
						"args"    : {"file":"${packages}/LiveStamps/TimeZones.sublime-settings"}
					},
					{
						"caption" : "-"
					},
					{
						"caption" : "Settings – Default",
						"command" : "open_file",
						"args"    : {"file":"${packages}/LiveStamps/LiveStamps.sublime-settings"}
					},
					{
						"caption" : "Settings – User",
						"command" : "open_file",
						"args"    : {"file":"${packages}/User/LiveStamps.sublime-settings"}
					},
					{
						"caption" : "-"
					},"""

		for platform in ['Windows', 'OSX', 'Linux']:
			result +="""
					{
						"caption" : "Key Bindings – Default",
						"command" : "open_file",
						"args"    : {"file":"${packages}/LiveStamps/Default (%s).sublime-keymap", "platform":"%s"}
					},
					{
						"caption" : "Key Bindings – Default",
						"command" : "open_file",
						"args"    : {"file":"${packages}/User/Default (%s).sublime-keymap",  "platform":"%s"},
					},"""  % (platform, platform, platform, platform)

		if header:
			result = self.add_header(result, header)

		return result

	# Build menu keys for command pallate
	def get_command_menu(self):

		result ="""
				["""

		result += self.get_stamp_keys(False, " Stamp")
		result += self.get_value_keys(False, " Value")
		result += self.get_hilite_keys(False)
		result += self.get_menugen_keys(False)
		result += self.get_pref_keys(False)
		result += self.get_plugin_keys(False)

		result += """
				]"""

		return re.sub('caption\" : "','caption\" : "LiveStamps: ', result)

	# Build menu keys for context menu
	def get_context_menu(self):

		result ="""
			[
			{
				"caption"   : "LiveStamps",
				"id"        : "timestamps-context-menu",
				"children"  :
				["""

		result += self.get_stamp_keys()
		result += self.get_value_keys()
		result += self.get_hilite_keys()
		#result += self.get_menugen_keys()
		#result += self.get_pref_keys()
		result += self.add_divider()
		result += self.get_plugin_keys()

		result += """
				]
			}
			]"""

		return result

	# Build menu keys for toolbar menu
	def get_toolbar_menu(self):

		result = """
			[
			{
			"id"       : "tools",
			"children" :
			[
			{
				"caption"   : "LiveStamps",
				"id"        : "livestamps-tools-menu",
				"children"  :
				["""

		result += self.get_stamp_keys()
		result += self.get_value_keys()
		result += self.get_hilite_keys()

		result += self.add_divider()
		result += self.get_plugin_keys()

		result += """
				]
			}
			]
			},
			{
			"id"       : "preferences",
			"children" :
			[
			{
				"caption"  : "Package Settings",
				"mnemonic" : "P",
				"id"       : "package-settings",
				"children" :
				[
				{
					"caption"  : "LiveStamps",
					"id"       : "livestamps-preferences-menu",
					"children" :
					["""
		result += self.get_menugen_keys()
		result += self.add_divider()
		result += self.get_pref_keys(False)

		return result + """
					]
				}
				]
			}
			]
		}
		]"""

	# Build menu keys for sidebar menu
	def get_sidebar_menu(self):
		result ="""
			[
			{
				"caption"   : "LiveStamps",
				"id"        : "timestamps-sidebar-menu",
				"children"  :
				["""

		result += self.get_stamp_keys()
		result += self.get_value_keys()
		result += self.get_hilite_keys()
		result += self.get_menugen_keys()
		result += self.get_pref_keys()
		result += self.add_divider()
		result += self.get_plugin_keys()

		result += """
				]
			}
			]"""

		return result

class RefreshMetaCommand(sublime_plugin.TextCommand):
	'''
		Refreshes and builds the metadata for each stamp
	'''
	def run(self, view):
		# Update our global variables
		global s
		global m
		global z

		# Refresh settings, stamp and timezone metadata
		s = sublime.load_settings("LiveStamps.sublime-settings")
		z = sublime.load_settings("TimeZones.sublime-settings")
		m = s.get("stamps")

		# Try to find the filepath for the file
		self.path = self.view.file_name()

		# Store the files contents for checksum later
		self.data = self.view.substr(sublime.Region(0, self.view.size()))

		# Grab file, user and checksum data
		self.info = {
			"user"        : getpass.getuser(),
			"checksum"    : self.md5hash(),
			"extension"   : self.get_file("extension", self.path),
			"base_name"   : self.get_file("base_name", self.path),
			"file_name"   : self.get_file("file_name", self.path),
			"file_path"   : self.get_file("file_path", self.path),
			"parent_name" : self.get_file("parent_name", self.path),
			"parent_path" : self.get_file("parent_path", self.path),
		}

		# Build stamp meta
		self.get_meta()


	# Helper function to generate md5 checksum of the file contents
	def md5hash(self):
		# Remove existing checksums from contents and recalculate
		cleanh = re.sub(m["checksum"]['regex'], '', self.data)
		# Convert string to bytes
		encode = cleanh.encode(encoding='UTF-8')
		# Generate a hash of the document
		return hashlib.md5(encode).hexdigest()

	# Helper function to grab file and path meta
	def get_file(self, prop="file_name", filepath=os.getcwd()):

		# If file is currently unsaved and has no path
		if filepath == None:
			return "unknown"

		# Something was passed, so try to get the basename and extension
		else:
			(basename, ext) = os.path.splitext(filepath)

			# Current filename with extension
			if prop == "file_name":
				return os.path.basename(filepath)

			# Current filepath
			elif prop == "file_path":
				return filepath

			# Current file extension
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

	# Helper function to grab current time
	def time_stamp(self):

		# Load defined timezone
		timezone = z.get(s.get("timezone", 0))

		# DST check
		if s.get("daylight"):
			timezone = timezone + 1

		# Get current UTC time
		time = datetime.utcnow()

		# Check it's valid.
		if s.get("utc_time", True):
			if timezone < 0:
				time = time - timedelta(hours=timezone * -1)
			else:
				time = time + timedelta(hours=timezone)

		# Return the current time with offset
		return time

	# Helper function to get a time offset
	def time_offset(self, value = "auto"):

		time = self.time_stamp()

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

				# Cool one liner cast... but not safe!
				# offset = dict(items.split("=") for items in value)

			# Apply each offset to the current time
			if "microseconds" in offset:
				time += timedelta(microseconds = float(offset["microseconds"]))
			if "milliseconds" in offset:
				time += timedelta(milliseconds = float(offset["milliseconds"]))
			if "seconds" in offset:
				time += timedelta(seconds      = float(offset["seconds"]))
			if "minutes" in offset:
				time += timedelta(minutes      = float(offset["minutes"]))
			if "hours" in offset:
				time += timedelta(hours        = float(offset["hours"]))
			if "days" in offset:
				time += timedelta(days         = float(offset["days"]))
			if "weeks" in offset:
				time += timedelta(weeks        = float(offset["weeks"]))
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
				time += timedelta(days = days)

			if "years" in offset:

				# Get current year
				year = datetime.today().year

				# Check for leap year
				year = 366 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 365

				# Convert years to days
				days = float(offset["years"]) * year

				# Add the offset
				time += timedelta(days = days)

		return time

	# Get the true value of a stamp, recursively for multipart stamps
	def truevalues(self, stamp, convert = False):

		if stamp in self.info:
			stamp = self.info[stamp]
		elif stamp in m:
			if "strft" in m[stamp]:
				time = self.time_offset(m[stamp]["value"])
				stamp = time.strftime(m[stamp]["strft"])
			else:
				stamp = m[stamp]["value"]

		if isinstance(stamp, list):
			values = []
			for part in stamp:
				values.append( self.truevalues(part, convert))

			return values

		return stamp

	# Build and format final stamp and value output strings
	def get_meta(self):

		for stamp, info in m.items():

			# Check stamp is OK
			if 'value' not in info:
				m[stamp]['value'] = "LiveStamps: Stamp '" + stamp + "' has no value defined"
			if 'stamp' not in info:
				m[stamp]['stamp'] = "{0}"

			truevalues = self.truevalues(stamp)

			if isinstance(truevalues, list):
				i = 0
				for part in m[stamp]['value']:
					if part in m:
						truepart = truevalues[i]
						injector = m[part]['stamp'] if "stamp" in m[part] else '{0}'
						if isinstance(truepart, list):
							truevalues[i] = injector.format(*truepart)
						else:
							truevalues[i] = injector.format(truepart)

					i += 1


				m[stamp]['final_stamp'] = m[stamp]['stamp'].format(*truevalues)
				m[stamp]['final_value'] = " ".join(str(x) for x in truevalues)
			else:
				m[stamp]['final_stamp'] = m[stamp]['stamp'].format(truevalues)
				m[stamp]['final_value'] = truevalues

	def pretty2(self, stamp):

		if '@' in stamp:
			idx = stamp.index('@')
			first = -1;

			for i, space in enumerate(stamp):
				if space == " " and i > idx:
					maxlength = len(max(m.keys(), key=len)) + 2
					formatter = "{0:<"+ str(maxlength) +"s}{1}"
					left  = stamp[:i].strip()
					right = stamp[i:].strip()
					return formatter.format(left, right)

		return stamp

	def pretty(self, stamp, values):

		val = m[stamp]['stamp']
		idx = val.index('{')

		maxlength = len(max(m.keys(), key=len)) + 2
		formatter = "{0:<"+ str(maxlength) +"s}{1}"


		left  = val[:idx].strip()
		right = val[idx:]
		val = formatter.format(left, right)

		print (val)

		return val.format(*values)

class StampInserterCommand(sublime_plugin.TextCommand):
	'''
		Injects a stamp, which will auto update according to its regex pattern in the document
	'''
	def run(self, edit, kind):

		# Final output string
		result = ""

		# Inject all values at once, alphabetically
		if kind == "all":

			# Sort stamps alphabetically
			sortedKeys = sorted(m.keys())

			# Build the output string piece by piece
			for name in sortedKeys:
				result += m[name]["final_stamp"] + "\n"


		# Inject a single stamp
		else:
			result += m[kind]["final_stamp"] + "\n"

		# Insert the stamp(s) into the document
		for pos in self.view.sel():

			# Insert at each cursor location
			if pos.empty():
				self.view.insert(edit, pos.a, result)

			# Replace selected area(s) with stamp
			else:
				self.view.replace(edit, pos, result)

class ValueInserterCommand(sublime_plugin.TextCommand):
	'''
		Injects the raw value of a stamp
	'''
	def run(self, edit, kind):

		# Final output string
		result = ""

		# Inject all values at once, alphabetically
		if kind == "all":
			# Sort stamps alphabetically
			sortedKeys = sorted(m.keys())

			# Get the length of the longest key
			maxlength = len(max(sortedKeys, key=len))
			formatter = "{0:<"+ str(maxlength) +"s} : {1}\n"

			print (maxlength)
			# Concatenate all stamps and format
			for name in sortedKeys:
				# Build the output string piece by piece
				details = m[name]["final_value"]
				# Mimic PHP sprintf for neat output
				result += formatter.format(name, details)

		# Inject a single stamp
		else:
			result = m[kind]["final_value"]

		# Insert the stamp(s) into the document
		for pos in self.view.sel():

			# Insert at each cursor location
			if pos.empty():
				self.view.insert(edit, pos.a, result)

			# Replace selected area(s) with stamp
			else:
				self.view.replace(edit, pos, result)

class InsertStampCommand(sublime_plugin.TextCommand):
	'''
		Wrapper class to inject a stamp or a value with a single command, depending on argument
	'''
	def run(self, view, kind="time", stamptype="stamp"):

		# Grab fresh file, user, document and checksum meta
		self.view.run_command('refresh_meta')

		# Inject a stamp
		if stamptype == "stamp":
			self.view.run_command('stamp_inserter', {'kind': kind})

		# Inject a value
		else:
			self.view.run_command('value_inserter', {'kind': kind})

class UpdateStampsCommand(sublime_plugin.TextCommand):
	'''
		Update all stamps in the current document
	'''
	def run(self, edit):

		# Grab fresh file, user, document and checksum meta
		self.view.run_command('refresh_meta')

		# Update any stamp, except those in a sublime settings file
		if "sublime-settings" not in m["extension"]["final_stamp"]:
			for k, v in m.items():

				# Check if a regex is supplied
				if 'regex' in v:
					regex = v['regex']

					# Check regex is not a complete wildcard
					if regex != "":

						# Find each stamp and replace
						for region in self.view.find_all(regex, 0):
							self.view.replace(edit, region, v['final_stamp'])

class HighlightStampsCommand(sublime_plugin.TextCommand):
	'''
		Enables or disables various stamp highlighting modes:

			shading - Highlights the stamp background
			outline - Underlines the stamp
			markers - Adds markers in the gutter on lines where a stmap is present
	'''
	def run(self, view, clear=False):

		# Enable highlighting
		if s.get("highlighter") and self.view.size() <= s.get("maxsize"):

			# Find highlighting regions
			self.regions = self.find_stamps(m)
			self.scoping = s.get("scoping")

			# Logic gauntlet to ensure refresh after a mode is enabled/disabled
			if s.get("shading"):
				self.shading()
			else:
				self.view.erase_regions("StampHighlighterShading")

			if s.get("outline"):
				self.outline()
			else:
				self.view.erase_regions("StampHighlighterOutline")

			if s.get("markers"):
				self.markers()
			else:
				self.view.erase_regions("StampHighlighterMarkers")

		# Disable highlighting
		else:
			self.view.erase_regions("StampHighlighterShading")
			self.view.erase_regions("StampHighlighterOutline")
			self.view.erase_regions("StampHighlighterMarkers")

	# Get all matching stamp patterns
	def find_stamps(self, stamps):
		result = [];
		for k, v in stamps.items():
			if 'regex' in v:
				matches = self.view.find_all(v['regex'], 0)
				for items in matches:
					result.append(items)

		return result

	# Enable background highlighting
	def shading(self):
		self.view.add_regions(
			'StampHighlighterShading',
			self.regions,
			self.scoping,
			"",
			sublime.DRAW_EMPTY
		)

	# Enable outline/underline
	def outline(self):
		self.view.add_regions(
			'StampHighlighterOutline',
			self.regions,
			self.scoping,
			"",
			sublime.DRAW_NO_FILL
		)

	# Enable gutter markers
	def markers(self):
		self.view.add_regions(
			'StampHighlighterMarkers',
			self.regions,
			self.scoping,
			"dot",
			sublime.DRAW_STIPPLED_UNDERLINE | sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE
		)

class LiveStampsToggleCommand(sublime_plugin.TextCommand):
	'''
		Toggles a LiveStamps setting through the UI
	'''
	def run(self, edit, mode):

		# Get current State and toggle it
		state = False if s.get(mode) == True else True

		# Save settings
		s.set(mode, state)
		sublime.save_settings("LiveStamps.sublime-settings")

		# Change to state to semantic output
		state = "ON" if state else "OFF"

		# Refresh highlighter
		self.view.run_command('highlight_stamps', {'clear': True})
		self.view.run_command('highlight_stamps')

		# Build a status message
		msg = "LiveStamps: Set " + mode + " " + state

		# Inform the user of the state change, via status bar and console
		print (msg)
		sublime.status_message(msg)

class LiveStampsUpdateListener(sublime_plugin.EventListener):
	'''
		Event listener for auto updating stamps
	'''
	def __init__(self):
		# Initialize queue tracker
		self.queue = 0

	# Listen for save event
	def on_pre_save(self, view):
		if s.get("auto_update"):
			view.run_command('update_stamps')

	# When the view is changed, queue the highlighter and set the timeout
	def on_modified(self, view):
		# Increment queue
		self.queue += 1
		# Queue asynchronous worker thread
		sublime.set_timeout_async(lambda: self.queue_highlighter(view), s.get("timeout"))

	# If the queue is empty, call the highlighter. Otherwise wait for queue to clear
	def queue_highlighter(self, view):
		# Decrement queue
		self.queue -= 1
		# If nothing queued, do some work
		if self.queue == 0:
			view.run_command('highlight_stamps')

	# Launch the highlighter on activation, if enabled
	def on_activated(self, view):
		if s.get("highlighter"):
			view.run_command('highlight_stamps')

	# Launch the highlighter on load, if enabled
	def on_load(self, view):
		if s.get("highlighter"):
			view.run_command('highlight_stamps')

	# Determine if the view is a find results view.
	def is_find_results(view):
		return view.settings().get('syntax') and "Find Results" in view.settings().get('syntax')
