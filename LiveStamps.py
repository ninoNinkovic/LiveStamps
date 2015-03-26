import sublime, time, sublime_plugin, getpass, hashlib, re, ntpath, os, sys, json
from datetime import datetime, timedelta
from collections import OrderedDict

# Global settings
s = sublime.load_settings("LiveStamps.sublime-settings")

# Global stamp metadata
m = s.get("stamps")

class NotifyCommand(sublime_plugin.TextCommand):
	'''
	*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
	* Shows a Sublime message in the console, statusbar, or error and dialog popups.
	*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
	'''
	def run(self, view, message, modes="console status"):

		global s

		# Check init and grab fresh meta if needed
		if s.get("console_events") == None:
			self.view.run_command('refresh_meta')

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

class RefreshMetaCommand(sublime_plugin.TextCommand):
	'''
	*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
	* Build Metadata For LiveStamps & Magic Values
	*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
	'''

	def run(self, view):
		# Update our global variables
		global s
		global m

		# Load user settings, initialize metadata dictionary
		s = sublime.load_settings("LiveStamps.sublime-settings")
		m = s.get("stamps")

		# Get current filepath and contents from view
		self.path = self.view.file_name()
		self.data = self.view.substr(sublime.Region(0, self.view.size()))

		# Get master timezone dictionary
		self.timezones = self.get_time_zones()

		# Build 'magic values'
		self.magic_values()

		# Get docblock stamp alignement
		self.docalign = self.get_docalign()
		self.maxwidth = len(max(m.keys(), key=len))

		# Let er rip... parse final stamp metadata
		self.get_meta()
		#self.dump_meta()

	def dump_meta(self):

		sortedKeys = sorted(m.keys())

		for stamp in sortedKeys:
			print ("\n" + stamp.upper() +"\n------------------------------")
			for name, value in m[stamp].items():
				layout = "{0:<"+ str(self.maxwidth) +"s} : {1}"
				print(layout.format( name, value ))

	#-------------------------------------------------------------------------------
	# Regex Helpers
	#-------------------------------------------------------------------------------

	# Build the auto stamp pattern
	def stampify(self, stamp, values):

		if isinstance(values, list):
			injection_flags = ""
			i = 0
			for value in values:
				injection_flags += "{" + str(i) + "} "
				i += 1

		else:
			injection_flags = "{0}"

		return s.get("autostamp").format(stamp, injection_flags)

	# Build the auto regex pattern
	def regexify(self, stamp):
		return s.get("autoregex").format(stamp)

		if "tflag" in m[stamp]:
			return self.time_regex(m[stamp]["tflag"])
		else:
			return s.get("autoregex").format(stamp)

	# *** WARNING *** DANGEROUS REGEX PATTERNS IN HERE...NOT READY FOR USE!
	def time_regex(self, regex):
		# Experimental build for auto strftime() patterns.

		swaps = {
			# abbreviated weekday name
			'%a' : "(Mon|Tue|Wed|Thu|Fri|Sat|Sun)",
			# full weekday name
			'%A' : "(Thuday|Thuday|Thusday|Thunesday|Thursday|Thuday|Thuurday)",
			# abbreviated month name
			'%b' : "(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",
			# full month name
			'%B' : "(January|February|March|April|May|June|July|August|September|October|November|December)",
			# preferred date and time representation
			'%c' : "(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\s|\s\s)(\d|\d\d)\s(\d\d:\d\d:\d\d)\s\d\d\d\d",
			# century number (the year divided by 100, range 00 to 99)
			'%C' : "(0-2)(0|1)",
			# day of the month (01 to 31)
			'%d' : "(0-3)(0-9)",
			# same as %m/%d/%y
			'%D' : "(01|02|03|04|05|06|07|08|09|10|11|12)/(01|02|03|04|05|06|07|08|09|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31)/\d\d",
			# day of the month (1 to 31),
			'%e' : "(01|02|03|04|05|06|07|08|09|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31)",
			# like %G, but without the century
			'%g' : "(\d\d)",
			# 4-digit year corresponding to the ISO week number (see %V).
			'%G' : "(0-2)\d\d\d",
			# same as %b
			'%h' : "(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",
			# hour, using a 24-hour clock (00 to 23)
			'%H' : "(0-2)\d",
			# hour, using a 12-hour clock (01 to 12)
			'%I' : "(01|02|03|04|05|06|07|08|09|10|11|12)",
			# day of the year (001 to 366)
			'%j' : "(0-6)(0-6)(0-9)",
			# month (01 to 12)
			'%m' : "(01|02|03|04|05|06|07|08|09|10|11|12)",
			# minute
			'%M' : "((0-5)\d)",
			# newline character
			'%n' : "(\n)",
			# either am or pm according to the given time value
			'%p' : "(AM|PM)",
			# time in a.m. and p.m. notation
			'%r' : "(a.m.|p.m.)",
			# time in 24 hour notation
			'%R' : "(0-2)\d:\d\d)",
			# second
			'%S' : "(0-6)(0-9)",
			# tab character
			'%t' : "(\t)",
			# current time, equal to %H:%M:%S
			'%T' : "(0-2)\d:(0-5)\d:(0-5)\d)",
			# weekday as a number (1 to 7), Monday=1. Warning: In Sun Solaris Sunday=1
			'%u' : "(1-7)",
			# week number of the current year, starting with the first Sunday as the first day of the first week
			'%U' : "(0-5)\d",
			# The ISO 8601 week number of the current year (01 to 53), where week 1 is the first week that has at least 4 days in the current year, and with Monday as the first day of the week
			'%V' : "(0-5)\d",
			# week number of the current year, starting with the first Monday as the first day of the first week
			'%W' : "(0-5)\d",
			# day of the week as a decimal, Sunday=0
			'%w' : "(0-5)",
			# preferred date representation without the time
			'%x' : "(01|02|03|04|05|06|07|08|09|10|11|12)/(01|02|03|04|05|06|07|08|09|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31)/\d\d",
			# preferred time representation without the date
			'%X': "(0-2)\d:(0-5)\d:(0-5)\d)",
			# year without a century (range 00 to 99)
			'%y' : "(\d\d)",
			# year including the century
			'%Y' : "((0-2)\d\d)",
			# UTC offset in the form +HHMM or -HHMM (empty string if the the object is naive).
			'%z' : "",
			# time zone or name or abbreviation
			'%Z' : "(ACDT|ACST|ACT|ADT|AEDT|AEST|AFT|AKDT|AKST|AMST|AMT|ART|AST|AWDT|AWST|AZOST|AZT|BDT|BIOT|BIT|BOT|BRT|BST|BTT|CAT|CCT|CDT|CEDT|CEST|CET|CHADT|CHAST|CHOT|CHST|CHUT|CIST|CIT|CKT|CLST|CLT|COST|COT|CST|CT|CVT|CWST|CXT|DAVT|DDUT|DFT|EASST|EAST|EAT|ECT|EDT|EEDT|EEST|EET|EGST|EGT|EIT|EST|FET|FJT|FKST|FKT|FNT|GALT|GAMT|GET|GFT|GILT|GIT|GMT|GST|GYT|HADT|HAEC|HAST|HKT|HMT|HOVT|HST|ICT|IDT|IOT|IRDT|IRST|IST|IST|JST|KGT|KOST|KRAT|KST|LHST|LINT|MAGT|MART|MAWT|MDT|MET|MEST|MHT|MIST|MIT|MMT|MSK|MST|MUT|MVT|MYT|NCT|NDT|NFT|NPT|NST|NT|NUT|NZDT|NZST|OMST|ORAT|PDT|PET|PETT|PGT|PHOT|PKT|PMDT|PMST|PONT|PST|PYST|PYT|RET|ROTT|SAKT|SAMT|SAST|SBT|SCT|SGT|SLST|SRET|SRT|SST|SYOT|TAHT|THA|TFT|TJT|TKT|TLT|TMT|TOT|TVT|UCT|ULAT|USZ1|UTC|UYST|UYT|UZT|VET|VLAT|VOLT|VOST|VUT|WAKT|WAST|WAT|WEDT|WEST|WET|WIT|WST|YAKT|YEKT|Z)",
			# a literal % character
			'%%' : "(%)",
		}
		for rgx, val in swaps.items():
			regex = re.sub(rgx, val, regex)

		return regex

	#-------------------------------------------------------------------------------
	# Time Helpers
	#-------------------------------------------------------------------------------

	# Get a dictionary of the Olson timezones and offsets
	def get_time_zones(self):
		'''
			This function is not needed for now, but might be of use in the future.

			So why is it here?

			Unfortunatly python is kind of clunky when it comes to time and timezone
			management. There isn't really an easily "portable" library, and the built
			in falls way short.

			Currently the best options are external modules. Pytz of course and one in
			development called Arrow. Arrow is aimed at fixing python time headaches
			problem for but I don't know if it's quite there yet.

			Adding python modules in sublime text adds the following overhead:

				- Renaming all the module import statements and initialization
				- Detecting if plugin is currently compressed and unpacking if so
				- When I got the unpacking working, it left an unclosed thread sometimes
				- Module bloat which is significantly larger than this entire plugin.
				- Even once loaded, pytz/datetime are just a pain vs. other languages.

			Yes, it is absolutely possible, but managing all the above everytime the
			module is updated is not fun.

			Ultimately, if the local system clock is set right, the current solution
			just works.
		'''
		return {
			'Africa/Abidjan'                   : ['+00:00', '+00:00', 'GMT'],
			'Africa/Accra'                     : ['+00:00', '+00:00', 'GMT'],
			'Africa/Addis_Ababa'               : ['+03:00', '+03:00', 'EAT'],
			'Africa/Algiers'                   : ['+01:00', '+01:00', 'CET'],
			'Africa/Asmara'                    : ['+03:00', '+03:00', 'EAT'],
			'Africa/Asmera'                    : ['+03:00', '+03:00', 'EAT'],
			'Africa/Bamako'                    : ['+00:00', '+00:00', 'GMT'],
			'Africa/Bangui'                    : ['+01:00', '+01:00', 'WAT'],
			'Africa/Banjul'                    : ['+00:00', '+00:00', 'GMT'],
			'Africa/Bissau'                    : ['+00:00', '+00:00', 'GMT'],
			'Africa/Blantyre'                  : ['+02:00', '+02:00', 'CAT'],
			'Africa/Brazzaville'               : ['+01:00', '+01:00', 'WAT'],
			'Africa/Bujumbura'                 : ['+02:00', '+02:00', 'CAT'],
			'Africa/Cairo'                     : ['+02:00', '+03:00', 'EET'],
			'Africa/Casablanca'                : ['+00:00', '+01:00', 'WET'],
			'Africa/Ceuta'                     : ['+01:00', '+02:00', 'CET'],
			'Africa/Conakry'                   : ['+00:00', '+00:00', 'GMT'],
			'Africa/Dakar'                     : ['+00:00', '+00:00', 'GMT'],
			'Africa/Dar_es_Salaam'             : ['+03:00', '+03:00', 'EAT'],
			'Africa/Djibouti'                  : ['+03:00', '+03:00', 'EAT'],
			'Africa/Douala'                    : ['+01:00', '+01:00', 'WAT'],
			'Africa/El_Aaiun'                  : ['+00:00', '+01:00', 'WET'],
			'Africa/Freetown'                  : ['+00:00', '+00:00', 'GMT'],
			'Africa/Gaborone'                  : ['+02:00', '+02:00', 'CAT'],
			'Africa/Harare'                    : ['+02:00', '+02:00', 'CAT'],
			'Africa/Johannesburg'              : ['+02:00', '+02:00', 'SAST'],
			'Africa/Juba'                      : ['+03:00', '+03:00', 'EAT'],
			'Africa/Kampala'                   : ['+03:00', '+03:00', 'EAT'],
			'Africa/Khartoum'                  : ['+03:00', '+03:00', 'EAT'],
			'Africa/Kigali'                    : ['+02:00', '+02:00', 'CAT'],
			'Africa/Kinshasa'                  : ['+01:00', '+01:00', 'WAT'],
			'Africa/Lagos'                     : ['+01:00', '+01:00', 'WAT'],
			'Africa/Libreville'                : ['+01:00', '+01:00', 'WAT'],
			'Africa/Lome'                      : ['+00:00', '+00:00', 'GMT'],
			'Africa/Luanda'                    : ['+01:00', '+01:00', 'WAT'],
			'Africa/Lubumbashi'                : ['+02:00', '+02:00', 'CAT'],
			'Africa/Lusaka'                    : ['+02:00', '+02:00', 'CAT'],
			'Africa/Malabo'                    : ['+01:00', '+01:00', 'WAT'],
			'Africa/Maputo'                    : ['+02:00', '+02:00', 'CAT'],
			'Africa/Maseru'                    : ['+02:00', '+02:00', 'SAST'],
			'Africa/Mbabane'                   : ['+02:00', '+02:00', 'SAST'],
			'Africa/Mogadishu'                 : ['+03:00', '+03:00', 'EAT'],
			'Africa/Thurovia'                  : ['+00:00', '+00:00', 'EAT'],
			'Africa/Nairobi'                   : ['+03:00', '+03:00', 'WAT'],
			'Africa/Ndjamena'                  : ['+01:00', '+01:00', 'WAT'],
			'Africa/Niamey'                    : ['+01:00', '+01:00', 'GMT'],
			'Africa/Nouakchott'                : ['+00:00', '+00:00', 'GMT'],
			'Africa/Ouagadougou'               : ['+00:00', '+00:00', 'WAT'],
			'Africa/Porto-Novo'                : ['+01:00', '+01:00', 'GMT'],
			'Africa/Sao_Tome'                  : ['+00:00', '+00:00', 'UTC'],
			'Africa/Timbuktu'                  : ['+00:00', '+00:00', 'GMT'],
			'Africa/Tripoli'                   : ['+01:00', '+02:00', 'EET'],
			'Africa/Tunis'                     : ['+01:00', '+01:00', 'CET'],
			'Africa/Windhoek'                  : ['+01:00', '+02:00', 'WAST'],
			'America/Adak'                     : ['−10:00', '−09:00', 'HADT'],
			'America/Anchorage'                : ['−09:00', '−08:00', 'AKDT'],
			'America/Anguilla'                 : ['−04:00', '−04:00', 'AST'],
			'America/Antigua'                  : ['−04:00', '−04:00', 'AST'],
			'America/Araguaina'                : ['−03:00', '−03:00', 'BRT'],
			'America/Argentina/Buenos_Aires'   : ['−03:00', '−03:00', 'ART'],
			'America/Argentina/Catamarca'      : ['−03:00', '−03:00', 'ART'],
			'America/Argentina/ComodRivadavia' : ['−03:00', '−03:00', 'ART'],
			'America/Argentina/Cordoba'        : ['−03:00', '−03:00', 'ART'],
			'America/Argentina/Jujuy'          : ['−03:00', '−03:00', 'ART'],
			'America/Argentina/La_Rioja'       : ['−03:00', '−03:00', 'ART'],
			'America/Argentina/Mendoza'        : ['−03:00', '−03:00', 'ART'],
			'America/Argentina/Rio_Gallegos'   : ['−03:00', '−03:00', 'ART'],
			'America/Argentina/Salta'          : ['−03:00', '−03:00', 'ART'],
			'America/Argentina/San_Juan'       : ['−03:00', '−03:00', 'ART'],
			'America/Argentina/San_Luis'       : ['−03:00', '−03:00', 'ART'],
			'America/Argentina/Tucuman'        : ['−03:00', '−03:00', 'ART'],
			'America/Argentina/Ushuaia'        : ['−03:00', '−03:00', 'ART'],
			'America/Aruba'                    : ['−04:00', '−04:00', 'AST'],
			'America/Asuncion'                 : ['−04:00', '−03:00', 'PYST'],
			'America/Atikokan'                 : ['−05:00', '−05:00', 'EST'],
			'America/Atka'                     : ['−10:00', '−09:00', 'HADT'],
			'America/Bahia'                    : ['−03:00', '−02:00', 'BRT'],
			'America/Bahia_Banderas'           : ['−06:00', '−05:00', 'CST'],
			'America/Barbados'                 : ['−04:00', '−04:00', 'AST'],
			'America/Belem'                    : ['−03:00', '−03:00', 'BRT'],
			'America/Belize'                   : ['−06:00', '−06:00', 'CST'],
			'America/Blanc-Sablon'             : ['−04:00', '−04:00', 'AST'],
			'America/Boa_Vista'                : ['−04:00', '−04:00', 'AMT'],
			'America/Bogota'                   : ['−05:00', '−05:00', 'COT'],
			'America/Boise'                    : ['−07:00', '−06:00', 'MDT'],
			'America/Buenos_Aires'             : ['−03:00', '−03:00', 'ART'],
			'America/Cambridge_Bay'            : ['−07:00', '−06:00', 'MDT'],
			'America/Campo_Grande'             : ['−04:00', '−03:00', 'AMT'],
			'America/Cancun'                   : ['−06:00', '−05:00', 'CST'],
			'America/Caracas'                  : ['−04:30', '−04:30', 'VET'],
			'America/Catamarca'                : ['−03:00', '−03:00', 'ART'],
			'America/Cayenne'                  : ['−03:00', '−03:00', 'GFT'],
			'America/Cayman'                   : ['−05:00', '−05:00', 'EST'],
			'America/Chicago'                  : ['−06:00', '−05:00', 'CDT'],
			'America/Chihuahua'                : ['−07:00', '−06:00', 'MST'],
			'America/Coral_Harbour'            : ['−05:00', '−05:00', 'EST'],
			'America/Cordoba'                  : ['−03:00', '−03:00', 'ART'],
			'America/Costa_Rica'               : ['−06:00', '−06:00', 'CST'],
			'America/Creston'                  : ['−07:00', '−07:00', 'MST'],
			'America/Cuiaba'                   : ['−04:00', '−03:00', 'AMT'],
			'America/Curacao'                  : ['−04:00', '−04:00', 'AST'],
			'America/Danmarkshavn'             : ['+00:00', '+00:00', 'GMT'],
			'America/Dawson'                   : ['−08:00', '−07:00', 'PDT'],
			'America/Dawson_Creek'             : ['−07:00', '−07:00', 'MST'],
			'America/Denver'                   : ['−07:00', '−06:00', 'MDT'],
			'America/Detroit'                  : ['−05:00', '−04:00', 'EDT'],
			'America/Dominica'                 : ['−04:00', '−04:00', 'AST'],
			'America/Edmonton'                 : ['−07:00', '−06:00', 'MDT'],
			'America/Eirunepe'                 : ['−05:00', '−05:00', 'ACT'],
			'America/El_Salvador'              : ['−06:00', '−06:00', 'CST'],
			'America/Ensenada'                 : ['−08:00', '−07:00', 'PDT'],
			'America/Fort_Wayne'               : ['−05:00', '−04:00', 'EDT'],
			'America/Fortaleza'                : ['−03:00', '−03:00', 'BRT'],
			'America/Glace_Bay'                : ['−04:00', '−03:00', 'ADT'],
			'America/Godthab'                  : ['−03:00', '−02:00', 'WGT'],
			'America/Goose_Bay'                : ['−04:00', '−03:00', 'ADT'],
			'America/Grand_Turk'               : ['−05:00', '−04:00', 'EDT'],
			'America/Grenada'                  : ['−04:00', '−04:00', 'AST'],
			'America/Guadeloupe'               : ['−04:00', '−04:00', 'AST'],
			'America/Guatemala'                : ['−06:00', '−06:00', 'CST'],
			'America/Guayaquil'                : ['−05:00', '−05:00', 'ECT'],
			'America/Guyana'                   : ['−04:00', '−04:00', 'GYT'],
			'America/Halifax'                  : ['−04:00', '−03:00', 'ADT'],
			'America/Havana'                   : ['−05:00', '−04:00', 'CDT'],
			'America/Hermosillo'               : ['−07:00', '−07:00', 'MST'],
			'America/Indiana/Indianapolis'     : ['−05:00', '−04:00', 'EDT'],
			'America/Indiana/Knox'             : ['−06:00', '−05:00', 'CDT'],
			'America/Indiana/Marengo'          : ['−05:00', '−04:00', 'EDT'],
			'America/Indiana/Petersburg'       : ['−05:00', '−04:00', 'EDT'],
			'America/Indiana/Tell_City'        : ['−06:00', '−05:00', 'CDT'],
			'America/Indiana/Valparaiso'       : ['−06:00', '−05:00', 'UTC'],
			'America/Indiana/Vevay'            : ['−05:00', '−04:00', 'EDT'],
			'America/Indiana/Vincennes'        : ['−05:00', '−04:00', 'EDT'],
			'America/Indiana/Winamac'          : ['−05:00', '−04:00', 'EDT'],
			'America/Indianapolis'             : ['−05:00', '−04:00', 'EDT'],
			'America/Inuvik'                   : ['−07:00', '−06:00', 'MDT'],
			'America/Iqaluit'                  : ['−05:00', '−04:00', 'EDT'],
			'America/Jamaica'                  : ['−05:00', '−05:00', 'EST'],
			'America/Jujuy'                    : ['−03:00', '−03:00', 'ART'],
			'America/Juneau'                   : ['−09:00', '−08:00', 'AKDT'],
			'America/Kentucky/Louisville'      : ['−05:00', '−04:00', 'EDT'],
			'America/Kentucky/Thuticello'      : ['−05:00', '−04:00', 'UTC'],
			'America/Knox_IN'                  : ['−06:00', '−05:00', 'CDT'],
			'America/Kralendijk'               : ['−04:00', '−04:00', 'AST'],
			'America/La_Paz'                   : ['−04:00', '−04:00', 'BOT'],
			'America/Lima'                     : ['−05:00', '−05:00', 'PET'],
			'America/Los_Angeles'              : ['−08:00', '−07:00', 'PDT'],
			'America/Louisville'               : ['−05:00', '−04:00', 'EDT'],
			'America/Lower_Princes'            : ['−04:00', '−04:00', 'AST'],
			'America/Maceio'                   : ['−03:00', '−03:00', 'BRT'],
			'America/Managua'                  : ['−06:00', '−06:00', 'CST'],
			'America/Manaus'                   : ['−04:00', '−04:00', 'AMT'],
			'America/Marigot'                  : ['−04:00', '−04:00', 'AST'],
			'America/Martinique'               : ['−04:00', '−04:00', 'AST'],
			'America/Matamoros'                : ['−06:00', '−05:00', 'CDT'],
			'America/Mazatlan'                 : ['−07:00', '−06:00', 'MST'],
			'America/Mendoza'                  : ['−03:00', '−03:00', 'ART'],
			'America/Menominee'                : ['−06:00', '−05:00', 'CDT'],
			'America/Merida'                   : ['−06:00', '−05:00', 'CST'],
			'America/Metlakatla'               : ['−08:00', '−08:00', 'PST'],
			'America/Mexico_City'              : ['−06:00', '−05:00', 'CST'],
			'America/Miquelon'                 : ['−03:00', '−02:00', 'PMDT'],
			'America/Thucton'                  : ['−04:00', '−03:00', 'EDT'],
			'America/Thuterrey'                : ['−06:00', '−05:00', 'EDT'],
			'America/Thutevideo'               : ['−03:00', '−02:00', 'EDT'],
			'America/Thutreal'                 : ['−05:00', '−04:00', 'AKDT'],
			'America/Thutserrat'               : ['−04:00', '−04:00', 'FNT'],
			'America/Nassau'                   : ['−05:00', '−04:00', 'CDT'],
			'America/New_York'                 : ['−05:00', '−04:00', 'CDT'],
			'America/Nipigon'                  : ['−05:00', '−04:00', 'CDT'],
			'America/Nome'                     : ['−09:00', '−08:00', 'MDT'],
			'America/Noronha'                  : ['−02:00', '−02:00', 'EST'],
			'America/North_Dakota/Beulah'      : ['−06:00', '−05:00', 'EDT'],
			'America/North_Dakota/Center'      : ['−06:00', '−05:00', 'SRT'],
			'America/North_Dakota/New_Salem'   : ['−06:00', '−05:00', 'MST'],
			'America/Ojinaga'                  : ['−07:00', '−06:00', 'EDT'],
			'America/Panama'                   : ['−05:00', '−05:00', 'AST'],
			'America/Pangnirtung'              : ['−05:00', '−04:00', 'ACT'],
			'America/Paramaribo'               : ['−03:00', '−03:00', 'AMT'],
			'America/Phoenix'                  : ['−07:00', '−07:00', 'AST'],
			'America/Port_of_Spain'            : ['−04:00', '−04:00', 'CDT'],
			'America/Port-au-Prince'           : ['−05:00', '−04:00', 'CDT'],
			'America/Porto_Acre'               : ['−05:00', '−05:00', 'BRT'],
			'America/Porto_Velho'              : ['−04:00', '−04:00', 'CST'],
			'America/Puerto_Rico'              : ['−04:00', '−04:00', 'CDT'],
			'America/Rainy_River'              : ['−06:00', '−05:00', 'ACT'],
			'America/Rankin_Inlet'             : ['−06:00', '−05:00', 'ART'],
			'America/Recife'                   : ['−03:00', '−03:00', 'PST'],
			'America/Regina'                   : ['−06:00', '−06:00', 'BRT'],
			'America/Resolute'                 : ['−06:00', '−05:00', 'CLST'],
			'America/Rio_Branco'               : ['−05:00', '−05:00', 'AST'],
			'America/Rosario'                  : ['−03:00', '−03:00', 'BRT'],
			'America/Santa_Isabel'             : ['−08:00', '−07:00', 'EGT'],
			'America/Santarem'                 : ['−03:00', '−03:00', 'MDT'],
			'America/Santiago'                 : ['−04:00', '−03:00', 'AKDT'],
			'America/Santo_Domingo'            : ['−04:00', '−04:00', 'AST'],
			'America/Sao_Paulo'                : ['−03:00', '−02:00', 'NDT'],
			'America/Scoresbysund'             : ['−01:00', '+00:00', 'AST'],
			'America/Shiprock'                 : ['−07:00', '−06:00', 'AST'],
			'America/Sitka'                    : ['−09:00', '−08:00', 'AST'],
			'America/St_Barthelemy'            : ['−04:00', '−04:00', 'AST'],
			'America/St_Johns'                 : ['−03:30', '−02:30', 'CST'],
			'America/St_Kitts'                 : ['−04:00', '−04:00', 'CST'],
			'America/St_Lucia'                 : ['−04:00', '−04:00', 'UTC'],
			'America/St_Thomas'                : ['−04:00', '−04:00', 'ADT'],
			'America/St_Vincent'               : ['−04:00', '−04:00', 'EDT'],
			'America/Swift_Current'            : ['−06:00', '−06:00', 'UTC'],
			'America/Tegucigalpa'              : ['−06:00', '−06:00', 'UTC'],
			'America/Thule'                    : ['−04:00', '−03:00', 'UTC'],
			'America/Thunder_Bay'              : ['−05:00', '−04:00', 'UTC'],
			'America/Tijuana'                  : ['−08:00', '−07:00', 'PDT'],
			'America/Toronto'                  : ['−05:00', '−04:00', 'EDT'],
			'America/Tortola'                  : ['−04:00', '−04:00', 'AST'],
			'America/Vancouver'                : ['−08:00', '−07:00', 'PDT'],
			'America/Virgin'                   : ['−04:00', '−04:00', 'AST'],
			'America/Whitehorse'               : ['−08:00', '−07:00', 'PDT'],
			'America/Winnipeg'                 : ['−06:00', '−05:00', 'CDT'],
			'America/Yakutat'                  : ['−09:00', '−08:00', 'AKDT'],
			'America/Yellowknife'              : ['−07:00', '−06:00', 'MDT'],
			'Antarctica/Casey'                 : ['+11:00', '+08:00', 'AWST'],
			'Antarctica/Davis'                 : ['+05:00', '+07:00', 'DAVT'],
			'Antarctica/DumontDUrville'        : ['+10:00', '+10:00', 'DDUT'],
			'Antarctica/Macquarie'             : ['+11:00', '+11:00', 'MIST'],
			'Antarctica/Mawson'                : ['+05:00', '+05:00', 'MAWT'],
			'Antarctica/McMurdo'               : ['+12:00', '+13:00', 'NZDT'],
			'Antarctica/Palmer'                : ['−04:00', '−03:00', 'CLST'],
			'Antarctica/Rothera'               : ['−03:00', '−03:00', 'ROTT'],
			'Antarctica/South_Pole'            : ['+12:00', '+13:00', 'NZDT'],
			'Antarctica/Syowa'                 : ['+03:00', '+03:00', 'SYOT'],
			'Antarctica/Troll'                 : ['+00:00', '+02:00', 'UTC'],
			'Antarctica/Vostok'                : ['+06:00', '+06:00', 'VOST'],
			'Arctic/Longyearbyen'              : ['+01:00', '+02:00', 'CET'],
			'Asia/Aden'                        : ['+03:00', '+03:00', 'AST'],
			'Asia/Almaty'                      : ['+06:00', '+06:00', 'ALMT'],
			'Asia/Amman'                       : ['+02:00', '+03:00', 'EET'],
			'Asia/Anadyr'                      : ['+12:00', '+12:00', 'ANAT'],
			'Asia/Aqtau'                       : ['+05:00', '+05:00', 'AQTT'],
			'Asia/Aqtobe'                      : ['+05:00', '+05:00', 'AQTT'],
			'Asia/Ashgabat'                    : ['+05:00', '+05:00', 'TMT'],
			'Asia/Ashkhabad'                   : ['+05:00', '+05:00', 'TMT'],
			'Asia/Baghdad'                     : ['+03:00', '+03:00', 'AST'],
			'Asia/Bahrain'                     : ['+03:00', '+03:00', 'AST'],
			'Asia/Baku'                        : ['+04:00', '+05:00', 'AZT'],
			'Asia/Bangkok'                     : ['+07:00', '+07:00', 'ICT'],
			'Asia/Beirut'                      : ['+02:00', '+03:00', 'EET'],
			'Asia/Bishkek'                     : ['+06:00', '+06:00', 'KGT'],
			'Asia/Brunei'                      : ['+08:00', '+08:00', 'BNT'],
			'Asia/Calcutta'                    : ['+05:30', '+05:30', 'IST'],
			'Asia/Choibalsan'                  : ['+08:00', '+08:00', 'CHOT'],
			'Asia/Chongqing'                   : ['+08:00', '+08:00', 'CST'],
			'Asia/Chungking'                   : ['+08:00', '+08:00', 'CST'],
			'Asia/Colombo'                     : ['+05:30', '+05:30', 'IST'],
			'Asia/Dacca'                       : ['+06:00', '+06:00', 'BDT'],
			'Asia/Damascus'                    : ['+02:00', '+03:00', 'EET'],
			'Asia/Dhaka'                       : ['+06:00', '+06:00', 'BDT'],
			'Asia/Dili'                        : ['+09:00', '+09:00', 'TLT'],
			'Asia/Dubai'                       : ['+04:00', '+04:00', 'GST'],
			'Asia/Dushanbe'                    : ['+05:00', '+05:00', 'TJT'],
			'Asia/Gaza'                        : ['+02:00', '+03:00', 'EET'],
			'Asia/Harbin'                      : ['+08:00', '+08:00', 'CST'],
			'Asia/Hebron'                      : ['+02:00', '+03:00', 'EET'],
			'Asia/Ho_Chi_Minh'                 : ['+07:00', '+07:00', 'ICT'],
			'Asia/Hong_Kong'                   : ['+08:00', '+08:00', 'HKT'],
			'Asia/Hovd'                        : ['+07:00', '+07:00', 'HOVT'],
			'Asia/Irkutsk'                     : ['+08:00', '+08:00', 'IRKT'],
			'Asia/Istanbul'                    : ['+02:00', '+03:00', 'EET'],
			'Asia/Jakarta'                     : ['+07:00', '+07:00', 'WIB'],
			'Asia/Jayapura'                    : ['+09:00', '+09:00', 'WIT'],
			'Asia/Jerusalem'                   : ['+02:00', '+03:00', 'IST'],
			'Asia/Kabul'                       : ['+04:30', '+04:30', 'AFT'],
			'Asia/Kamchatka'                   : ['+12:00', '+12:00', 'PETT'],
			'Asia/Karachi'                     : ['+05:00', '+05:00', 'PKT'],
			'Asia/Kashgar'                     : ['+08:00', '+08:00', 'XJT'],
			'Asia/Kathmandu'                   : ['+05:45', '+05:45', 'NPT'],
			'Asia/Katmandu'                    : ['+05:45', '+05:45', 'NPT'],
			'Asia/Khandyga'                    : ['+09:00', '+09:00', 'YAKT'],
			'Asia/Kolkata'                     : ['+05:30', '+05:30', 'IST'],
			'Asia/Krasnoyarsk'                 : ['+07:00', '+07:00', 'KRAT'],
			'Asia/Kuala_Lumpur'                : ['+08:00', '+08:00', 'MYT'],
			'Asia/Kuching'                     : ['+08:00', '+08:00', 'MYT'],
			'Asia/Kuwait'                      : ['+03:00', '+03:00', 'AST'],
			'Asia/Macao'                       : ['+08:00', '+08:00', 'CST'],
			'Asia/Macau'                       : ['+08:00', '+08:00', 'CST'],
			'Asia/Magadan'                     : ['+10:00', '+10:00', 'MAGT'],
			'Asia/Makassar'                    : ['+08:00', '+08:00', 'WITA'],
			'Asia/Manila'                      : ['+08:00', '+08:00', 'PHT'],
			'Asia/Muscat'                      : ['+04:00', '+04:00', 'GST'],
			'Asia/Nicosia'                     : ['+02:00', '+03:00', 'EET'],
			'Asia/Novokuznetsk'                : ['+07:00', '+07:00', 'KRAT'],
			'Asia/Novosibirsk'                 : ['+06:00', '+06:00', 'NOVT'],
			'Asia/Omsk'                        : ['+06:00', '+06:00', 'OMST'],
			'Asia/Oral'                        : ['+05:00', '+05:00', 'ORAT'],
			'Asia/Phnom_Penh'                  : ['+07:00', '+07:00', 'ICT'],
			'Asia/Pontianak'                   : ['+07:00', '+07:00', 'WIB'],
			'Asia/Pyongyang'                   : ['+09:00', '+09:00', 'KST'],
			'Asia/Qatar'                       : ['+03:00', '+03:00', 'AST'],
			'Asia/Qyzylorda'                   : ['+06:00', '+06:00', 'QYZT'],
			'Asia/Rangoon'                     : ['+06:30', '+06:30', 'MMT'],
			'Asia/Riyadh'                      : ['+03:00', '+03:00', 'AST'],
			'Asia/Saigon'                      : ['+07:00', '+07:00', 'ICT'],
			'Asia/Sakhalin'                    : ['+11:00', '+11:00', 'SAKT'],
			'Asia/Samarkand'                   : ['+05:00', '+05:00', 'UZT'],
			'Asia/Seoul'                       : ['+09:00', '+09:00', 'KST'],
			'Asia/Shanghai'                    : ['+08:00', '+08:00', 'CST'],
			'Asia/Singapore'                   : ['+08:00', '+08:00', 'SGT'],
			'Asia/Taipei'                      : ['+08:00', '+08:00', 'CST'],
			'Asia/Tashkent'                    : ['+05:00', '+05:00', 'UZT'],
			'Asia/Tbilisi'                     : ['+04:00', '+04:00', 'GET'],
			'Asia/Tehran'                      : ['+03:30', '+04:30', 'IRST'],
			'Asia/Tel_Aviv'                    : ['+02:00', '+03:00', 'IST'],
			'Asia/Thimbu'                      : ['+06:00', '+06:00', 'BTT'],
			'Asia/Thimphu'                     : ['+06:00', '+06:00', 'BTT'],
			'Asia/Tokyo'                       : ['+09:00', '+09:00', 'JST'],
			'Asia/Ujung_Pandang'               : ['+08:00', '+08:00', 'WITA'],
			'Asia/Ulaanbaatar'                 : ['+08:00', '+08:00', 'ULAT'],
			'Asia/Ulan_Bator'                  : ['+08:00', '+08:00', 'ULAT'],
			'Asia/Urumqi'                      : ['+08:00', '+08:00', 'XJT'],
			'Asia/Ust-Nera'                    : ['+10:00', '+10:00', 'VLAT'],
			'Asia/Vientiane'                   : ['+07:00', '+07:00', 'ICT'],
			'Asia/Vladivostok'                 : ['+10:00', '+10:00', 'VLAT'],
			'Asia/Yakutsk'                     : ['+09:00', '+09:00', 'YAKT'],
			'Asia/Yekaterinburg'               : ['+05:00', '+05:00', 'YEKT'],
			'Asia/Yerevan'                     : ['+04:00', '+04:00', 'AMT'],
			'Atlantic/Azores'                  : ['−01:00', '+00:00', 'AZOT'],
			'Atlantic/Bermuda'                 : ['−04:00', '−03:00', 'ADT'],
			'Atlantic/Canary'                  : ['+00:00', '+01:00', 'WET'],
			'Atlantic/Cape_Verde'              : ['−01:00', '−01:00', 'CVT'],
			'Atlantic/Faeroe'                  : ['+00:00', '+01:00', 'WET'],
			'Atlantic/Faroe'                   : ['+00:00', '+01:00', 'WET'],
			'Atlantic/Jan_Mayen'               : ['+01:00', '+02:00', 'CET'],
			'Atlantic/Madeira'                 : ['+00:00', '+01:00', 'WET'],
			'Atlantic/Reykjavik'               : ['+00:00', '+00:00', 'GMT'],
			'Atlantic/South_Georgia'           : ['−02:00', '−02:00', 'GST'],
			'Atlantic/St_Helena'               : ['+00:00', '+00:00', 'GMT'],
			'Atlantic/Stanley'                 : ['−03:00', '−03:00', 'FKST'],
			'Australia/ACT'                    : ['+10:00', '+11:00', 'AEDT'],
			'Australia/Adelaide'               : ['+09:30', '+10:30', 'ACDT'],
			'Australia/Brisbane'               : ['+10:00', '+10:00', 'AEST'],
			'Australia/Broken_Hill'            : ['+09:30', '+10:30', 'ACDT'],
			'Australia/Canberra'               : ['+10:00', '+11:00', 'AEDT'],
			'Australia/Currie'                 : ['+10:00', '+11:00', 'AEDT'],
			'Australia/Darwin'                 : ['+09:30', '+09:30', 'ACST'],
			'Australia/Eucla'                  : ['+08:45', '+08:45', 'ACWST'],
			'Australia/Hobart'                 : ['+10:00', '+11:00', 'AEDT'],
			'Australia/LHI'                    : ['+10:30', '+11:00', 'LHDT'],
			'Australia/Lindeman'               : ['+10:00', '+10:00', 'AEST'],
			'Australia/Lord_Howe'              : ['+10:30', '+11:00', 'LHDT'],
			'Australia/Melbourne'              : ['+10:00', '+11:00', 'AEDT'],
			'Australia/North'                  : ['+09:30', '+09:30', 'AEDT'],
			'Australia/NSW'                    : ['+10:00', '+11:00', 'ACST'],
			'Australia/Perth'                  : ['+08:00', '+08:00', 'AWST'],
			'Australia/Queensland'             : ['+10:00', '+10:00', 'AEST'],
			'Australia/South'                  : ['+09:30', '+10:30', 'ACDT'],
			'Australia/Sydney'                 : ['+10:00', '+11:00', 'AEDT'],
			'Australia/Tasmania'               : ['+10:00', '+11:00', 'AEDT'],
			'Australia/Victoria'               : ['+10:00', '+11:00', 'AEDT'],
			'Australia/West'                   : ['+08:00', '+08:00', 'AWST'],
			'Australia/Yancowinna'             : ['+09:30', '+10:30', 'ACDT'],
			'Brazil/Acre'                      : ['−05:00', '−05:00', 'ACT'],
			'Brazil/DeNoronha'                 : ['−02:00', '−02:00', 'FNT'],
			'Brazil/East'                      : ['−03:00', '−02:00', 'BRT'],
			'Brazil/West'                      : ['−04:00', '−04:00', 'AMT'],
			'Canada/Atlantic'                  : ['−04:00', '−03:00', 'ADT'],
			'Canada/Central'                   : ['−06:00', '−05:00', 'CDT'],
			'Canada/Eastern'                   : ['−05:00', '−04:00', 'CST'],
			'Canada/East-Saskatchewan'         : ['−06:00', '−06:00', 'EDT'],
			'Canada/Mountain'                  : ['−07:00', '−06:00', 'MDT'],
			'Canada/Newfoundland'              : ['−03:30', '−02:30', 'NDT'],
			'Canada/Pacific'                   : ['−08:00', '−07:00', 'PDT'],
			'Canada/Saskatchewan'              : ['−06:00', '−06:00', 'CST'],
			'Canada/Yukon'                     : ['−08:00', '−07:00', 'PDT'],
			'Chile/Continental'                : ['−04:00', '−03:00', 'CLST'],
			'Chile/EasterIsland'               : ['−06:00', '−05:00', 'EASST'],
			'Cuba'                             : ['−05:00', '−04:00', 'CDT'],
			'Egypt'                            : ['+02:00', '+02:00', 'EET'],
			'Eire'                             : ['+00:00', '+01:00', 'GMT'],
			'Etc/GMT'                          : ['+00:00', '+00:00', 'GMT'],
			'Etc/GMT+0'                        : ['+00:00', '+00:00', 'GMT'],
			'Etc/UCT'                          : ['+00:00', '+00:00', 'UCT'],
			'Etc/Universal'                    : ['+00:00', '+00:00', 'UTC'],
			'Etc/UTC'                          : ['+00:00', '+00:00', 'UTC'],
			'Etc/Zulu'                         : ['+00:00', '+00:00', 'UTC'],
			'Europe/Amsterdam'                 : ['+01:00', '+02:00', 'CET'],
			'Europe/Andorra'                   : ['+01:00', '+02:00', 'CET'],
			'Europe/Athens'                    : ['+02:00', '+03:00', 'EET'],
			'Europe/Belfast'                   : ['+00:00', '+01:00', 'GMT'],
			'Europe/Belgrade'                  : ['+01:00', '+02:00', 'CET'],
			'Europe/Berlin'                    : ['+01:00', '+02:00', 'CET'],
			'Europe/Bratislava'                : ['+01:00', '+02:00', 'CET'],
			'Europe/Brussels'                  : ['+01:00', '+02:00', 'CET'],
			'Europe/Bucharest'                 : ['+02:00', '+03:00', 'EET'],
			'Europe/Budapest'                  : ['+01:00', '+02:00', 'CET'],
			'Europe/Busingen'                  : ['+01:00', '+02:00', 'CET'],
			'Europe/Chisinau'                  : ['+02:00', '+03:00', 'EET'],
			'Europe/Copenhagen'                : ['+01:00', '+02:00', 'CET'],
			'Europe/Dublin'                    : ['+00:00', '+01:00', 'GMT'],
			'Europe/Gibraltar'                 : ['+01:00', '+02:00', 'CET'],
			'Europe/Guernsey'                  : ['+00:00', '+01:00', 'GMT'],
			'Europe/Helsinki'                  : ['+02:00', '+03:00', 'EET'],
			'Europe/Isle_of_Man'               : ['+00:00', '+01:00', 'GMT'],
			'Europe/Istanbul'                  : ['+02:00', '+03:00', 'EET'],
			'Europe/Jersey'                    : ['+00:00', '+01:00', 'GMT'],
			'Europe/Kaliningrad'               : ['+02:00', '+02:00', 'EET'],
			'Europe/Kiev'                      : ['+02:00', '+03:00', 'EET'],
			'Europe/Lisbon'                    : ['+00:00', '+01:00', 'WET'],
			'Europe/Ljubljana'                 : ['+01:00', '+02:00', 'CET'],
			'Europe/London'                    : ['+00:00', '+01:00', 'GMT'],
			'Europe/Luxembourg'                : ['+01:00', '+02:00', 'CET'],
			'Europe/Madrid'                    : ['+01:00', '+02:00', 'CET'],
			'Europe/Malta'                     : ['+01:00', '+02:00', 'CET'],
			'Europe/Mariehamn'                 : ['+02:00', '+03:00', 'EET'],
			'Europe/Minsk'                     : ['+03:00', '+03:00', 'MSK'],
			'Europe/Thuaco'                    : ['+01:00', '+02:00', 'MSK'],
			'Europe/Moscow'                    : ['+03:00', '+03:00', 'EET'],
			'Europe/Nicosia'                   : ['+02:00', '+03:00', 'CET'],
			'Europe/Oslo'                      : ['+01:00', '+02:00', 'CET'],
			'Europe/Paris'                     : ['+01:00', '+02:00', 'CET'],
			'Europe/Podgorica'                 : ['+01:00', '+02:00', 'CET'],
			'Europe/Prague'                    : ['+01:00', '+02:00', 'EET'],
			'Europe/Riga'                      : ['+02:00', '+03:00', 'CET'],
			'Europe/Rome'                      : ['+01:00', '+02:00', 'SAMT'],
			'Europe/Samara'                    : ['+04:00', '+04:00', 'CET'],
			'Europe/San_Marino'                : ['+01:00', '+02:00', 'CET'],
			'Europe/Sarajevo'                  : ['+01:00', '+02:00', 'MSK'],
			'Europe/Simferopol'                : ['+03:00', '+03:00', 'CET'],
			'Europe/Skopje'                    : ['+01:00', '+02:00', 'EET'],
			'Europe/Sofia'                     : ['+02:00', '+03:00', 'CET'],
			'Europe/Stockholm'                 : ['+01:00', '+02:00', 'EET'],
			'Europe/Tallinn'                   : ['+02:00', '+03:00', 'UTC'],
			'Europe/Tirane'                    : ['+01:00', '+02:00', 'CET'],
			'Europe/Tiraspol'                  : ['+02:00', '+03:00', 'EET'],
			'Europe/Uzhgorod'                  : ['+02:00', '+03:00', 'EET'],
			'Europe/Vaduz'                     : ['+01:00', '+02:00', 'CET'],
			'Europe/Vatican'                   : ['+01:00', '+02:00', 'CET'],
			'Europe/Vienna'                    : ['+01:00', '+02:00', 'CET'],
			'Europe/Vilnius'                   : ['+02:00', '+03:00', 'EET'],
			'Europe/Volgograd'                 : ['+03:00', '+03:00', 'MSK'],
			'Europe/Warsaw'                    : ['+01:00', '+02:00', 'CET'],
			'Europe/Zagreb'                    : ['+01:00', '+02:00', 'CET'],
			'Europe/Zaporozhye'                : ['+02:00', '+03:00', 'EET'],
			'Europe/Zurich'                    : ['+01:00', '+02:00', 'CET'],
			'GB'                               : ['+00:00', '+01:00', 'GMT'],
			'GB-Eire'                          : ['+00:00', '+01:00', 'GMT'],
			'GMT'                              : ['+00:00', '+00:00', 'GMT'],
			'GMT+0'                            : ['+00:00', '+00:00', 'GMT'],
			'GMT0'                             : ['+00:00', '+00:00', 'GMT'],
			'GMT-0'                            : ['+00:00', '+00:00', 'GMT'],
			'Greenwich'                        : ['+00:00', '+00:00', 'GMT'],
			'Hongkong'                         : ['+08:00', '+08:00', 'HKT'],
			'Iceland'                          : ['+00:00', '+00:00', 'GMT'],
			'Indian/Antananarivo'              : ['+03:00', '+03:00', 'EAT'],
			'Indian/Chagos'                    : ['+06:00', '+06:00', 'IOT'],
			'Indian/Christmas'                 : ['+07:00', '+07:00', 'CXT'],
			'Indian/Cocos'                     : ['+06:30', '+06:30', 'CCT'],
			'Indian/Comoro'                    : ['+03:00', '+03:00', 'EAT'],
			'Indian/Kerguelen'                 : ['+05:00', '+05:00', 'TFT'],
			'Indian/Mahe'                      : ['+04:00', '+04:00', 'SCT'],
			'Indian/Maldives'                  : ['+05:00', '+05:00', 'MVT'],
			'Indian/Mauritius'                 : ['+04:00', '+04:00', 'MUT'],
			'Indian/Mayotte'                   : ['+03:00', '+03:00', 'EAT'],
			'Indian/Reunion'                   : ['+04:00', '+04:00', 'RET'],
			'Iran'                             : ['+03:30', '+04:30', 'IRST'],
			'Israel'                           : ['+02:00', '+03:00', 'IST'],
			'Jamaica'                          : ['−05:00', '−05:00', 'EST'],
			'Japan'                            : ['+09:00', '+09:00', 'JST'],
			'Kwajalein'                        : ['+12:00', '+12:00', 'MHT'],
			'Libya'                            : ['+02:00', '+01:00', 'EET'],
			'Mexico/BajaNorte'                 : ['−08:00', '−07:00', 'PDT'],
			'Mexico/BajaSur'                   : ['−07:00', '−06:00', 'MST'],
			'Mexico/General'                   : ['−06:00', '−05:00', 'CST'],
			'Navajo'                           : ['−07:00', '−06:00', 'NZDT'],
			'NZ'                               : ['+12:00', '+13:00', 'CHADT'],
			'NZ-CHAT'                          : ['+12:45', '+13:45', 'MDT'],
			'Pacific/Apia'                     : ['+13:00', '+14:00', 'CST'],
			'Pacific/Auckland'                 : ['+12:00', '+13:00', 'WSDT'],
			'Pacific/Chatham'                  : ['+12:45', '+13:45', 'NZDT'],
			'Pacific/Chuuk'                    : ['+10:00', '+10:00', 'CHADT'],
			'Pacific/Easter'                   : ['−06:00', '−05:00', 'CHUT'],
			'Pacific/Efate'                    : ['+11:00', '+11:00', 'EASST'],
			'Pacific/Enderbury'                : ['+13:00', '+13:00', 'VUT'],
			'Pacific/Fakaofo'                  : ['+13:00', '+13:00', 'PHOT'],
			'Pacific/Fiji'                     : ['+12:00', '+13:00', 'TKT'],
			'Pacific/Funafuti'                 : ['+12:00', '+12:00', 'FJT'],
			'Pacific/Galapagos'                : ['−06:00', '−06:00', 'TVT'],
			'Pacific/Gambier'                  : ['−09:00', '−09:00', 'GALT'],
			'Pacific/Guadalcanal'              : ['+11:00', '+11:00', 'GAMT'],
			'Pacific/Guam'                     : ['+10:00', '+10:00', 'SBT'],
			'Pacific/Honolulu'                 : ['−10:00', '−10:00', 'ChST'],
			'Pacific/Johnston'                 : ['−10:00', '−10:00', 'HST'],
			'Pacific/Kiritimati'               : ['+14:00', '+14:00', 'HST'],
			'Pacific/Kosrae'                   : ['+11:00', '+11:00', 'LINT'],
			'Pacific/Kwajalein'                : ['+12:00', '+12:00', 'KOST'],
			'Pacific/Majuro'                   : ['+12:00', '+12:00', 'MHT'],
			'Pacific/Marquesas'                : ['−09:30', '−09:30', 'MHT'],
			'Pacific/Midway'                   : ['−11:00', '−11:00', 'MART'],
			'Pacific/Nauru'                    : ['+12:00', '+12:00', 'SST'],
			'Pacific/Niue'                     : ['−11:00', '−11:00', 'NRT'],
			'Pacific/Norfolk'                  : ['+11:30', '+11:30', 'NUT'],
			'Pacific/Noumea'                   : ['+11:00', '+11:00', 'NFT'],
			'Pacific/Pago_Pago'                : ['−11:00', '−11:00', 'NCT'],
			'Pacific/Palau'                    : ['+09:00', '+09:00', 'SST'],
			'Pacific/Pitcairn'                 : ['−08:00', '−08:00', 'PWT'],
			'Pacific/Pohnpei'                  : ['+11:00', '+11:00', 'PST'],
			'Pacific/Ponape'                   : ['+11:00', '+11:00', 'PONT'],
			'Pacific/Port_Moresby'             : ['+10:00', '+10:00', 'PONT'],
			'Pacific/Rarotonga'                : ['−10:00', '−10:00', 'PGT'],
			'Pacific/Saipan'                   : ['+10:00', '+10:00', 'CKT'],
			'Pacific/Samoa'                    : ['−11:00', '−11:00', 'ChST'],
			'Pacific/Tahiti'                   : ['−10:00', '−10:00', 'SST'],
			'Pacific/Tarawa'                   : ['+12:00', '+12:00', 'TAHT'],
			'Pacific/Tongatapu'                : ['+13:00', '+13:00', 'GILT'],
			'Pacific/Truk'                     : ['+10:00', '+10:00', 'TOT'],
			'Pacific/Wake'                     : ['+12:00', '+12:00', 'CHUT'],
			'Pacific/Wallis'                   : ['+12:00', '+12:00', 'WAKT'],
			'Pacific/Yap'                      : ['+10:00', '+10:00', 'WFT'],
			'Poland'                           : ['+01:00', '+02:00', 'CHUT'],
			'Portugal'                         : ['+00:00', '+01:00', 'CET'],
			'PRC'                              : ['+08:00', '+08:00', 'WET'],
			'ROC'                              : ['+08:00', '+08:00', 'CST'],
			'ROK'                              : ['+09:00', '+09:00', 'KST'],
			'Singapore'                        : ['+08:00', '+08:00', 'SGT'],
			'Turkey'                           : ['+02:00', '+03:00', 'EET'],
			'UCT'                              : ['+00:00', '+00:00', 'UCT'],
			'Universal'                        : ['+00:00', '+00:00', 'AKDT'],
			'US/Alaska'                        : ['−09:00', '−08:00', 'HADT'],
			'US/Aleutian'                      : ['−10:00', '−09:00', 'MST'],
			'US/Arizona'                       : ['−07:00', '−07:00', 'CDT'],
			'US/Central'                       : ['−06:00', '−05:00', 'EDT'],
			'US/Eastern'                       : ['−05:00', '−04:00', 'EDT'],
			'US/East-Indiana'                  : ['−05:00', '−04:00', 'HST'],
			'US/Hawaii'                        : ['−10:00', '−10:00', 'CDT'],
			'US/Indiana-Starke'                : ['−06:00', '−05:00', 'EDT'],
			'US/Michigan'                      : ['−05:00', '−04:00', 'MDT'],
			'US/Mountain'                      : ['−07:00', '−06:00', 'PDT'],
			'US/Pacific'                       : ['−08:00', '−07:00', 'SST'],
			'US/Samoa'                         : ['−11:00', '−11:00', 'UTC'],
			'UTC'                              : ['+00:00', '+00:00', 'UTC'],
			'W-SU'                             : ['+03:00', '+03:00', 'MSK'],
			'Zulu'                             : ['+00:00', '+00:00', 'UTC'],
		}

	# Get strftime() flag definitions
	def get_time_flags(self):
		return {
			'a' : "Abbreviated weekday name",
			'A' : "Full weekday name",
			'b' : "Abbreviated month name",
			'B' : "Full month name",
			'c' : "Preferred date and time representation",
			'C' : "Century number [00-99]",
			'd' : "Day of the month with leading zeros [01 to 31]",
			'D' : "Current date, equal to %m/%d/%y",
			'e' : "Day of the month [1 to 31]",
			'E' : None,
			'F' : "Current date, equal to %Y-%m-%d",
			'f' : "",
			'g' : "Two-digit year based off the ISO 8601 week number [00-99]",
			'G' : "Four-digit year based off the ISO 8601 week number",
			'h' : "Abbreviated month name",
			'H' : "Hour using 24-hour notation [00-23]",
			'i' : "Hour using 12-hour notation [01-12]",
			'I' : "",
			'j' : "Day of the year [001-366]",
			'J' : None,
			'k' : "",
			'K' : None,
			'l' : "",
			'L' : None,
			'm' : "Month number with leading zeros [01-12]",
			'M' : "Minutes with leading zeros [00-59]",
			'n' : "Literal newline character",
			'N' : None,
			'o' : None,
			'O' : None,
			'p' : "AM|PM",
			'P' : None,
			'q' : None,
			'Q' : None,
			'r' : "Time in 12 hour notation",
			'R' : "Time in 24 hour notation",
			's' : "",
			'S' : "Seconds with leading zeros [00-59]",
			't' : "Literal tab character",
			'T' : "Current time, equal to %H:%M:%S",
			'u' : "Weekday as a number [1-7] where Mon=1. Note: In Sun Solaris Sun=1",
			'U' : "Week number, based off the first sunday of the year",
			'v' : "Current date, equal to %d-%b-%Y",
			'V' : "ISO 8601 week: Year starts Monday of 1st week with 4 days [01-53]",
			'w' : "Day of the week as a decimal, Sunday=0 [0-6]",
			'W' : "Week number: Year starting first Monday of the year [01-53]",
			'x' : "Preferred date representation",
			'X' : "Preferred time representation",
			'y' : "Two-digit year without century [00-99]",
			'Y' : "Four-digit year including century",
			'z' : "UTC offset in seconds, blank on naive objects",
			'Z' : "Time zone or name or abbreviation, blank on naive objects",
		}

	# Get a +ve or -ve human readable timestamp based off the local date/time
	def time_stamp(self, value="auto", tflags = ''):

		# A standard timezone was specified
		if isinstance(value, str) and value in self.timezones:
			# Set env to specified timezone
			os.environ['TZ'] = value
			# Reset time conversion rules
			time.tzset()
			# Return formatted timestring
			return time.strftime(tflags)

		# A Time offset from the local timezone was specified
		else:
			# Set env to default timezone, UTC at worst
			os.environ['TZ'] = s.get("timezone") if s.get("timezone") in self.timezones else 'UTC'
			# Reset time conversion rules
			time.tzset()
			# Grab datetime object for arithmetic
			now = datetime.now()


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
		totalsecs = (now - datetime.utcfromtimestamp(0)).total_seconds()

		# Convert back to time object for consistent formatting
		return time.strftime(tflags, time.localtime(totalsecs))

	#-------------------------------------------------------------------------------
	# Value Helpers
	#-------------------------------------------------------------------------------

	# Enable/Disbale docblock stamp alignment
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

			#
			for i, space in enumerate(stamp):
				if space == " " and i > idx:
					formatter = "{0:<"+ str(maxlength) +"s}{1}"
					lead      = stamp[:idx]
					left      = stamp[idx:i].rstrip()
					right     = stamp[i:].strip()
					aligned   = formatter.format(left, right)
					return lead + aligned

		return stamp

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
		#nohash = re.sub(m["checksum"]['regex'], '', self.data)

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

		# Grab user info
		userinfo             = s.get("user_info")
		userinfo["username"] = getpass.getuser()

		# Get available magic values
		magic_values = {
			"checksum"       : self.checksum(),
			"extension"      : self.get_file("extension", self.path),
			"base_name"      : self.get_file("base_name", self.path),
			"file_size"      : self.get_file("file_size", self.path),
			"file_name"      : self.get_file("file_name", self.path),
			"file_path"      : self.get_file("file_path", self.path),
			"parent_name"    : self.get_file("parent_name", self.path),
			"parent_path"    : self.get_file("parent_path", self.path),
			"file_extname"  : self.get_file("file_extname", self.path),
		}

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

		return magic_values

	# Recursively get the true value of a stamp.
	def true_values(self, stamp, final_value=True):

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

			# Format the stamp(s)
			if isinstance(value, list):
				layout = self.doc_align(layout.format(*value))
			else:
				layout = self.doc_align(layout.format(value))

			# Store final values, all recursion has completed.
			if final_value:
				m[name]['final_stamp'] = layout
				m[name]['final_value'] = value

			# Return a recursed and formatted sub-stamp
			else:
				return layout if stamp[0] != "_" else value

		# Only reach here on non stamp base stamp values
		return stamp

	# Build and format final stamp and value output strings
	def get_meta(self):

		# Iterate each stamp definitions...
		for stamp, info in m.items():

			# Check stamp is OK
			if 'value' not in info:
				m[stamp]['value'] = "LiveStamps: Stamp '" + stamp + "' has no value defined"

			# Get the 'true' values of the stamp (other stamps, times and magic values)
			self.true_values(stamp)

class StampInserterCommand(sublime_plugin.TextCommand):
	'''
	*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
	* Injects A Self Updating 'LiveStamp'
	*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
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
				if "stamp" in m[name]:
					result += m[name]["final_stamp"] + "\n"

		# Inject a single stamp
		else:
			result += m[kind]["final_stamp"]

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
	*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
	* Injects A Raw Value
	*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
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

class LiveStampsInsertCommand(sublime_plugin.TextCommand):
	'''
	*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
	* Wrapper Class For Stamp & Value Injection
	*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
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

		if kind == "all":
			stamptype += "s"

		# Build a status message
		msg = "LiveStamps: Inserted " + kind + " " + stamptype

		# Inform the user of the state change, via status bar and console
		self.view.run_command('notify', {'message': msg, 'modes': 'console status'})

class LiveStampsUpdateCommand(sublime_plugin.TextCommand):
	'''
	*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
	* Updates All Stamps In The Current View
	*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
	'''
	def run(self, edit):

		# Grab fresh file, user, document and checksum meta
		self.view.run_command('refresh_meta')

		# Build a status message
		msg = "LiveStamps: Updated all stamps"

		# Update any stamp, except those in a sublime settings files
		if "sublime" not in m["extension"]["value"] and m["file_extname"]["value"] != "LiveStamps.py":

			for stamp, info in m.items():
				# Check if a regex is supplied, it must be a live stamp
				if 'regex' in info and info['regex'] != 'auto':

					# Find each stamp and replace
					for region in self.view.find_all(info['regex'] , 0):
						self.view.replace(edit, region, info['final_stamp'])

		# Change notification on prevent
		else:
			msg = "LiveStamps: Auto update disabled while editing plugin files."


		# Inform the user of the state change, via status bar and console
		self.view.run_command('notify', {'message': msg, 'modes': 'console status'})

class LiveStampsHighlightCommand(sublime_plugin.TextCommand):
	'''
	*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
	* Enables or disableS various stamp highlighting modes
	*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*

		MODES:

		shading - Highlights the stamp background
		outline - Underlines the stamp
		markers - Adds markers in the gutter on lines where a stmap is present
	'''
	def run(self, view, clear=False):

		# Enable highlighting
		if (s.get("highlighter") and self.view.size() <= s.get("maxsize")):

			self.highlight()

		# Disable highlighting
		else:

			self.clear()

	#-------------------------------------------------------------------------------
	# Helpers
	#-------------------------------------------------------------------------------

	# Get all matching stamp patterns
	def find(self):

		result = [];

		# Iterate the stamp list
		for stamp, info in m.items():

			# Check if a regex is supplied
			if 'regex' in info:

				# Final initialization check
				if info['regex'] == 'auto':
					self.view.run_command('refresh_meta')
					return self.find()

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

	#-------------------------------------------------------------------------------
	# Highlight Region Calls
	#-------------------------------------------------------------------------------

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

class LiveStampsToggleCommand(sublime_plugin.TextCommand):
	'''
	*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
	* Toggles A Plugin Setting
	*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
	'''
	def run(self, edit, mode, value=None):

		self.value = value

		# Assume boolean True/False by default
		if value == None:

			# Get current State and toggle it
			value = False if s.get(mode) == True else True

			self.value = value

			# Save settings
			s.set(mode, value)
			sublime.save_settings("LiveStamps.sublime-settings")

			# Change to state to semantic output
			value = "ON" if value else "OFF"

		# Allow explicit values
		else:
			s.set(mode, value)
			sublime.save_settings("LiveStamps.sublime-settings")

		# Build a status message
		msg = "LiveStamps: Set " + mode + " to " + str(value)

		# Inform the user of the value change, via status bar and console
		self.view.run_command('notify', {'message': msg, 'modes': 'console status'})

		# Refresh highlighter
		self.view.run_command('live_stamps_highlight', {'clear': True})
		self.view.run_command('live_stamps_highlight')


	def is_checked(self, **args):

		mode = args['mode']

		# Check for non-boolean values
		if mode in ["markers", "underline", "hash_mode"] and "value" in args:
			return args['value'] == s.get(mode)

		return s.get(mode) != False

class LiveStampsMenuGenCommand(sublime_plugin.TextCommand):
	'''
	*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
	* Builds various ST3 menus to easily update user defined LiveStamp definitions
	*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
	'''
	def run(self, edit, menutype="context"):

		global m

		# Build every menu, one by one
		if menutype == "all":
			self.view.run_command('live_stamps_menu_gen', {'menutype' : 'context'})
			self.view.run_command('live_stamps_menu_gen', {'menutype' : 'toolbar'})
			self.view.run_command('live_stamps_menu_gen', {'menutype' : 'sidebar'})
			self.view.run_command('live_stamps_menu_gen', {'menutype' : 'command'})

		# Build a single menu
		else:

			# Get latest stamp definitions
			self.view.run_command('refresh_meta')

			# Sort them
			self.stamp_keys = self.sort_stamps()

			# Figure out menutype and filename
			if menutype == "context":
				menujson = self.get_context_menu()
				menuname = "Context.sublime-menu"

			elif menutype == "toolbar":
				menujson = self.get_toolbar_menu()
				menuname = "Main.sublime-menu"

			elif menutype == "sidebar":
				menujson = self.get_sidebar_menu()
				menuname = "Side Bar.sublime-menu"

			elif menutype == "command":
				menujson = self.get_command_menu()
				menuname = "LiveStamps.sublime-commands"

			# Concatenate the appropriate filename
			menuname = sublime.packages_path() + "/LiveStamps/" + menuname

			# Dump the dictionary to a JSON array
			if not isinstance(menujson, list):
				menujson = json.dumps( [menujson], sort_keys=False, indent=2 )
			else:
				menujson = json.dumps( menujson, sort_keys=False, indent=2 )

			# Write the new menu
			self.write_menu(menuname, menujson)

			# Build a status message
			msg = "LiveStamps: Generating " + menutype + " menu"

			# Inform the user of the state change, via status bar and console
			self.view.run_command('notify', {'message': msg, 'modes': 'console status'})

	#-------------------------------------------------------------------------------
	# I/O Helpers
	#-------------------------------------------------------------------------------

	# Write the menu to file
	def write_menu(self, fname, contents=False):
		'''
		Create a file from current view, or from specified string.
		'''

		ftemp = open(fname, "wb")

		if contents:
			ftemp.write(bytes(contents, 'UTF-8'))
		else:
			ftemp.write(self.get_text())

		ftemp.close

	# Insert the menu into the current view
	def paste_menu(self, menu):
		for pos in self.view.sel():
			# Insert at each cursor location
			if pos.empty():
				self.view.insert(edit, pos.a, menujson)
			# Replace selected area(s) with menu
			else:
				self.view.replace(edit, pos, menujson)

	#-------------------------------------------------------------------------------
	# Menu Constructors
	#-------------------------------------------------------------------------------

	# Sort user defined stamps into submenus
	def sort_stamps(self):

		# Create our menu sorting dictionary with a root menu by default
		menus = {'root': []}

		# Iterate the dictionary alphebetically
		for stamp in sorted(m.keys()):

			# If a stamp has a menu key defined, insert into submenu
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

		for menu in menus:
			menus[menu] = sorted(menus[menu])

		return menus

	# Build an ordered menu key
	def build_key(self, caption, command, args = None):

		# Build a menu key with arguments
		if isinstance(args, dict):
			return 	OrderedDict([
								("caption", caption.title().replace("_", " ")),
								("command", command),
								("args"   , args),
							])

		# Build a menu key with no arguments
		else:
			return 	OrderedDict([
								("caption", caption.title().replace("_", " ")),
								("command", command),
							])

	# Create an empty menu with headers
	def build_menu(self, caption="Submenu", ID=False, mnemonic=False):

		# Build an ordered menu with an optional identifier and mnemonic shortcut key
		if ID and mnemonic:
			return OrderedDict([
					("caption", caption),
					("id", ID),
					("mnemonic", mnemonic),
					("children"   , []),
				])
		elif ID:
			return OrderedDict([
					("caption", caption),
					("id", ID),
					("children"   , []),
				])
		else:
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
	def cap_check(self, cap_vals, noargs):

		result = {}

		# A dict was passed, all good
		if isinstance(cap_vals, dict):
			result = cap_vals

		# If a list of captions was passed use them to create a default dictionary
		elif isinstance(cap_vals, list):

			# Use caption as default argument value, or None if args flag is false
			for caption in cap_vals:
				result[caption] = None if noargs else caption

		# If a string was passed create a default dictionary
		elif isinstance(cap_vals, str):
			result = {
				cap_vals : None if noargs else cap_vals
			}

		return result #OrderedDict(sorted(result.items()))

	# Add keys to a parent menu with a common command
	def add_keys(self, parent, keymap, noargs = False):

		# Assign some vars for clarity
		command = keymap['command']
		argkeys = keymap['arg_keys']
		capvals = self.cap_check(keymap["cap_vals"], noargs)

		# Build each key
		for caption, argument in capvals.items():

			# When the command has no arguments, save some work
			if argument == None:
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

	#-------------------------------------------------------------------------------
	# Submenu Macros
	#-------------------------------------------------------------------------------

	# menu: Insert Stamps
	def get_stamp_menu(self, header='Insert Stamp', ID=False, mnemonic=False):

		# Define the submenu
		menu = self.build_menu(header, ID, mnemonic)

		# Iterate the sorted stamp commands
		for submenu in self.stamp_keys:

			# Add root commands
			if submenu == 'root':
				self.add_keys(menu, {
					"command"  : "live_stamps_insert",
					"arg_keys" : '{"stamptype": "stamp", "kind": "%s"}',
					"cap_vals" : self.stamp_keys[submenu],
				})

			# Add menus
			else:
				parent = self.add_keys(self.build_menu(submenu), {
					"command"  : "live_stamps_insert",
					"arg_keys" : '{"stamptype": "stamp", "kind": "%s"}',
					"cap_vals" : self.stamp_keys[submenu],
				})

				self.add_submenu(menu, parent)

		# Sort commands by caption key
		menu['children'] = sorted(menu['children'], key=lambda k: k['caption'])

		return menu

	# Submenu: Insert Value
	def get_value_menu(self, header='Insert Value', ID=False, mnemonic=False):

		# Define the submenu
		menu = self.build_menu(header, ID, mnemonic)

		# Iterate the sorted stamp commands
		for submenu in self.stamp_keys:

			# Add root commands
			if submenu == 'root':
				self.add_keys(menu, {
					"command"  : "live_stamps_insert",
					"arg_keys" : '{"stamptype": "value", "kind": "%s"}',
					"cap_vals" : self.stamp_keys[submenu],
				})

			# Add menus
			else:
				parent = self.add_keys(self.build_menu(submenu), {
					"command"  : "live_stamps_insert",
					"arg_keys" : '{"stamptype": "value", "kind": "%s"}',
					"cap_vals" : self.stamp_keys[submenu],
				})

				self.add_submenu(menu, parent)

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
			"cap_vals" : ["highlighter"],
		})

		self.add_divider(menu)

		# Add root commands
		self.add_keys(menu, {
			"command"  : "live_stamps_toggle",
			"arg_keys" : {"mode": 0},
			"cap_vals" : ["outline", "shading"],
		})

		# Add Marker submenu
		markers = self.add_keys(self.build_menu("Markers"), {
			"command"  : "live_stamps_toggle",
			"arg_keys" : {"mode": "markers", "value": 0},
			"cap_vals" : ["none", "dot", "circle", "bookmark", "cross"],
		})

		# Add menu marker submenu
		self.add_submenu( menu, markers )

		underlines = self.add_keys(self.build_menu("Underline"), {
			"command"  : "live_stamps_toggle",
			"arg_keys" : {"mode": "underline", "value": 0},
			"cap_vals" : ["none", "stippled", "squiggly", "solid"],
		})

		# Add menu marker submenu
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
			"cap_vals" : ["md5", "sha1", "sha224", "sha256", "sha384", "sha512"],
		})

	# Submenu: Menu Generation
	def get_menugen_menu(self, header='Generate Menu', ID=False, mnemonic=False):

		# Define the menu
		menu = self.build_menu(header, ID, mnemonic)

		# Add Checksum submenu
		launch = self.add_keys(self.build_menu("Open"), {
			"command"  : "open_file",
			"arg_keys" : '{"file" : "${packages}/LiveStamps/%s"}',
			"cap_vals" : {
				'Context Menu'  : "Context.sublime-menu",
				'Side Bar Menu' : "Side Bar.sublime-menu",
				'Main Menu'     : "Main.sublime-menu",
				'Commands'      : "LiveStamps.sublime-commands",
			},
		})

		self.add_submenu( menu, launch )

		# Add divider and settings commands
		self.add_divider(menu)

		# Add root commands
		return self.add_keys(menu, {
			"command"  : "live_stamps_menu_gen",
			"arg_keys" : {"menutype": 0},
			"cap_vals" : ["all", "command", "context", "sidebar", "toolbar"],
		})

	# Submenu: Plugin Preferences
	def get_preference_menu(self, header='Preferences', ID=False, mnemonic=False):

		# Define the menu
		menu = self.build_menu(header, ID, mnemonic)

		#menu['children'].append( self.build_key("Update On Save", "live_stamps_toggle", {"mode": "auto_update"}) )

		# Add divider and a single root key
		self.add_submenu( menu, self.build_key("Update On Save", "live_stamps_toggle", {"mode": "auto_update"}) )
		self.add_divider( menu )

		# Add menu Hilite submenu
		self.add_submenu( menu, self.get_hilite_menu() )

		# Add menu generation submenu
		self.add_submenu( menu, self.get_menugen_menu() )

		# Add Checksum submenu
		self.add_submenu( menu, self.get_checksum_menu() )

		# Add divider and settings commands
		self.add_divider( menu )
		self.add_keys(menu, {
			"command"  : "open_file",
			"arg_keys" : '{"file" : "${packages}/%s/LiveStamps.sublime-settings"}',
			"cap_vals" : {
				'Settings – Default' : "LiveStamps",
				'Settings – User'    : "User",
			},
		})

		# Add divider and keybindings commands, Special case create cap_vals programatically
		self.add_divider( menu )
		for platform in ['Windows', 'OSX', 'Linux']:
			self.add_keys( menu, {
				"command"  : "open_file",
				"arg_keys" : '{"file":"${packages}/%s/Default (%s).sublime-keymap", "platform":"%s"}',
				"cap_vals" : {
					'Key Bindings – Default' : ['LiveStamps', platform, platform],
					'Key Bindings – User'    : ['User',       platform, platform],
				},
			})

		return menu

	#-------------------------------------------------------------------------------
	# Main Menu Macros
	#-------------------------------------------------------------------------------

	# Context Menu
	def get_context_menu(self, header='LiveStamps', ID='timestamps-context-menu', mnemonic=False):

		# Define the menu
		menu = self.build_menu(header, ID, mnemonic)

		# Add submenus and dividers
		self.add_submenu( menu, self.get_stamp_menu() )
		self.add_submenu( menu, self.get_value_menu() )
		self.add_submenu( menu, self.get_preference_menu() )
		self.add_divider( menu )
		self.add_submenu( menu, self.build_key("Update Now", "live_stamps_update") )

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

	# Command Pallate Menu
	def get_command_menu(self):

		# Get menu of all commands and flatten
		context = self.get_context_menu()
		commands = self.get_commands(context)

		result = []

		# Iterate and modify captions to ensure unique commnads
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

class LiveStampsListener(sublime_plugin.EventListener):
	'''
	*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
	* Highlight & Autosave Event Listener
	*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
	'''
	def __init__(self):

		# Initialize queue tracker
		self.queue = 0


	# On first load check for setting initialization
	def check_init(self, view):

		if s.get("stamps") == None:
			view.run_command('refresh_meta')

	# Launch the highlighter on load, if enabled
	def on_load(self, view):

		# Check settings init
		self.check_init(view)

		if s.get("highlighter"):
			view.run_command('live_stamps_highlight')

	# Listen for save event
	def on_pre_save(self, view):

		# Check settings init
		self.check_init(view)

		if s.get("auto_update"):
			view.run_command('live_stamps_update')

	# When the view is changed, queue the highlighter and set the timeout
	def on_modified(self, view):

		# Check settings init
		self.check_init(view)

		# Increment queue
		self.queue += 1
		# Queue asynchronous worker thread
		sublime.set_timeout_async(lambda: self.queue_highlighter(view), s.get("timeout", 200))

	# If the queue is empty, call the highlighter. Otherwise wait for queue to clear
	def queue_highlighter(self, view):
		# Decrement queue
		self.queue -= 1
		# If nothing queued, do some work
		if self.queue == 0:
			view.run_command('live_stamps_highlight')

	# Launch the highlighter on activation, if enabled
	def on_activated_async(self, view):

		# Check settings init
		self.check_init(view)

		if s.get("highlighter"):

			view.run_command('live_stamps_highlight')



	# Determine if the view is a find results view.
	def is_find_results(view):
		return view.settings().get('syntax') and "Find Results" in view.settings().get('syntax')














