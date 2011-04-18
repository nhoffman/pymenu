#!/usr/bin/env python

__version__ = '0.2.0'

import sys
import os
import textwrap
import string
import logging

if sys.version_info[0] == 3:
    raw_input = input

log = logging

try:
    import curses, curses.textpad, curses.wrapper
    curses_ok = True
except ImportError:
    curses_ok = False
    log.info('curses module not available for import')
################### utility functions

def clear_screen(lines=50):
	print (('\n'*lines))

def check_file(filename):
	if not os.access(filename,os.F_OK):
		raise ResponseError('Error: cannot access %s ' % filename)

def offer_list(options):
	"""Options is a list of values or (value, label) pairs"""
	
	fstr = '%(i)3s) %(label)s'
	choices = {}
	for i, value in enumerate(options):
		i += 1
		try:
			# unpack fails if value is not a two-tuple
			value, label = value
		except (ValueError,TypeError):
			label = value
		choices[i] = {'i':i,'value':value, 'label':label}
		print((fstr % choices[i]))
	
	print((fstr % {'i':'X','label':'Exit this menu'}))
	
	response = None
	while True:
		uinput = raw_input('please enter a selection and press return: ').strip()
		if uinput.lower() == 'x':
			return response
		else:
			try:
				return choices[int(uinput)]['value']
			except KeyError:
				print(('"%s" is not an available choice' % uinput))
			except ValueError:
				print('please choose a number')
				
def offer_options(options, default=None):
    """options is a multiline string of the format 

        choice | msg | varout
        
    choice is a number to select at the prompt
    msg is a description of the choice
    varout is the value that will be returned 
    """
    
    while True:
        print(('Please choose from the following options or Q to quit, then press return.\n'))
        print(('%s) %s' % ('Q', 'quit')))
        d = {}
        first_int = 0
        last_choice = 'not an int'
        for line in options.splitlines():
            if line.strip() == '':
                continue
            choice, msg, varout = [x.strip() for x in line.split('|')]
            choice = choice.upper()
            
            if choice == '#':
                if isinstance(last_choice, int):
                    choice = last_choice + 1
                    last_choice = choice
                else:
                    choice = 1
                    last_choice = 1
            
            d['%s' % choice] = varout 
            print (('%s) %s' % (choice, msg)))
        
        if default:
            print (('[press return for %s]' % default))
        
        
        response = raw_input('\nPick a number or letter: ').upper()
        
        if response == 'Q':
            log.info('user terminated program')
            sys.exit('Quitting')
        elif response == '' and default is not None:
            return default
        elif response in d:
            return d[response]
        else:
            print (('\nError: [%s] is not an option\n' % response))

def request_file_name(msg=None):
	"""Prompt user for the name of a file; repeat if file not found.
	Return an absolute path."""
	
	while True:
		if msg:
			print ('')
			print ((textwrap.dedent(msg)))
			print ('')
		
		# note that dragging file icon into windows terminal generates external 
		# double quotes which muct be removed
		filename = raw_input('file or directory name: ').strip().replace('"','')
		
		if os.access(filename, os.F_OK):
			return os.path.abspath(filename)
		else:
			print (('---> File "%s" not found.' % filename))
			options = """
			1 | Try again | try_again
			"""
			response = offer_options(options)

if curses_ok:
    def _send_editor(stdscr,contents=None):
        """
        Present user with a simple editor. Call like this:
        
        edited_str = curses.wrapper(_send_editor,contents=starting_string)
        """
        
        instructions = """
        Ctrl-plus...
        <-B  F-> P-up N-down 
        A - Go to left edge E - Go to right edge 
        H - Backspace   D - Delete character under cursor.
        K - If line is blank, delete it, otherwise clear to end of line.
        O - Insert a blank line at cursor location.
        L - Refresh screen.
        J - Terminate if the window is 1 line, otherwise insert newline.
        G - Terminate, returning the window contents.
        """.strip().splitlines()
        
        ystart = len(instructions)
        
        begin_x = 0
        begin_y = ystart + 2
        height = 15
        width = 80
        win = curses.newwin(height, width, begin_y, begin_x)	 
        if contents:
            win.addstr(0,0,contents)
        TB = curses.textpad.Textbox(win)
            
        for i, line in enumerate(instructions):
            stdscr.addstr(i, 0, line.strip())
        stdscr.addstr(ystart + 1, 0, "Edit comment below:", curses.A_STANDOUT)
        stdscr.refresh()
        
        TB.edit()
        return TB.gather().strip()
    
    def send_editor(contents=None):
        return curses.wrapper(_send_editor, contents)

def multiline_input(msg = None, prompt='# '):
	
	if msg:
		sys.stdout.write( msg + '\n')
	sys.stdout.write('Press return then Ctrl+C when finished.\n')
	
	output = []
	
	try:
		while True:	
			output.append(raw_input(prompt))
	except KeyboardInterrupt:
		return '\n'.join([o.strip() for o in output	if o.strip()])


class StopAsking(Exception): pass
class ResponseError(Exception): pass

class Option:
	def __init__(self):
		self.send_editor = False
		
	def __getitem__(self, key):
		return getattr(self,key)
	
	def __repr__(self):
		keys = 'key val label type'.split()
		
		def getattr_safe(obj,attr,default):
			try:
				return getattr(self,k)
			except AttributeError:
				return default
		
		return '\n'.join(['%6s : %s' % (k, getattr_safe(self,k,None)) for k in keys])

class Menu:
	"""
	Creates a simple, interactive text-based user interface. 
	"""
	
	def __init__(self, width=60, xlabel=None, qlabel=None, screenheight=50):
			
		self.options = {} # self.options[key] = Option instance
		self.keys = [] # provide order to the set of options
		self.width = width
		self.wrapper = textwrap.TextWrapper(
			initial_indent=')' + ' ' * 2,
			subsequent_indent = ' ' * 5,
			width=width)
		# don't clear screen on first invocation
		self.cls = False	
		self.screenheight = screenheight
		self.pick = {} # used in self.display()
		self.visible = set()
		
		if not xlabel: xlabel = 'Exit this menu and continue'
		if not qlabel: qlabel = 'Quit the program'
		
		self.xlabel = xlabel
		self.qlabel = qlabel
							
	def __getitem__(self, key):
		return self.options[key]
	
	def get(self, key, alt=None):
		return self.options.get(key, alt)

	def clear(self):
		clear_screen(self.screenheight)

	def add_parser_data(self, parser, options, exclude=None):

		"""Add options using information from optparse.OptionParser 
		object and options (output of parser.parse_args()). Options 
		with keys in set exclude will not be added to the 
		interactive menu."""

		if not exclude:
			exclude = set()
			
		for opt in parser.option_list:			
			if not opt.dest or opt.dest in exclude:
				continue

			if isinstance(opt.default, bool):
				this_type = 'bool'
			else:
				this_type = opt.type
						
			self.add_option(key = opt.dest,
				label = opt.help,
				val = getattr(options, opt.dest),
				type = this_type,
				is_file = opt.metavar == 'FILE')

	def set_default(self, key, val):
		"""
		Set default value for a single option
		"""
		
		opt = self[key]		
		fun = {'int':int, 'float':float, 'bool':bool}.get(opt.type, str)
		
		try:						
			val = fun(val)
		except ValueError:
			raise ResponseError("""'%s' is not a valid option""" % val)
		
		# don't check if file isn't specified
		if opt.is_file and bool(val):			
			# windows terminal encloses filename in double quotes
			val = val.strip().replace('"','')
			check_file(val)
		
		opt.key, opt.val = key, val
		return opt.val
	
	def set_defaults(self, **kwargs):
		"""Sets option values from a dictionary of key, val pairs.
		Raises AssertionError if input dictionary contains keys not found in 
		self.options"""
		
		for k,v in list(kwargs.items()):
			assert k in self.options
			opt = self.set_default(k,v)
				
	def add_option(self, key, label, val=None, 
		type='string', handler=None, is_file=False, send_editor=False):
		
		"""
		key - a string to identify the option
		val - default option value
		type - choose from int, float, string, bool
		label - a description of the parameter
		handler - a function that takes a Menu instance as its only argument. 
		Unacceptable responses can raise a ResponseError and provide 
		an error message; acceptable responses return a value to set as 
		opt.val. The handler is expected to provide prompts for user input.
		Other input to the handler function can be provided as
		attributes of the menu instance.
 		"""
		opt = Option()
		
		assert type in ['int','float','bool','string','choice']
		opt.type = {'int':'int','float':'float','bool':'bool'}.get(type,'string')
		
		self.options[key] = opt
		self.keys.append(key)
		
		opt.label = ' '.join(label.split())
		opt.is_file = is_file

		if handler:
			opt.handler = handler
		else:
			opt.handler = None
		
		opt.send_editor = send_editor
		
		self.set_default(key,val)
		# the option is visible by default
		self.visible.add(key)
				
	def display(self, header=None):	
				
		fstr = '%2s%s %s'
		if self.cls: self.clear()
		if header: print ((header,'\n'))
		
		self.wrapper.width = self.width
		self.pick = {}		
		options = [self.options[k] for k in self.keys if k in self.visible]
		for i, opt in enumerate(options):
			i += 1
			self.pick[i] = opt
			lines = self.wrapper.wrap(opt.label)	
			this_width = {1:self.width}.get(len(lines), self.width+2)
						
			if opt.val != '':
				lines[-1] =  lines[-1].rstrip().ljust(this_width,'.')
			
			help = '\n'.join(lines)
			print((fstr % (i, help, opt.val) + '\n'))
		print((' '*5 + '-'*self.width))
		print((' X' + self.wrapper.fill(self.xlabel)))
		print((' Q' + self.wrapper.fill(self.qlabel) + '\n'))
		self.cls = True

	def ask_number(self):
				
		msg = 'Choose a number above to change a setting: '
		response = raw_input(msg).strip()
		
		try:
			if not response:
				raise ResponseError('Please enter a number listed above')
			if response.lower() == 'x':
				raise StopAsking
			elif response.lower() == 'q':
				sys.exit()
			
			# return an Option object
			return self.pick[int(response)]
		except KeyError:
			raise  ResponseError('%s is not an available option' % response)
		except ValueError:
			raise ResponseError('Please choose a number listed above')
	
	def handle_response(self, opt=None):
				
		if not opt:
			opt = self.ask_number()
		
		if opt.handler:
			response = opt.handler(self)
		elif opt.send_editor:
			log.debug('sending editor containing value [%s]' % opt.val)
			response = send_editor(opt.val)
			log.debug('editor returned value [%s]' % response)
		else:		
			if opt.type == 'bool':
				opt.val = not opt.val
				return
			elif opt.is_file:
				msg = 'Drag a file icon into this window to select a file or folder: '
			else:
				msg = {'int': 'Please enter a number: ',
				'float': 'Please enter a number: ',
				'string': 'Please enter a value: '}[opt.type]
			response = raw_input(msg).strip()
			
		if response or response is False:
			self.set_default(opt.key, response)
			log.debug('set %s to [%s]' % (opt.key, opt.val))
					
	def get_dict(self):		
		return dict([(k, o.val) for k,o in list(self.options.items())])
		
	def run(self, header=None):
		"""
		Present the user with a menu of options."""
		
		show = True
		while True:
			try:
				if show:
					self.display(header)
				self.handle_response()
				
				show = True
			except StopAsking:
				return self.get_dict()
			except ResponseError as msg:
				print(('\n' + msg.__str__().strip()))
				show = False
		
		
if __name__ == '__main__':
	
	import pprint, glob, optparse
	
	def wrap_handler(menu):
		submenu = Menu(width=menu.width)
		submenu.add_option('wrap_width', 'Wrap width', menu['wrap_width'].val,'int')
		submenu.cls = True
		
		new_width = submenu.run()['wrap_width']
		menu.width = new_width
		return new_width
			
	def color_handler(menu):
		
		submenu = Menu(width=menu.width)
		submenu.add_option('color', 'Favorite Color', menu['color'].val)
		submenu.cls = True	
		return submenu.run()['color']
		
	def add_opt_handler(menu):
		
		submenu = Menu(width=menu.width)
		submenu.add_option('key', 'Option Key', None)
		submenu.add_option('label', 'Option Label', None)
		submenu.add_option('val', 'Option Value', None)		
		submenu.cls = True	
		subdict = submenu.run()
		menu.add_option(**subdict)
	
	def see_files(menu):
		
		files = glob.glob(os.path.join(os.path.split(__file__)[0],'*.py'))
		print('please select a file')
		return offer_list(files)
		
	def hide_opt(menu):
		print('choose an option to hide')
		menu.visible.remove(offer_list([k for k in menu.keys if k in menu.visible]))
		
	usage = "Usage: Menu.py [options]"
	parser = optparse.OptionParser(usage=usage, version=__version__)
	
	parser.add_option("-c", "--count", dest="count",
	help="""Number of objects. The objects 
	might be small, or round, or wet, or salty. They may not be
	made of paper or lead. If you insist, the objects might be 
	imported from China, but not from Indonesia or France.""", default=1,
	type='int')
	
	parser.add_option("-s", "--favorite_song", dest="favorite_song",
	help='Favorite Song', default='My country tis of thee')

	parser.add_option("-H", "--height", dest="height",
	help='Height in cm', default=60.5, type='float')	

	parser.add_option("-d", "--loves_dogs", dest="loves_dogs",
	help='Really likes dogs', action='store_true', default=False)

	parser.add_option("-w", "--wrap_width", dest="wrap_width",
	help='Width of Menu interface in characters', default=40, type='int')

	parser.add_option("-C", "--color", dest="color",
	help='Favorite Color', default='green')
	
	(options, args) = parser.parse_args()
	
	# create the Menu instance, importing options from parser
	menu = Menu()
	menu.add_parser_data(parser, options)
	
	object_msg = """
	Number of objects. The objects might be small, or round,
	or wet, or salty. They may not be made of paper or red.
	If you insist, the objects might be imported from China,
	but not from Indonesia or France.
	""".strip()
	
	# can add handlers to existing options
	menu['wrap_width'].handler = wrap_handler
	menu['color'].handler = color_handler	
	
	# can also add new options 
	menu.add_option('add_option', 'add an option', '', handler=add_opt_handler)	
	menu.add_option('choose_file', 'Choose a .py file', '', handler=see_files)	
	menu.add_option('hide', 'Choose an option to hide', '', handler=hide_opt)
	menu.add_option('edit_test', 'Test the editor', 'starting text', send_editor=True)
	
	# print the values of the option, value pairs on completion
	pprint.PrettyPrinter().pprint(menu.run())
	raw_input('press return to continue. ')
	
	# override defaults passed from OptionParser instance
	d = {'count': 5,
		'favorite_song': 'Wish You Were Here',
		'height': 44.0,
		'loves_dogs': True} 
	
	menu.set_defaults(**d)
	# print the values of the option, value pairs on completion
	pprint.PrettyPrinter().pprint(menu.run())
	
