import sublime, time, sublime_plugin, getpass, hashlib, re, ntpath, os, sys
from datetime import datetime, timedelta

# Global settings, meta and timezones vars
s = sublime.load_settings("LiveStamps.sublime-settings")
z = sublime.load_settings("TimeZones.sublime-settings")
m = s.get("stamps")

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

	# Helper function to make sure user defined stamps are well written
	def check(self, stamp):
		if 'value' not in m[stamp]:
			m[stamp]['value'] = "LiveStamps: Stamp must have a 'value' key defined"
		if 'stamp' not in m[stamp]:
			m[stamp]['stamp'] = "LiveStamps: Stamp must have a 'stamp' key defined"

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

		if filepath == None:
			# If file is unsaved, or it has no path
			return "unknown"
		else:
			# Get the basename and extension
			(basename, ext) = os.path.splitext(filepath)

			if prop == "file_name":
				# Current filename with extension
				return os.path.basename(filepath)
			elif prop == "file_path":
				# Current filepath
				return filepath
			elif prop == "extension":
				# Current file extension
				return ext.strip('.')
			elif prop == "base_name":
				# Basename of the current file
				return basename
			elif prop == "parent_name":
				# Parent folder's name
				return os.path.split(os.path.dirname(filepath))[1]
			elif prop == "parent_path":
				# Parent folder's path, nothing if unsaved file
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
		if s.get("utc_time", True):
			if timezone < 0:
				time = time - timedelta(hours=timezone * -1)
			else:
				time = time + timedelta(hours=timezone)
		return time

	# Helper function to grab/format values for time, date file and checksum
	def auto_value(self, stamp):

		# Get user defined stamp value
		value = m[stamp]["value"]

		# If a user specific format string has been specified, i.e. octal etc
		if "format" in m[stamp]:
			# Apply user defined formatting
			return value.format(m[stamp]["format"])

		# If a user specific time format string has been specified, i.e. "%d-%m-%Y"
		elif "strft" in m[stamp]:
			# Grab current timestamp or use explicit
			time = self.time_stamp() if value == "auto" else value
			# Return formatted time string
			return time.strftime(m[stamp]["strft"])

		# Otherwise check for file, hash or user metadata or at worst, use the raw defined value
		return self.info[stamp] if (value == 'auto' and stamp in self.info) else value

	# Build and format final stamp and value output strings
	def get_meta(self):

		for stamp, info in m.items():
			# Check stamp is OK
			self.check(stamp)
			# List of values used to format final stamp output
			values = []
			# String used to format final value output
			result = ""
			# Counter for final value position (in the format string)
			index  = 0

			if "parts" not in info:
				# If the stamp only has one part
				values.append( self.auto_value(stamp) )
				result = "{0}"

			else:
				# Else, the stamp has multiple parts get each value
				for piece in info['parts']:
					# Increment our indx/formatting string
					result += "{"+str(index)+"} "
					index  += 1

					if piece in m:
						# If the piece is another stamp, format accordingly.
						values.append( self.auto_value(piece) )
					else:
						# It's not a stamp, just a raw value.
						values.append( piece )

			# Finally, inject each stamp piece using format() and store the final_stamp, and final_value
			m[stamp]['final_stamp'] = info['stamp'].format(*values)
			m[stamp]['final_value'] = result.format(*values)

class StampInserterCommand(sublime_plugin.TextCommand):
	'''
		Injects a stamp, which will auto update according to its regex pattern in the document
	'''
	def run(self, edit, kind):

		# Final output string
		result = ""

		# Build the output String
		if kind == "all":
			# Inject all values at once, alphabetically
			sortedKeys = sorted(m.keys())
			# Concatenate all stamps and format
			for name in sortedKeys:
				# Build the output string piece by piece
				result += m[name]["final_stamp"]
				# Newline at end of each stamp
				result += "\n"
		else:
			# Inject a single stamp
			result += m[kind]["final_stamp"]

		for pos in self.view.sel():
			# Insert the stamp(s) into the document
			if pos.empty():
				# Insert at each cursor location
				self.view.insert(edit, pos.a, result)
			else:
				# Replace selected area(s) with stamp
				self.view.replace(edit, pos, result)

class ValueInserterCommand(sublime_plugin.TextCommand):
	'''
		Injects the raw value of a stamp
	'''
	def run(self, edit, kind):

		# Final output string
		result = ""

		if kind == "all":
			# Inject all values at once, alphabetically
			sortedKeys = sorted(m.keys())
			# Concatenate all stamps and format
			for name in sortedKeys:
				# Build the output string piece by piece
				details = m[name]["final_value"]
				# Mimic PHP sprintf for neat output
				result += "{0:<12s} : {1}\n".format(name, details)
		else:
			# Inject a single stamp
			result = m[kind]["final_value"]

		for pos in self.view.sel():
			# Insert the stamp(s) into the document
			if pos.empty():
				# Insert at each cursor location
				self.view.insert(edit, pos.a, result)
			else:
				# Replace selected area(s) with stamp
				self.view.replace(edit, pos, result)

class InsertStampCommand(sublime_plugin.TextCommand):
	'''
		Wrapper class to inject a stamp or a value with a single command, depending on argument
	'''
	def run(self, view, kind="time", stamptype="stamp"):

		# Grab fresh file, user, document and checksum meta
		self.view.run_command('refresh_meta')

		if stamptype == "stamp":
			# Inject a stamp
			self.view.run_command('stamp_inserter', {'kind': kind})
		else:
			# Inject a value
			self.view.run_command('value_inserter', {'kind': kind})

class UpdateStampsCommand(sublime_plugin.TextCommand):
	'''
		Update all stamps in the current document
	'''
	def run(self, edit):

		# Grab fresh file, user, document and checksum meta
		self.view.run_command('refresh_meta')

		if "sublime-settings" not in m["extension"]["final_stamp"]:
			# Update any stamp, except those in a sublime settings file
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

		if s.get("highlighter") and self.view.size() <= s.get("maxsize"):
			# Enable highlighting
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

		else:
			# Disable highlighting
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

		return (result)

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
		sublime.set_timeout(lambda: self.queue_highlighter(view), s.get("timeout"))

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
