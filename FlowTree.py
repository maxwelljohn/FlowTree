import sublime, sublime_plugin

class ExampleCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		self.view.insert(edit, 0, "Hello, World!")

class Logger(sublime_plugin.EventListener):
	def on_new(self, view):
		try:
			edit = view.begin_edit('test')
			view.insert(edit, 0, "I spy with my little eye...")
		finally:
			view.end_edit()