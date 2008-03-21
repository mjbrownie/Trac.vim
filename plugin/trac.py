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
class TracRPC:
	def __init__ (self, server_url):
		self.server_url = server_url
		self.server = xmlrpclib.ServerProxy(server_url)
		self.multicall = xmlrpclib.MultiCall(self.server)
	def setServer (self, url):
		self.server_url = url
		self.server = xmlrpclib.ServerProxy(url)

class TracWiki(TracRPC):
	""" Trac Wiki Class """

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
	
	def addAttachment (self, file):
		''' Add attachment '''
		file_name = os.path.basename (file)
		
		self.server.wiki.putAttachment(self.currentPage + '/' + file_name , xmlrpclib.Binary(open(file).read()))

	def getAttachment (self, file):
		''' Add attachment '''
		buffer = self.server.wiki.getAttachment( file )
		file_name = os.path.basename (file)
		
		if os.path.exists(file_name) == False:
			fp = open(file_name , 'w')
			fp.write (buffer.data)	
			fp.close()
		else:
			print "Will not overwrite existing file "  + file_name

	def listAttachments(self):
		self.current_attachments = self.server.wiki.listAttachments(self.currentPage)

	def getWikiHtml(self, wikitext):
		return self.server.wiki.wikiToHtml(wikitext)
	
	def getPageHtml(self, page):
		return self.server.wiki.getPageHTML(page)

########################
# TracTicket 
########################
class TracTicket(TracRPC):
	""" Trac Ticket Class """

	def __init__ (self, server_url):
		
		TracRPC.__init__(self, server_url)
		
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

		#for ticket in self.server.ticket.query("owner=" + owner):
		for ticket in self.server.ticket.query():
			multicall.ticket.get(ticket)
	
		ticket_list = "(Hit <enter> or <space> on a line containing Ticket:>>)\n" 

		for ticket in multicall():
			if ticket[3]["status"] != "closed":
				
				str_ticket = "\n================================================="
				str_ticket +=  "\nTicket:>> " + str(ticket[0])
				str_ticket += "\n================================================="
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

		self.listAttachments()

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
		str_ticket += "* Attachments: " + "\n"
		for attach in self.current_attachments:
			str_ticket += '               ' + attach

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

	def createTicket (self, description, summary):
		""" create a trac ticket """

		attributes = {}
		self.current_ticket_id =  self.server.ticket.create(summary, description, attributes, False)

	def addAttachment (self, file):
		''' Add attachment '''
		file_name = os.path.basename (file)
		
		self.server.ticket.putAttachment(self.current_ticket_id, file,'attachment' , xmlrpclib.Binary(open(file).read()))

	def listAttachments(self):
		a_attach = self.server.ticket.listAttachments(self.current_ticket_id)

		self.current_attachments = []
		for attach in a_attach:
			self.current_attachments.append (attach[0])

	
	def returnOptions(self,op_id):
		return self.a_option[op_id]

	def getAttachment (self, file):
		''' Add attachment '''
		buffer = self.server.ticket.getAttachment( self.current_ticket_id , file )
		file_name = os.path.basename (file)
	
		if os.path.exists(file_name) == False:
			fp = open(file_name , 'w')
			fp.write (buffer.data)	
			fp.close()
		else:
			print "Will not overwrite existing file "  + file_name
		
class TracSearch(TracRPC):
	""" Search for tickets and Wiki's """
	def __init__ (self, server_url):
		TracRPC.__init__(self, server_url)

	def search(self , search_pattern):
		""" Perform a search call  """
		a_search =  self.server.search.performSearch(search_pattern)
		
		str_result = "Results for " + search_pattern + "\n\n"
		str_result += "(Hit <enter> or <space >on a line containing Ticket:>>)"
		for search in a_search:
			str_result += "\n================================================="
			
			if search[0].find('/ticket/') != -1: 
				str_result += "\nTicket:>> " + os.path.basename (search[0])
			if search[0].find('/wiki/')!= -1: 
				str_result += "\nWiki:>> " + os.path.basename(search[0])
			if search[0].find('/changeset/')!= -1: 
				str_result += "\nChangeset:>> " + search[0] #os.path.basename(search[0])

			str_result += "\n=================================================\n"
			str_result += "\n" + search[4]
			str_result += "\n-------------------------------------------------\n\n\n"

		return str_result
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
		#(disabling this)
		#vim.command('source ' + self.sessfile)
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
		vim.command('nnoremap <buffer> :wq<cr> :TracSaveWiki')
		vim.command('vertical resize +70')
		vim.command('nnoremap <buffer> :w<cr> :TracSaveWiki')
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
		vim.command('nnoremap <buffer> <cr> :python trac_wiki_view("CURRENTLINE")<cr>')
		vim.command('nnoremap <buffer> <Space> :python trac_html_view ()<cr><cr><cr>')
		vim.command('nnoremap <buffer> :q<cr> :TracNormalView<cr>')
		vim.command('setlocal winwidth=30')
		vim.command('vertical resize 30')
		vim.command('setlocal cursorline')
		vim.command('setlocal linebreak')

	def on_write(self):
		if self.hide_trac_wiki == True:
			vim.command('silent g/^Trac/d _')
			vim.command('silent g/^Wiki/d _')
			vim.command('silent g/^InterMapTxt$/d _')
			vim.command('silent g/^InterWiki$/d _')
			vim.command('silent g/^SandBox$/d _')
			vim.command('silent g/^InterTrac$/d _')
			vim.command('silent g/^TitleIndex$/d _')
			vim.command('silent g/^RecentChanges$/d _')
			vim.command('silent g/^CamelCase$/d _')

		vim.command('sort')
		vim.command('silent norm ggOWikiStart')

class WikiAttachmentWindow(VimWindow):
	def __init__(self, name = 'WIKIATT_WINDOW'):
		VimWindow.__init__(self, name)

	def on_create(self):
		vim.command('nnoremap <buffer> <cr> :TWGetAttachment CURRENTLINE<cr>')
		vim.command('nnoremap <buffer> :q<cr> :TracNormalView<cr>')
		vim.command('setlocal winwidth=30')
		vim.command('vertical resize 30')
		vim.command('setlocal cursorline')
		vim.command('setlocal linebreak')

########################
# TracWikiUI 
########################
class TracWikiUI(UI):
	""" Trac Wiki User Interface Manager """
	def __init__(self):
		""" Initialize the User Interface """
		self.wikiwindow         = WikiWindow()
		self.tocwindow          = WikiTOContentsWindow()
		self.wiki_attach_window = WikiAttachmentWindow()
		self.mode               = 0 #Initialised to default
		self.sessfile           = "/tmp/trac_vim_saved_session." + str(os.getpid())
		self.winbuf             = {}

	def trac_wiki_mode(self):
		""" change mode to wiki """
		if self.mode == 1: # is wiki mode ?
		  return
		self.mode = 1
		#if self.minibufexpl == 1:
		  #vim.command('CMiniBufExplorer')         # close minibufexplorer if it is open
		# save session
		#vim.command('mksession! ' + self.sessfile)
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
		self.wiki_attach_window.destroy()

	def create(self):
		""" create windows """
		self.tocwindow.create("belowright new")
		self.wikiwindow.create("vertical belowright new")

class TracSearchWindow(VimWindow):
	""" for displaying search results """
	def __init__(self, name = 'SEARCH_WINDOW'):
		VimWindow.__init__(self, name)
	def on_create(self):
		vim.command('nnoremap <buffer> <c-]> :TracWikiView <C-R><C-W><cr>')
		vim.command('nnoremap <buffer> <cr> :python trac_search_view(False)<cr>')
		vim.command('nnoremap <buffer> <space> :python trac_search_view(True)<cr>')
		vim.command('nnoremap <buffer> :q<cr> :TracNormalView<cr>')
		vim.command('setlocal syntax=wiki')
		vim.command('setlocal linebreak')

class TracSearchUI(UI):
	""" Seach UI manager """
	def __init__(self):
		""" Initialize the User Interface """
		self.searchwindow = TracSearchWindow()
		self.mode       = 0 #Initialised to default
		self.sessfile   = "/tmp/trac_vim_saved_session." + str(os.getpid())
		self.winbuf     = {}
		
	def search_mode(self):
		""" Opens Search Window """

		if self.mode == 1: # is wiki mode ?
		  return
		self.mode = 1
		#if self.minibufexpl == 1:
		  #vim.command('CMiniBufExplorer')         # close minibufexplorer if it is open
		# save session
		#vim.command('mksession! ' + self.sessfile)
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
		self.searchwindow.destroy()

	def create(self):
		""" create windows """
		self.searchwindow.create("vertical belowright new")

########################
# TicketWindow Editing Window
########################
class TicketWindow (VimWindow):
	""" Ticket Window """
	def __init__(self, name = 'TICKET_WINDOW'):
		VimWindow.__init__(self, name)
	def on_create(self):
		#vim.command('nnoremap <buffer> <c-]> :python trac_ticket_view("CURRENTLINE") <cr>')
		#vim.command('resize +20')
		vim.command('nnoremap <buffer> :w<cr> :TracSaveTicket<cr>')
		vim.command('nnoremap <buffer> :wq<cr> :TracSaveTicket<cr>:TracNormalView<cr>')
		vim.command('nnoremap <buffer> :q<cr> :TracNormalView<cr>')
		#vim.command('setlocal linebreak')
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

#######################

# TicketTOContentsWindow
########################
class TicketTOContentsWindow (VimWindow):
	""" Ticket Table Of Contents """
	def __init__(self, name = 'TICKETTOC_WINDOW'):
		VimWindow.__init__(self, name)

	def on_create(self):
		vim.command('nnoremap <buffer> <cr> :python trac_ticket_view  ("CURRENTLINE")<cr>')
		vim.command('nnoremap <buffer> :q<cr> :TracNormalView<cr>')
		vim.command('setlocal cursorline')
		vim.command('setlocal linebreak')
		vim.command('setlocal syntax=wiki')
		vim.command('silent norm ggf: <esc>')

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
		#vim.command('mksession! ' + self.sessfile)
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
		""" initialize Trac """

		self.server_list     = server_list
		self.server_url      = server_list.values()[0]

		self.default_comment = comment
		
		self.wiki            = TracWiki(self.server_url)
		self.search          = TracSearch(self.server_url)
		self.ticket          = TracTicket(self.server_url)

		self.ui              = TracWikiUI()
		self.uiserver        = TracServerUI()
		self.uiticket        = TracTicketUI()
		self.uisearch        = TracSearchUI()
		self.user            = self.get_user(self.server_url)


		vim.command('sign unplace *')

	def create_wiki_view(self , page, b_create = False) :
		""" Creates The Wiki View """
		if (page == False):
			page = 'WikiStart'

		self.normal_mode()

		self.ui.trac_wiki_mode()
		self.ui.tocwindow.clean()
		self.ui.tocwindow.write(self.wiki.getAllPages())
		self.ui.wikiwindow.clean()
		self.ui.wikiwindow.write(self.wiki.getPage(page, b_create))

		self.wiki.listAttachments();

		if (self.wiki.current_attachments != []):
			self.ui.wiki_attach_window.create('vertical belowright new')
			self.ui.wiki_attach_window.write("\n".join(self.wiki.current_attachments))

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
			#self.ticket.listAttachments()

		if self.ticket.a_option == []:
			self.ticket.getOptions()

	def create_server_view(self):
		""" Display's The Server list view """

		self.uiserver.server_mode()
		self.uiserver.serverwindow.clean()
		servers = "\n".join(self.server_list.keys())
		self.uiserver.serverwindow.write(servers)
	def set_current_server (self, server_key, quiet = False):
		""" Sets the current server key """	
		self.server_url = self.server_list[server_key]
		self.user = self.get_user(self.server_url)

		self.wiki.setServer(self.server_url)
		self.ticket.setServer(self.server_url)
		self.search.setServer(self.server_url)
		
		self.user = self.get_user(self.server_url)

		if quiet == False:
			print "SERVER SET TO : " + server_key

	def get_user (self, server_url):
		#TODO fix for https
		return re.sub('http://(.*):.*$',r'\1',server_url)

	def normal_mode(self) :
		trac.uiserver.normal_mode()
		trac.ui.normal_mode()
		trac.uiticket.normal_mode()
		trac.uisearch.normal_mode()
#########################
# VIM API FUNCTIONS
#########################
def trac_init():
	''' Initialize Trac Environment '''
	global trac
	global browser

	# get needed vim variables

	comment = vim.eval('tracDefaultComment')
	if comment == '':
		comment = 'VimTrac update'

	server_list = vim.eval('g:tracServerList')

	trac = Trac(comment, server_list)

	browser = vim.eval ('g:tracBrowser')
def trac_wiki_view (name = False, new_wiki = False):
	''' View Wiki Page '''
	global trac

	if name == 'CURRENTLINE':
		name = vim.current.line

	#try: 
	print 'Connecting...'
	trac_normal_view()
	trac.create_wiki_view(name, True)
	print 'Done.'
	#except: 
	#	print "Could not make connection: "   +  "".join(traceback.format_tb( sys.exc_info()[2]))

def trac_normal_view ():
	'''  Back to Normal'''
	global trac
	try:
		trac.uiserver.normal_mode()
		trac.ui.normal_mode()
		trac.uiticket.normal_mode()
		trac.uisearch.normal_mode()

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
	print 'Connecting...'

	if id == 'CURRENTLINE': 
		id = vim.current.line
		if (id.find('Ticket:>>') == -1):
			print "Hit enter on a line containing Ticket:>>"
			return False
		else :
			id = id.replace ('Ticket:>> ' ,'') 
	trac.normal_mode()
	trac.create_ticket_view(id)
	#print 'Done.'
	#except:
	#	print "Could not make connection: "  + "".join(traceback.format_tb( sys.exc_info()[2]))

def trac_server(server_key = '', quiet = False):
	''' View Server Options '''
	global trac

	if server_key == '':
		print "Use Tab completion with :TracServer to cycle through servers"
		#trac.ui.normal_mode()
		#trac.create_server_view()
	else:
		trac.set_current_server(server_key, quiet)
		if quiet == False:
			trac.normal_mode()
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
	""" Adds Comment window comments to the current ticket """
	global trac

	if trac.uiticket.mode == 0 or trac.ticket.current_ticket_id == False:
		print "Cannot make changes when there is no current ticket is open in Ticket View"
		return 0

	comment = trac.uiticket.commentwindow.dump()
	attribs = {}

	if comment == '':
		print "Comment window is empty. Not adding to ticket"

	trac.ticket.updateTicket(comment, attribs, False)
	trac.uiticket.commentwindow.clean()
	trac.create_ticket_view(trac.ticket.current_ticket_id)

def trac_create_ticket(summary = ''):
	""" writes comment window to a new  ticket  """
	global trac

	if trac.uiticket.mode == 0:
		print "Can't create a ticket when not in Ticket View"
		return 0

	description = trac.uiticket.commentwindow.dump()
	attribs = {}

	if description == '' or summary == '':
		print "Comment window and Summary cannot be empty. Not creating ticket"

	trac.ticket.createTicket(description,summary )
	trac.uiticket.commentwindow.clean()
	trac.create_ticket_view(trac.ticket.current_ticket_id)

def trac_search (keyword):
	"""  run a search """
	
	global trac

	trac.normal_mode()
	output_string = trac.search.search(keyword)

	trac.uisearch.search_mode()
	trac.uisearch.searchwindow.clean()
	trac.uisearch.searchwindow.write(output_string)

def trac_add_attachment (file):
	""" add an attachment to current wiki / ticket """
	global trac

	if trac.ui.mode == 1:
		print "Adding attachment to wiki " + trac.wiki.currentPage + '...'
		trac.wiki.addAttachment (file)
		print 'Done.'
	elif trac.uiticket.mode == 1:
		print "Adding attachment to ticket #" + trac.ticket.current_ticket_id + '...'
		trac.ticket.addAttachment (file)
		print 'Done.'
	
	else:
		print "You need an active ticket or wiki open!"

def trac_get_attachment (file):
	''' retrieves attachment '''

	if (file == 'CURRENTLINE'):
		file = vim.current.line 

	if trac.ui.mode == 1:
		print "Retrieving attachment from wiki " + trac.wiki.currentPage + '...'
		trac.wiki.getAttachment (file)
		print 'Done.'
	elif trac.uiticket.mode == 1:
		print "Retrieving attachment from ticket #" + trac.ticket.current_ticket_id + '...'
		trac.ticket.getAttachment (file)
		print 'Done.'
	else:
		print "You need an active ticket or wiki open!"

def trac_list_attachments():

	global trac

	if trac.ui.mode == 1:
		option = trac.wiki.current_attachments
		print trac.wiki.current_attachments
	elif trac.uiticket.mode == 1:
		option = trac.ticket.current_attachments
	else:
		print "You need an active ticket or wiki open!"
	
	vim.command ('let g:tracOptions = "' + "|".join (option) + '"')

def trac_window_resize():

	global mode
	mode = mode + 1
	if mode >= 3:
		mode = 0

	if mode == 0:
		vim.command("wincmd =")
	elif mode == 1:
		vim.command("wincmd |")
	if mode == 2:
		vim.command("wincmd _")

def trac_open_browser(page):

	global browser

	#basedir = trac.wiki.server_url.replace('login/xmlrpc', '')

	basedir = re.sub('^(.*)@(.*)/login/xmlrpc$', r'\2',trac.wiki.server_url)

	print 'Opening page with ' + '!' + browser +" " +  basedir + '/wiki/'+ page

	vim.command ('!' + browser +" " + basedir + '/wiki/'+ page);

def trac_preview (b_dump = False):
	''' browser view of current wiki buffer '''
	global browser

	if trac.ui.mode == 1:
		print "Retrieving preview from wiki " + trac.wiki.currentPage + '...'
		wikitext = trac.ui.wikiwindow.dump()
	elif trac.uiticket.mode == 1:
		print "Retrieving preview from ticket #" + trac.ticket.current_ticket_id + '...'
		wikitext = trac.uiticket.commentwindow.dump()
	else:
		print "You need an active ticket or wiki open!"
		return False

	html = '<html><body>' + trac.wiki.getWikiHtml (wikitext) +  '</body></html>'

	file_name = vim.eval ('g:tracTempHtml') 

	fp = open(file_name , 'w')
	fp.write (html)	
	fp.close()

	
	if b_dump == True:
		trac.normal_mode()
		vim.command ('split')
		vim.command ('enew')
		vim.command ('r!lynx -dump ' + file_name );
		vim.command ('set ft=text');
	else:
		vim.command ('!' + browser +" file://" + file_name);	

def trac_html_view(page = False):
	
	global browser

	if page == False:
		page = vim.current.line

	html = '<html><body>' + trac.wiki.getPageHtml (page) +  '</body></html>'

	file_name = vim.eval ('g:tracTempHtml') 

	fp = open(file_name , 'w')
	fp.write (html)	
	fp.close()

	vim.command ('!' + browser +" file://" + file_name);	

def trac_search_view(b_preview):
	line = vim.current.line

	if (line.find('Ticket:>> ') != -1):
		trac_ticket_view(line.replace('Ticket:>> ', ''))

	elif (line.find('Wiki:>> ')!= -1):
		if b_preview == False:
			trac_wiki_view(line.replace('Wiki:>> ', ''))
		else:
			trac_html_view(line.replace('Wiki:>> ', ''))

	elif (line.find('Changeset:>> ')!= -1):
		trac_changeset_view(line.replace('Changeset:>> ', ''))

def trac_changeset_view(changeset, b_full_path = False):
	global trac
	if b_full_path == True:
		changeset = trac.wiki.server_url.replace('login/xmlrpc' , 'changeset/' + changeset)

	trac.normal_mode()
	vim.command ('split')
	vim.command ('enew')
	vim.command("setlocal buftype=nofile")
	vim.command ('Nread ' + changeset + '?format=diff');
	vim.command ('set ft=diff');
