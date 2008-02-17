import os
import sys
import vim
import socket
import base64
import traceback
import xml.dom.minidom
import xmlrpclib
import re
########################
# TracWiki 
########################
class TracWiki:
	""" Trac Wiki Class """

	def __init__ (self, server_url):
		self.server = xmlrpclib.ServerProxy(server_url)
		self.multicall = xmlrpclib.MultiCall(self.server)

	def getAllPages(self):
		""" Gets a List of Wiki Pages """
		return "\n".join(self.server.wiki.getAllPages())
	
	def getPage(self, name, b_create = False):
		""" Get Wiki Page """
		self.currentPage = name
		try:
			wikitext = self.server.wiki.getPage(name)
		except:
			if b_create == True:
				wikitext = "Describe " + name + " here."
				try:
					self.savePage (name, wikitext, "Initializing")	
					return wikitext
				except:
					print "Could not create page " + name
			else:
				print "Could not find page " + name + ". Use :TracCreateWiki " + name+ " to create it"
		return wikitext 

	def savePage (self, content, comment):
		""" Saves a Wiki Page """
		return self.server.wiki.putPage(self.currentPage, content , {"comment" : comment})
	
	def createPage (self, name, content, comment):
		""" Saves a Wiki Page """
		return self.server.wiki.putPage(name, content , {"comment" : comment})

	def setServer (self, url):
		self.server = xmlrpclib.ServerProxy(url)
########################
# TracTicket 
########################
class TracTicket:
	""" Trac Ticket Class """

	def __init__ (self, server_url):
		self.server = xmlrpclib.ServerProxy(server_url)
		self.multicall = xmlrpclib.MultiCall(self.server)
		self.current_ticket_id = False
		self.a_option = []

	def setServer (self, url):
		self.server = xmlrpclib.ServerProxy(url)
		self.getOptions()

	def getOptions (self): 
		""" Get all milestone/ priority /status options """

		multicall = xmlrpclib.MultiCall(self.server)
		multicall.ticket.milestone.getAll()
		multicall.ticket.type.getAll()
		multicall.ticket.status.getAll()
		multicall.ticket.resolution.getAll()
		multicall.ticket.priority.getAll() 
		multicall.ticket.severity.getAll()
		multicall.ticket.component.getAll()
		
		a_option = []

		for option in  multicall():
			a_option.append(option)

		self.a_option =  a_option

	def getAllTickets(self,owner):
		""" Gets a List of Ticket Pages """
		multicall = xmlrpclib.MultiCall(self.server)

		if self.a_option == []:
			self.getOptions()

		for ticket in self.server.ticket.query("owner=" + owner):
			multicall.ticket.get(ticket)
	
		ticket_list = "" 

		for ticket in multicall():
			if ticket[3]["status"] != "closed":
				str_ticket =  " * Ticket ID: " + str(ticket[0]) + "\n"
				str_ticket += " * Status: " + ticket[3]["status"]+ "\n" 
				str_ticket += " * Summary: " + ticket[3]["summary"]+ "\n\n"
				str_ticket += "--------------------------------------------\n\n"

				ticket_list += str_ticket

		ticket_list += "\n\n\n\n\n\n"
		return ticket_list
	
	def getTicket(self, id):
		""" Get Ticket Page """
		self.current_ticket_id = id

		ticket =  self.server.ticket.get(id)
		ticket_changelog = self.server.ticket.changeLog(id)

		#ticket_options = self.server.ticket.getAvailableActions(id)



		str_ticket = "= Ticket Summary =\n\n"
		str_ticket += "*   Ticket ID: " + ticket[0] +"\n" 
		str_ticket += "*      Status: " + ticket[3]["status"] + "\n" 
		str_ticket += "*     Summary: " + ticket[3]["summary"] + "\n"
		str_ticket += "*        Type: " + ticket[3]["type"] + "\n" 
		str_ticket += "*    Priority: " + ticket[3]["priority"] + "\n" 
		str_ticket += "*   Component: " + ticket[3]["component"] + "\n"
		str_ticket += "*   Milestone: " + ticket[3]["milestone"] + "\n"
		str_ticket += "\n---------------------------------------------------\n" 
		str_ticket += "= Description: =\n\n" 
		str_ticket += ticket[3]["description"] + "\n" +"\n"

		str_ticket += "= CHANGELOG =\n\n"

		import datetime
		for change in ticket_changelog:
			if change[4] != '':
				my_time = datetime.datetime.fromtimestamp(change[0]).strftime("%A (%a) %d/%m/%Y %H:%M:%S")
				str_ticket +=  '== ' +  my_time + " ==\n"
				#just mention if a ticket has been changed
				if change[2] == 'description':
					str_ticket += "      (" + change[1]  + ": modified description)\n\n"
				
				elif change[2] == 'comment':
					str_ticket += "      (" + change[1]  + ": comment)\n\n"
					str_ticket += change[4] + "\n\n"
				elif change[2] == 'milestone':
					str_ticket += "      (" + change[1] + ": milestone set to " + change[4] + ")\n\n"
				else :
					str_ticket += "      (" + change[1] + ": " + change[2] + " set to " + change[4] + ")\n\n"

		return str_ticket

	def updateTicket(self, comment, attribs = {}, notify = False):
		""" add ticket comments change attributes """
		return self.server.ticket.update(self.current_ticket_id,comment,attribs,notify)

	def returnOptions(self,op_id):
		return self.a_option[op_id]

########################
# VimWindow 
########################
class VimWindow:
	""" wrapper class of window of vim """
	def __init__(self, name = 'WINDOW'):
		""" initialize """
		self.name       = name
		self.buffer     = None
		self.firstwrite = 1
	def isprepared(self):
		""" check window is OK """
		if self.buffer == None or len(dir(self.buffer)) == 0 or self.getwinnr() == -1:
		  return 0
		return 1
	def prepare(self):
		""" check window is OK, if not then create """
		if not self.isprepared():
		  self.create()
	def on_create(self):
		pass
	def getwinnr(self):
		return int(vim.eval("bufwinnr('"+self.name+"')"))

	def xml_on_element(self, node):
		line = str(node.nodeName)
		if node.hasAttributes():
		  for (n,v) in node.attributes.items():
			line += str(' %s=%s' % (n,v))
		return line
	def xml_on_attribute(self, node):
		return str(node.nodeName)
	def xml_on_entity(self, node):
		return 'entity node'
	def xml_on_comment(self, node):
		return 'comment node'
	def xml_on_document(self, node):
		return '#document'
	def xml_on_document_type(self, node):
		return 'document type node'
	def xml_on_notation(self, node):
		return 'notation node'
	def xml_on_text(self, node):
		return node.data
	def xml_on_processing_instruction(self, node):
		return 'processing instruction'
	def xml_on_cdata_section(self, node):
		return node.data

	def write(self, msg):
		""" append last """
		self.prepare()
		if self.firstwrite == 1:
		  self.firstwrite = 0
		  self.buffer[:] = str(msg).split('\n')
		else:
		  self.buffer.append(str(msg).split('\n'))
		self.command('normal gg')
		self.on_write()
		#self.window.cursor = (len(self.buffer), 1)
	def on_write(self):
		''' for vim commands after a write is made to a buffer '''
		pass
	def dump (self):
		""" read buffer """
		return "\n".join (self.buffer[:])

	def create(self, method = 'new'):
		""" create window """
		vim.command('silent ' + method + ' ' + self.name)
		#if self.name != 'LOG___WINDOW':
		vim.command("setlocal buftype=nofile")
		self.buffer = vim.current.buffer
		self.width  = int( vim.eval("winwidth(0)")  )
		self.height = int( vim.eval("winheight(0)") )
		self.on_create()
	def destroy(self):
		""" destroy window """
		if self.buffer == None or len(dir(self.buffer)) == 0:
		  return
		#if self.name == 'LOG___WINDOW':
		#  self.command('hide')
		#else:
		self.command('bdelete ' + self.name)
		self.firstwrite = 1
	def clean(self):
		""" clean all datas in buffer """
		self.prepare()
		self.buffer[:] = []
		self.firstwrite = 1
	def command(self, cmd):
		""" go to my window & execute command """
		self.prepare()
		winnr = self.getwinnr()
		if winnr != int(vim.eval("winnr()")):
		  vim.command(str(winnr) + 'wincmd w')
		vim.command(cmd)

	def _xml_stringfy(self, node, level = 0, encoding = None):
		if node.nodeType   == node.ELEMENT_NODE:
		  line = self.xml_on_element(node)

		elif node.nodeType == node.ATTRIBUTE_NODE:
		  line = self.xml_on_attribute(node)

		elif node.nodeType == node.ENTITY_NODE:
		  line = self.xml_on_entity(node)

		elif node.nodeType == node.COMMENT_NODE:
		  line = self.xml_on_comment(node)

		elif node.nodeType == node.DOCUMENT_NODE:
		  line = self.xml_on_document(node)

		elif node.nodeType == node.DOCUMENT_TYPE_NODE:
		  line = self.xml_on_document_type(node)

		elif node.nodeType == node.NOTATION_NODE:
		  line = self.xml_on_notation(node)

		elif node.nodeType == node.PROCESSING_INSTRUCTION_NODE:
		  line = self.xml_on_processing_instruction(node)

		elif node.nodeType == node.CDATA_SECTION_NODE:
		  line = self.xml_on_cdata_section(node)

		elif node.nodeType == node.TEXT_NODE:
		  line = self.xml_on_text(node)

		else:
		  line = 'unknown node type'

		if node.hasChildNodes():
		  #print ''.ljust(level*4) + '{{{' + str(level+1)
		  #print ''.ljust(level*4) + line
		  return self.fixup_childs(line, node, level)
		else:
		  return self.fixup_single(line, node, level)

		return line

	def fixup_childs(self, line, node, level):
		line = ''.ljust(level*4) + line +  '\n'
		line += self.xml_stringfy_childs(node, level+1)
		return line
	def fixup_single(self, line, node, level):
		return ''.ljust(level*4) + line + '\n'

	def xml_stringfy(self, xml):
		return self._xml_stringfy(xml)
	def xml_stringfy_childs(self, node, level = 0):
		line = ''
		for cnode in node.childNodes:
		  line = str(line)
		  line += str(self._xml_stringfy(cnode, level))
		return line

	def write_xml(self, xml):
		self.write(self.xml_stringfy(xml))
	def write_xml_childs(self, xml):
		self.write(self.xml_stringfy_childs(xml))

########################
# UI Base Class
########################
class UI:
	""" User Interface Base Class """
	def __init__(self):
		""" Initialize the User Interface """

	def normal_mode(self):
		""" restore mode to normal """
		if self.mode == 0: # is normal mode ?
			return

		vim.command('sign unplace 1')
		vim.command('sign unplace 2')

		# destory all created windows
		self.destroy()

		# restore session
		vim.command('source ' + self.sessfile)
		#os.system('rm -f ' + self.sessfile)

		self.winbuf.clear()
		self.file    = None
		self.line    = None
		self.mode    = 0
		self.cursign = None

########################
# WikiWindow Editing Window
########################
class WikiWindow (VimWindow):
	""" Wiki Window """
	def __init__(self, name = 'WIKI_WINDOW'):
		VimWindow.__init__(self, name)
	def on_create(self):
		vim.command('nnoremap <buffer> <c-]> :TracWikiView <C-R><C-W><cr>')
		vim.command('nnoremap <buffer> :q<cr> :TracNormalView<cr>')
		vim.command('nnoremap <buffer> :wq<cr> :TracSaveWiki<cr>:TracNormalView<cr>')
		vim.command('vertical resize +70')
		vim.command('nnoremap <buffer> :w<cr> :TracSaveWiki<cr>')
		vim.command('setlocal syntax=wiki')
		vim.command('setlocal linebreak')

########################
# WikiTOContentsWindow
########################
class WikiTOContentsWindow (VimWindow):
	""" Wiki Table Of Contents """
	def __init__(self, name = 'WIKITOC_WINDOW'):
		VimWindow.__init__(self, name)

		if vim.eval('tracHideTracWiki') == 'yes':
			self.hide_trac_wiki = True
		else:
			self.hide_trac_wiki = False

	def on_create(self):
		vim.command('nnoremap <buffer> <cr> :TracWikiView <C-R><C-W><cr>')
		vim.command('nnoremap <buffer> :q<cr> :TracNormalView<cr>')
		vim.command('setlocal winwidth=30')
		vim.command('vertical resize 30')
		vim.command('setlocal cursorline')
		vim.command('setlocal linebreak')

	def on_write(self):
		if self.hide_trac_wiki == True:
			vim.command('silent g/^Trac/d')
			vim.command('silent g/^Wiki/d')
			vim.command('silent g/^InterMapTxt$/d')
			vim.command('silent g/^InterWiki$/d')
			vim.command('silent g/^SandBox$/d')
			vim.command('silent g/^InterTrac$/d')
			vim.command('silent g/^TitleIndex$/d')
			vim.command('silent g/^RecentChanges$/d')
			vim.command('silent g/^CamelCase$/d')

		vim.command('sort')
		vim.command('silent norm ggOWikiStart')

########################
# TracWikiUI 
########################
class TracWikiUI(UI):
	""" Trac Wiki User Interface Manager """
	def __init__(self):
		""" Initialize the User Interface """
		self.wikiwindow = WikiWindow()
		self.tocwindow  = WikiTOContentsWindow()
		self.mode       = 0 #Initialised to default
		self.sessfile   = "/tmp/trac_vim_saved_session." + str(os.getpid())
		self.winbuf     = {}

	def trac_wiki_mode(self):
		""" change mode to wiki """
		if self.mode == 1: # is wiki mode ?
		  return
		self.mode = 1
		#if self.minibufexpl == 1:
		  #vim.command('CMiniBufExplorer')         # close minibufexplorer if it is open
		# save session
		vim.command('mksession! ' + self.sessfile)
		for i in range(1, len(vim.windows)+1):
		  vim.command(str(i)+'wincmd w')
		  self.winbuf[i] = vim.eval('bufnr("%")') # save buffer number, mksession does not do job perfectly
		                                          # when buffer is not saved at all.
		#vim.command('silent topleft new')       # create srcview window (winnr=1)
		#for i in range(2, len(vim.windows)+1):
		#  vim.command(str(i)+'wincmd w')
		#  vim.command('hide')
		self.create()
		vim.command('2wincmd w') # goto srcview window(nr=1, top-left)
		self.cursign = '1'

	def destroy(self):
		""" destroy windows """
		self.wikiwindow.destroy()
		self.tocwindow.destroy()

	def create(self):
		""" create windows """
		self.tocwindow.create("belowright new")
		self.wikiwindow.create("vertical belowright new")

########################
# TicketWindow Editing Window
########################
class TicketWindow (VimWindow):
	""" Ticket Window """
	def __init__(self, name = 'TICKET_WINDOW'):
		VimWindow.__init__(self, name)
	def on_create(self):
		vim.command('nnoremap <buffer> <c-]> :TracTicketView <C-R><C-W><cr>')
		#vim.command('resize +20')
		vim.command('nnoremap <buffer> :w<cr> :TracSaveTicket<cr>')
		vim.command('nnoremap <buffer> :wq<cr> :TracSaveTicket<cr>:TracNormalView<cr>')
		vim.command('nnoremap <buffer> :q<cr> :TracNormalView<cr>')
		vim.command('setlocal linebreak')
		vim.command('setlocal syntax=wiki')

########################
# TicketCommentWindow
########################
class TicketCommentWindow (VimWindow):
	""" For adding Comments to tickets """
	def __init__ (self,name = 'TICKET_COMMENT_WINDOW'):
		VimWindow.__init__(self, name)

	def on_create(self):
		vim.command('nnoremap <buffer> :w<cr> :TTAddComment<cr>')
		vim.command('nnoremap <buffer> :wq<cr> :TTAddComment<cr>:TracNormalView<cr>')
		vim.command('nnoremap <buffer> :q<cr> :TracNormalView<cr>')
		vim.command('setlocal syntax=wiki')

########################
# TicketTOContentsWindow
########################
class TicketTOContentsWindow (VimWindow):
	""" Ticket Table Of Contents """
	def __init__(self, name = 'TICKETTOC_WINDOW'):
		VimWindow.__init__(self, name)

	def on_create(self):
		vim.command('nnoremap <buffer> <cr> :TracTicketView <C-R><C-W><cr>')
		vim.command('nnoremap <buffer> j /Ticket ID:<cr>f: zt')
		vim.command('nnoremap <buffer> k ?Ticket ID:<cr>nf: zt')
		vim.command('nnoremap <buffer> :q<cr> :TracNormalView<cr>')
		vim.command('setlocal cursorline')
		vim.command('setlocal linebreak')
		vim.command('setlocal syntax=wiki')

########################
# TracTicketUI
########################
class TracTicketUI (UI):
	""" Trac Wiki User Interface Manager """
	def __init__(self):
		""" Initialize the User Interface """
		self.ticketwindow  = TicketWindow()
		self.tocwindow     = TicketTOContentsWindow()
		self.commentwindow = TicketCommentWindow()
		self.mode          = 0 #Initialised to default
		self.sessfile      = "/tmp/trac_vim_saved_session." + str(os.getpid())
		self.winbuf        = {}

	def trac_ticket_mode(self):
		""" change mode to ticket """
		if self.mode == 1: # is wiki mode ?
		  return
		self.mode = 1
		#if self.minibufexpl == 1:
		  #vim.command('CMiniBufExplorer')         # close minibufexplorer if it is open
		# save session
		vim.command('mksession! ' + self.sessfile)
		for i in range(1, len(vim.windows)+1):
		  vim.command(str(i)+'wincmd w')
		  self.winbuf[i] = vim.eval('bufnr("%")') # save buffer number, mksession does not do job perfectly
		                                          # when buffer is not saved at all.
		#vim.command('silent topleft new')       # create srcview window (winnr=1)
		#for i in range(2, len(vim.windows)+1):
		#  vim.command(str(i)+'wincmd w')
		#  vim.command('hide')
		self.create()
		vim.command('2wincmd w') # goto srcview window(nr=1, top-left)
		self.cursign = '1'

	def destroy(self):
		""" destroy windows """
		self.ticketwindow.destroy()
		self.tocwindow.destroy()
		self.commentwindow.destroy()

	def create(self):
		""" create windows """
		self.tocwindow.create("vertical belowright new")
		self.ticketwindow.create("belowright new")
		self.commentwindow.create("belowright new")

#########################
# TracServerUI
#########################
class TracServerUI (UI):
	""" Server User Interface View """

	def __init__(self):
		self.serverwindow = ServerWindow()
		self.mode       = 0 #Initialised to default
		self.winbuf     = {}

	def server_mode (self):
		""" Displays server mode """
		self.create()
		vim.command('2wincmd w') # goto srcview window(nr=1, top-left)
		self.cursign = '1'
	
	def create(self):
		""" create windows """
		self.serverwindow.create("belowright new")

	def destroy(self):
		""" destroy windows """
		self.serverwindow.destroy()

class ServerWindow(VimWindow):
	""" Server Window """

	def __init__(self, name = 'SERVER_WINDOW'):
		VimWindow.__init__(self, name)

	def on_create(self):
		vim.command('nnoremap <buffer> :q<cr> :TracNormalView<cr>')
		#TODO fix this it uses a named buffer
		vim.command('nnoremap <buffer> <cr> "byy:TracServerView <C-R><cr>')

#########################
# Main Class
#########################
class Trac:
	""" Main Trac class """
	def __init__ (self, comment , server_list):
		""" initialize Debugger """

		self.server_list     = server_list
		self.server_url      = server_list.values()[0]

		self.default_comment = comment
		self.wiki            = TracWiki(self.server_url)
		self.ticket          = TracTicket(self.server_url)
		self.ui              = TracWikiUI()
		self.uiserver        = TracServerUI()
		self.uiticket        = TracTicketUI()
		self.user            = self.get_user(self.server_url)


		vim.command('sign unplace *')

	def create_wiki_view(self , page, b_create = False) :
		""" Creates The Wiki View """
		if (page == False):
			page = 'WikiStart'

		self.ui.trac_wiki_mode()
		self.ui.tocwindow.clean()
		self.ui.tocwindow.write(self.wiki.getAllPages())
		self.ui.wikiwindow.clean()
		self.ui.wikiwindow.write(self.wiki.getPage(page, b_create))


	def create_ticket_view(self ,id = False) :
		""" Creates The Ticket View """

		self.uiticket.trac_ticket_mode()
		self.uiticket.tocwindow.clean()
		self.uiticket.tocwindow.write(self.ticket.getAllTickets(self.user))
		self.uiticket.ticketwindow.clean()
		if (id == False):
			self.uiticket.ticketwindow.write("Select Ticket To Load")
		else:
			self.uiticket.ticketwindow.write(self.ticket.getTicket(id))

		if self.ticket.a_option == []:
			self.ticket.getOptions()

	def create_server_view(self):
		""" Display's The Server list view """

		self.uiserver.server_mode()
		self.uiserver.serverwindow.clean()
		servers = "\n".join(self.server_list.keys())
		self.uiserver.serverwindow.write(servers)
	def set_current_server (self, server_key):
		""" Sets the current server key """	
		self.server_url = self.server_list[server_key]
		self.user = self.get_user(self.server_url)
		self.wiki.setServer(self.server_url)
		self.ticket.setServer(self.server_url)
		self.user = self.get_user(self.server_url)
		print "SERVER SET TO : " + server_key

	def get_user (self, server_url):
		#TODO fix for https
		return re.sub('http://(.*):.*$',r'\1',server_url)

#########################
# VIM API FUNCTIONS
#########################
def trac_init():
	''' Initialize Trac Environment '''
	global trac

	# get needed vim variables

	comment = vim.eval('tracDefaultComment')
	if comment == '':
		comment = 'VimTrac update'

	server_list = vim.eval('g:tracServerList')

	trac = Trac(comment, server_list)

def trac_wiki_view (name = False, new_wiki = False):
	''' View Wiki Page '''
	global trac
	#try: 
	trac.uiticket.normal_mode()
	trac.create_wiki_view(name, True)
	#except: 
	#	print "Could not make connection: "   +  "".join(traceback.format_tb( sys.exc_info()[2]))

def trac_normal_view ():
	'''  Back to Normal'''
	global trac
	try:
		trac.uiserver.normal_mode()
		trac.ui.normal_mode()
		trac.uiticket.normal_mode()

	except: 
		print "Could not make connection: " # + "".join(traceback.format_tb( sys.exc_info()[2]))

def trac_save_wiki (comment = ''):
	''' Save the Current Wiki Page '''
	global trac

	if comment == '':
		comment = trac.default_comment

	try:
		trac.wiki.savePage (trac.ui.wikiwindow.dump(), comment)
	except:
		print "Could not make connection: " # +  "".join(traceback.format_tb( sys.exc_info()[2]))

def trac_ticket_view (id = False):
	''' Ticket View '''
	global trac
	#try:
	trac.ui.normal_mode()
	trac.create_ticket_view(id)
	#except:
	#	print "Could not make connection: "  + "".join(traceback.format_tb( sys.exc_info()[2]))

def trac_server(server_key = ''):
	''' View Server Options '''
	global trac

	if server_key == '':
		print "Use Tab completion with :TracServer to cycle through servers"
		#trac.ui.normal_mode()
		#trac.create_server_view()
	else:
		trac.set_current_server(server_key)
		trac.uiticket.normal_mode()
		trac.create_wiki_view('WikiStart')

def trac_get_options(op_id):
	global trac

	option = trac.ticket.returnOptions(op_id)

	#if option == [] or trac.ticket.current_ticket_id == False or trac.uiticket.mode == 0:
		#print "This should only be used in ticket mode"
		#print option
		#print trac.ticket.current_ticket_id 
		#print trac.uiticket.mode 
		#
		#return 0
	
	vim.command ('let g:tracOptions = "' + "|".join (option) + '"')

def trac_set_ticket(option,value):
	global trac

	if value == '':
		print option + " was empty. No changes made."
		return 0

	if trac.uiticket.mode == 0 or trac.ticket.current_ticket_id == False:
		print "Cannot make changes when there is no current ticket open in Ticket View"
		return 0

	comment = ''
	attribs = {value:option}
	trac.ticket.updateTicket(comment, attribs, False)

def trac_add_comment():
	global trac
	comment = trac.uiticket.commentwindow.dump()
	attribs = {}
	if comment == '':
		print "Comment window is empty. Not adding to ticket"

	if trac.uiticket.mode == 0 or trac.ticket.current_ticket_id == False:
		print "Cannot make changes when there is no current ticket is open in Ticket View"
		return 0

	trac.ticket.updateTicket(comment, attribs, False)
	trac.uiticket.commentwindow.clean()
	trac.create_ticket_view(trac.ticket.current_ticket_id)
