import sublime, sublime_plugin

class ExampleCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.view.insert(edit, 0, "Hello, World!")

class Logger(sublime_plugin.EventListener):
	def __init__(self):
		self.storage = []
	def on_new(self, view):
		try:
			edit = view.begin_edit('test')
			self.storage.append(repr(view))
			view.insert(edit, 0, repr(self.storage))
		finally:
			view.end_edit()