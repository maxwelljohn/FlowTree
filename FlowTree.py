import sublime, sublime_plugin
from collections import namedtuple

ViewNode = namedtuple('ViewNode', ['description', 'children'])

class ECommand(sublime_plugin.WindowCommand):
	root_node = ViewNode('root node', [])
	current_node = root_node
	node_index = {}
	@classmethod
	def visit_node(cls, view, search=False):
		if search:
			last_search = view.find_all('Searching \d+ files for .*$')[-1]
			desc = view.substr(last_search)
			vid = str(view.id()) + '-' + desc
		else:
			desc = view.file_name()
			vid = str(view.id())

		if vid in cls.node_index:
			cls.current_node = cls.node_index[vid]
		else:
			new_node = ViewNode(desc, [])
			cls.current_node.children.append(new_node)
			cls.node_index[vid] = new_node
			cls.current_node = new_node
			print(cls.flow_tree())
	@classmethod
	def record_on_activated(cls, view):
		if view.file_name():
			cls.visit_node(view)
	@classmethod
	def record_on_deactivated(cls, view):
		if 'Find Results' in view.name():
			cls.visit_node(view, True)
	@classmethod
	def flow_tree(cls):
		def show_node(node, indent):
			result = '  ' * indent
			result += node.description
			result += '\n'
			for child in node.children:
				result += show_node(child, indent + 1)
			return result
		return show_node(cls.root_node, 0)
	def run(self):
		view = self.window.new_file()
		view.set_name('Your FlowTree')
		edit = view.begin_edit('DisplayFlowTree')
		try:
			view.insert(edit, 0, ECommand.flow_tree())
		finally:
			view.end_edit(edit)

class Logger(sublime_plugin.EventListener):
	def on_activated(self, view):
		ECommand.record_on_activated(view)
	def on_deactivated(self, view):
		ECommand.record_on_deactivated(view)