import sublime, sublime_plugin

class ECommand(sublime_plugin.TextCommand):
	msg = "Hello, World!"
	def run(self, edit):
		self.view.insert(edit, 0, ECommand.msg)

class Logger(sublime_plugin.EventListener):
	def __init__(self):
		self.storage = []
	def log_info(self, view, action):
		entry = "%s view #%d, window %s, buffer %d, filename %s" % (action, view.id(), repr(view.window()), view.buffer_id(), view.file_name())
		print(entry)
		self.storage.append(entry)
		ECommand.msg = repr(self.storage)
	def on_new(self, view):
		self.log_info(view, 'new')
	def on_load(self, view):
		self.log_info(view, 'load')
	def on_activated(self, view):
		self.log_info(view, 'activated')