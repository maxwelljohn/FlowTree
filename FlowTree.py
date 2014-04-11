import sublime, sublime_plugin
from collections import namedtuple

class ViewNode(object):
	def __init__(self, description, children, is_search, is_open):
		self.description = description
		self.children = children
		self.is_search = is_search
		self.is_open = is_open

class ECommand(sublime_plugin.WindowCommand):
	root_node = ViewNode('root node', [], False, True)
	node_hist = [root_node]
	node_index = {}
	@classmethod
	def visit_node(cls, view, is_search=False):
		if is_search:
			last_search = view.find_all('Searching \d+ files for .*$')[-1]
			desc = view.substr(last_search)
			vid = str(view.id()) + '-' + desc
		else:
			desc = view.file_name()
			vid = str(view.id())

		if vid in cls.node_index:
			cls.node_hist.append(cls.node_index[vid])
		else:
			new_node = ViewNode(desc, [], is_search, True)
			# Filter out nodes that have been closed; they can't be assigned parentage.
			# (Mostly for the sake of searches.)
			cls.node_hist = [node for node in cls.node_hist if node.is_open]
			# Search views look for the most recent non-search view to use as their parent.
			hist = [node for node in cls.node_hist if not node.is_search] if is_search else cls.node_hist
			hist[-1].children.append(new_node)
			cls.node_index[vid] = new_node
			cls.node_hist.append(new_node)
		if len(cls.node_hist) > 100:
			cls.node_hist = cls.node_hist[-50:]
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
	@classmethod
	def record_on_close(cls, view):
		if cls.node_index[str(view.id())]:
			cls.node_index[str(view.id())].is_open = False
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
	def on_close(self, view):
		ECommand.record_on_close(view)