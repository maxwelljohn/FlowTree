import sublime, sublime_plugin
from collections import namedtuple

ViewNode = namedtuple('ViewNode', ['description', 'children'])

class ECommand(sublime_plugin.TextCommand):
	root_node = ViewNode('root node', [])
	current_node = root_node
	node_index = {}
	@classmethod
	def record_on_activated(cls, view):
		vid = view.id()
		if view.file_name():
			if vid in cls.node_index:
				cls.current_node = cls.node_index[vid]
			else:
				new_node = ViewNode(view.file_name(), [])
				cls.current_node.children.append(new_node)
				cls.node_index[vid] = new_node
				cls.current_node = new_node
			print(cls.flow_tree())
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
	def run(self, edit):
		self.view.insert(edit, 0, ECommand.flow_tree())

class Logger(sublime_plugin.EventListener):
	def on_activated(self, view):
		ECommand.record_on_activated(view)