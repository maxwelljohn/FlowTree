import sublime, sublime_plugin

class ExampleCommand(sublime_plugin.TextCommand):
	msg = "Hello, World!"
	def run(self, edit):
		self.view.insert(edit, 0, ExampleCommand.msg)

class Logger(sublime_plugin.EventListener):
	def __init__(self):
		self.storage = []
	def on_new(self, view):
		try:
			edit = view.begin_edit('test')
			self.storage.append(repr(view))
			ExampleCommand.msg = repr(self.storage)
		finally:
			view.end_edit(edit)