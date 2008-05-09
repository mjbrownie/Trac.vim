import os
import sys
import vim
#import traceback
import xmlrpclib
import re
########################
# RPC Base Class 
########################
class TracRPC:
    def __init__ (self, server_url):
        self.server_url = server_url
        self.server = xmlrpclib.ServerProxy(server_url)
        self.multicall = xmlrpclib.MultiCall(self.server)
    def setServer (self, url):
        self.server_url = url
        self.server = xmlrpclib.ServerProxy(url)
########################
# User Interface Base Classes 
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

    def write(self, msg):
        """ append last """
        self.prepare()
        if self.firstwrite == 1:
          self.firstwrite = 0
          msg = msg.encode('ascii', 'ignore')
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
class UI:
    """ User Interface Base Class """
    def __init__(self):
        """ Initialize the User Interface """

    def open(self):
        """ change mode to wiki """
        if self.mode == 1: # is wiki mode ?
          return
        self.mode = 1
        self.create()
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

        #self.winbuf.clear()
        self.file    = None
        self.line    = None
        self.mode    = 0
        self.cursign = None
########################
# Wiki Module
########################
class TracWiki(TracRPC):
    """ Trac Wiki Class """
    def __init__ (self, server_url):
        TracRPC.__init__(self, server_url)
        self.a_pages = []
    def getAllPages(self):
        """ Gets a List of Wiki Pages """
        self.a_pages = self.server.wiki.getAllPages()
        return "\n".join(self.a_pages)
    def getPage(self, name, b_create = False):
        """ Get Wiki Page """
        global trac

        self.currentPage = name
        try:
            wikitext = self.server.wiki.getPage(name)
        except:
            wikitext = "Describe " + name + " here."
            if b_create == True:
                try:
                    self.server.wiki.putPage(name, wikitext, {"comment" : "Initializing"})
                    return wikitext
                except:
                    print "Could not create page " + name
            else:
                print "Could not find page " + name + ". Use :TWCreate " + name+ " to create it"
                return False
        return wikitext 
    def save (self,  comment):
        """ Saves a Wiki Page """
        global trac

        if comment == '':
            comment = trac.default_comment
        self.server.wiki.putPage(self.currentPage, trac.uiwiki.wikiwindow.dump() , {"comment" : comment})
        
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
    def html_view(self, page):
        global browser

        if page == False:
            page = vim.current.line

        html = '<html><body>' + self.server.wiki.getPageHTML(page)+  '</body></html>'

        file_name = vim.eval ('g:tracTempHtml') 

        fp = open(file_name , 'w')
        fp.write (html) 
        fp.close()

        vim.command ('!' + browser +" file://" + file_name)    
    def get_options (self):
        vim.command ('let g:tracOptions = "' + "|".join (self.a_pages) + '"')

class TracWikiUI(UI):
    """ Trac Wiki User Interface Manager """
    def __init__(self):
        """ Initialize the User Interface """
        self.wikiwindow         = WikiWindow()
        self.tocwindow          = WikiTOContentsWindow()
        self.wiki_attach_window = WikiAttachmentWindow()
        self.mode               = 0 #Initialised to default
        #self.winbuf             = {}
    def destroy(self):
        """ destroy windows """
        self.wikiwindow.destroy()
        self.tocwindow.destroy()
        self.wiki_attach_window.destroy()

        vim.command ("call UnloadWikiCommands()")
        
    def create(self):
        """ create windows  and load the internal Commands """
        
        vim.command ("call LoadWikiCommands()")
        style = vim.eval ('g:tracWikiStyle') 
        
        if style == 'full':
            #vim.command('enew')
            self.wikiwindow.create('new')
            vim.command ("only")
            self.tocwindow.create("vertical aboveleft new")
            return False
        if style == 'top':
            self.wikiwindow.create("aboveleft new")
            self.tocwindow.create("vertical aboveleft new")
            return False
        self.tocwindow.create("belowright new")
        self.wikiwindow.create("vertical belowright new")
class WikiWindow (VimWindow):
    """ Wiki Window """
    def __init__(self, name = 'WIKI_WINDOW'):
        VimWindow.__init__(self, name)
    def on_create(self):
        vim.command('nnoremap <buffer> <c-]> :python trac.wiki_view ("<C-R><C-W>")<cr>')
        vim.command('nnoremap <buffer> :q<cr> :python trac.normal_view()<cr>')
        vim.command('nnoremap <buffer> :wq<cr> :python trac.save_wiki('')<cr>:python trac.normal_view()<cr>')
        #map gf to a new buffer (switching buffers doesnt work with nofile)
        vim.command('nnoremap <buffer> gf <c-w><c-f><c-w>K')
        vim.command('vertical resize +70')
        vim.command('nnoremap <buffer> :w<cr> :TWSave')
        vim.command('setlocal syntax=wiki')
        vim.command('setlocal linebreak')
        vim.command('setlocal noswapfile')
class WikiTOContentsWindow (VimWindow):
    """ Wiki Table Of Contents """
    def __init__(self, name = 'WIKITOC_WINDOW'):
        VimWindow.__init__(self, name)

        if vim.eval('tracHideTracWiki') == 'yes':
            self.hide_trac_wiki = True
        else:
            self.hide_trac_wiki = False

    def on_create(self):
        vim.command('nnoremap <buffer> <cr> :python trac.wiki_view("CURRENTLINE")<cr>')
        vim.command('nnoremap <buffer> <Space> :python trac.html_view ()<cr><cr><cr>')
        vim.command('nnoremap <buffer> :q<cr> :python trac.normal_view()<cr>')
        vim.command('setlocal winwidth=30')
        vim.command('vertical resize 30')
        vim.command('setlocal cursorline')
        vim.command('setlocal linebreak')
        vim.command('setlocal noswapfile')

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
        vim.command('nnoremap <buffer> <cr> :python trac.get_attachment("CURRENTLINE")<cr>')
        vim.command('nnoremap <buffer> :q<cr> :python trac.normal_view()<cr>')
        vim.command('setlocal winwidth=30')
        vim.command('vertical resize 30')
        vim.command('setlocal cursorline')
        vim.command('setlocal linebreak')
        vim.command('setlocal noswapfile')
########################
# Search Module
########################
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
            
            if search[0].find('/ticket/') != -1: 
                str_result += "\nTicket:>> " + os.path.basename (search[0])+ "\n    "
            if search[0].find('/wiki/')!= -1: 
                str_result += "\nWiki:>> " + os.path.basename(search[0]) + "\n    "
            if search[0].find('/changeset/')!= -1: 
                str_result += "\nChangeset:>> " + search[0]  + "\n    " #os.path.basename(search[0])
            str_result += "\n    ".join (search[4].strip().split("\n")) + "\n" 
            str_result += "\n-------------------------------------------------"

        return str_result

class TracSearchUI(UI):
    """ Seach UI manager """
    def __init__(self):
        """ Initialize the User Interface """
        self.searchwindow = TracSearchWindow()
        self.mode       = 0 #Initialised to default
        #self.winbuf     = {}
    def destroy(self):
        """ destroy windows """
        self.searchwindow.destroy()
    def create(self):
        """ create windows """
        style = vim.eval ('g:tracSearchStyle') 
        if style == 'right':
            self.searchwindow.create("vertical belowright new")
        else:
            self.searchwindow.create("vertical aboveleft new")
class TracSearchWindow(VimWindow):
    """ for displaying search results """
    def __init__(self, name = 'SEARCH_WINDOW'):
        VimWindow.__init__(self, name)
    def on_create(self):
        vim.command('nnoremap <buffer> <c-]> :python trac.wiki_view ("<cword>")<cr>')
        vim.command('nnoremap <buffer> <cr> :python trac.search_open(False)<cr>')
        #vim.command('nnoremap <buffer> <space> :python trac.search_open(True)<cr>') This messes folds
        vim.command('nnoremap <buffer> :q<cr> :python trac.normal_view()<cr>')
        vim.command('setlocal syntax=text')
        vim.command('setlocal foldmethod=indent')
        vim.command('setlocal linebreak')
        vim.command('setlocal noswapfile')

    def on_write (self):
        #Basic Highlighting
        vim.command('syntax reset')
        vim.command('syn match Keyword /\w*:>> .*$/ contains=Title')
        vim.command('syn match Title /\w*:>>/ contained')
        #vim.command('highlight Title ctermbg=255 guibg=255')
        vim.command('syn match SpecialKey /^-*$/')

########################
# Ticket Module
########################
class TracTicket(TracRPC):
    """ Trac Ticket Class """
    def __init__ (self, server_url):
        TracRPC.__init__(self, server_url)
        
        self.current_ticket_id = False
        self.a_option = []
        self.a_tickets = []
        self.filter = TracTicketFilter()

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
    def getAllTickets(self,owner, b_use_cache = False):
        """ Gets a List of Ticket Pages """
        
        if self.a_option == []:
            self.getOptions()
        
        if b_use_cache:
            tickets = self.a_tickets
        else:
            multicall = xmlrpclib.MultiCall(self.server)
            #for ticket in self.server.ticket.query("owner=" + owner):
            for ticket in self.server.ticket.query():
                multicall.ticket.get(ticket)
            tickets = multicall()
            self.a_tickets = tickets

        ticket_list = "(Hit <enter> or <space> on a line containing Ticket:>>)\n"

        if self.filter.filters != []:
            ticket_list += "(filtered)\n"
            i = 1
            ticket_list += self.filter.list()

        milestone = ''

        for ticket in tickets:
            

            if ticket[3]["status"] != "closed" and self.filter.check(ticket):
                str_ticket = ''

                #This wont work without ordering
                #last_milestone = ticket[3]["milestone"]
                #if milestone !=  last_milestone and last_milestone != '':
                    #milestone = ticket[3]["milestone"]
                    #str_ticket += "\n--------------------------------------------" + "\n"
                    #str_ticket += 'MILESTONE: ' + milestone + "\n"
                    #str_ticket += "--------------------------------------------" + "\n"

                str_ticket += "\nTicket:>> "      + str(ticket[0])        + "\n"
                str_ticket += " * Summary: "      + ticket[3]["summary"]  + "\n"
                str_ticket += "     * Priority: " + ticket[3]["priority"] + "\n"
                str_ticket += "     * Status: "   + ticket[3]["status"]   + "\n"
                milestone =  ticket[3]["milestone"] 
                if (milestone == ''):
                    milestone = 'NOMILESTONE'
                component =  ticket[3]["component"] 
                if (component == ''):
                    component = 'NOCOMPONENT'
                str_ticket += "     * Component: " + component          + "\n"
                str_ticket += "     * Milestone: " + milestone          + "\n"
                str_ticket += "     * Type: "      + ticket[3]["type"]  + "\n"
                str_ticket += "     * Owner: "     + ticket[3]["owner"] + "\n    "
                
                if self.session_is_present(ticket[0]):
                    str_ticket += "     * Session: PRESENT \n"
                str_ticket += "\n    ".join (ticket[3]["description"].strip().split("\n")) + "\n" 
                
                str_ticket += "--------------------------------------------"

                ticket_list += str_ticket

        ticket_list += "\n"
        return ticket_list
    def getTicket(self, id):
        """ Get Ticket Page """
        self.current_ticket_id = id

        ticket =  self.server.ticket.get(id)

        self.listAttachments()

        ticket_changelog = self.server.ticket.changeLog(id)

        #ticket_options = self.server.ticket.getAvailableActions(id)

        str_ticket = "= Ticket Summary =\n\n"
        str_ticket += "*   Ticket ID: " + str(ticket[0])         + "\n"
        str_ticket += "*       Owner: " + ticket[3]["owner"]     + "\n"
        str_ticket += "*      Status: " + ticket[3]["status"]    + "\n"
        str_ticket += "*     Summary: " + ticket[3]["summary"]   + "\n"
        str_ticket += "*        Type: " + ticket[3]["type"]      + "\n"
        str_ticket += "*    Priority: " + ticket[3]["priority"]  + "\n"
        str_ticket += "*   Component: " + ticket[3]["component"] + "\n"
        str_ticket += "*   Milestone: " + ticket[3]["milestone"] + "\n"
        #look for session files 
        
        if self.session_is_present():
            str_ticket += "*     Session: PRESENT \n"
        else:
            str_ticket += "*     Session: not present\n"

        str_ticket += "* Attachments: " + "\n"
        for attach in self.current_attachments:
            str_ticket += '               ' + attach

        str_ticket += "\n---------------------------------------------------\n" 
        str_ticket += "= Description: =\n\n    " 
        str_ticket += "\n    ".join (ticket[3]["description"].strip().split("\n")) + "\n" 
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
                    str_ticket += "      (" + change[1]  + ": comment)\n    "
                    str_ticket += "\n    ".join (change[4].strip().split("\n")) + "\n" 
                    #str_ticket += change[4] + "\n\n"
                elif change[2] == 'milestone':
                    str_ticket += "      (" + change[1] + ": milestone set to " + change[4] + ")\n\n"
                else :
                    str_ticket += "      (" + change[1] + ": " + change[2] + " set to " + change[4] + ")\n\n"

        return str_ticket
    def updateTicket(self, comment, attribs = {}, notify = False):
        """ add ticket comments change attributes """
        return self.server.ticket.update(self.current_ticket_id,comment,attribs,notify)
    def createTicket (self, description, summary, attributes = {}):
        """ create a trac ticket """


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
    def get_options(self,op_id):
        vim.command ('let g:tracOptions = "' + "|".join (self.a_option[op_id]) + '"')
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
    def set_attr (self,option,value):
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
        trac.ticket_view(trac.ticket.current_ticket_id, True)
    def add_comment(self):
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
        trac.ticket_view(trac.ticket.current_ticket_id)
    def update_description(self):
        """ Adds Comment window as a description to the current ticket """
        global trac
        
        confirm = vim.eval('confirm("Overwrite Description?", "&Yes\n&No\n",2)') 
        if int (confirm) == 2:
            print "Cancelled."
            return False

        if trac.uiticket.mode == 0 or trac.ticket.current_ticket_id == False:
            print "Cannot make changes when there is no current ticket is open in Ticket View"
            return 0

        comment = trac.uiticket.commentwindow.dump()
        attribs = {'description': comment}

        if comment == '':
            print "Comment window is empty. Not adding to ticket"

        trac.ticket.updateTicket('', attribs, False)
        trac.uiticket.commentwindow.clean()
        trac.ticket_view(trac.ticket.current_ticket_id)
    def create(self, summary = 'new ticket', type = False, server = False): 
        """ writes comment window to a new  ticket  """
        global trac

        #Used in quick tickets
        if server != False:
            trac.set_current_server(server,True, 'ticket')
            description = ''
        else:
            description = trac.uiticket.commentwindow.dump()


        if trac.uiticket.mode == 0 and server == False:
            print "Can't create a ticket when not in Ticket View"
            return 0

        confirm = vim.eval('confirm("Create Ticket on ' + trac.server_name + '?", "&Yes\n&No\n",2)') 
        if int (confirm) == 2:
            print "Cancelled."
            return False

        if type == False:
            attribs = {}
        else:
            attribs = {'type':type}

        if description == '' :
            print "Description is empty. Ticket needs more info"

        trac.ticket.createTicket(description,summary , attribs)
        trac.uiticket.commentwindow.clean()
        trac.ticket_view(trac.ticket.current_ticket_id)
    def close_ticket(self, comment):
        self.updateTicket(comment, {'status': 'closed'})
    def session_save (self):
        global trac

        if self.current_ticket_id == False:
            print "You need to have an active ticket"
            return False

        directory = vim.eval('g:tracSessionDirectory')   
        if os.path.isfile(directory) != False:
            print "Cant create session directory"
            return False
        
        if os.path.isdir(directory) == False: 
            os.mkdir(directory)

        serverdir = re.sub (r'[^\w]', '', trac.server_name)

        if os.path.isdir(directory +  '/' + serverdir) == False:
            os.mkdir(directory + '/' + serverdir)

        sessfile = directory + '/' + serverdir + "/vimsess." + str(self.current_ticket_id)
        vim.command('mksession! ' + sessfile )
        print "Session file Created: " + sessfile
    def session_load (self):
        global trac
        if self.current_ticket_id == False:
            print "You need to have an active ticket"
            return False

        serverdir = re.sub (r'[^\w]', '', trac.server_name)
        directory = vim.eval('g:tracSessionDirectory')   
        sessfile = directory + '/' + serverdir + "/vimsess." + str(self.current_ticket_id)

        if os.path.isfile(sessfile) == False:
            print "This ticket does not have a session: " + sessfile
            return False
            

        vim.command("bdelete TICKETTOC_WINDOW")
        vim.command("bdelete TICKET_WINDOW")
        vim.command("bdelete TICKET_COMMENT_WINDOW")
        vim.command('source ' + sessfile )
        vim.command("bdelete TICKETTOC_WINDOW")
        vim.command("bdelete TICKET_WINDOW")
        vim.command("bdelete TICKET_COMMENT_WINDOW")
        trac.ticket_view(self.current_ticket_id)
    def get_session_file(self, id = False):
        global trac

        if id == False:
            id = self.current_ticket_id

        directory = vim.eval('g:tracSessionDirectory')   
        serverdir = re.sub (r'[^\w]', '', trac.server_name)

        return directory + '/' + serverdir + "/vimsess." + str (id)
    def session_is_present(self, id = False):
        sessfile = self.get_session_file(id) 
        return  os.path.isfile(sessfile) 
    def set_summary(self, summary):
        confirm = vim.eval('confirm("Overwrite Summary?", "&Yes\n&No\n",2)') 
        if int (confirm) == 2:
            print "Cancelled."
            return False

        attribs = {'summary': summary}
        trac.ticket.updateTicket('', attribs, False)
        

class TracTicketFilter:
    def __init__(self):
        self.filters = []
    def add (self,  keyword,attribute, b_whitelist = True, b_refresh_ticket = True):
        self.filters.append({'attr':attribute,'key':keyword,'whitelist':b_whitelist}) 
        if b_refresh_ticket == True:
            self.refresh_tickets()
    def clear(self):
        self.filters = []
        self.refresh_tickets()
    def delete (self, number):
        number = int(number)
        try: 
            del self.filters[number -1]
        except:
            return False
        self.refresh_tickets()
    def list (self):
        if self.filters == []:
            return ''

        i = 0 
        str_list = ""
        for filter in self.filters:
            i+=1
            is_whitelist = 'whitelist'
            if (filter['whitelist'] == False):
                is_whitelist = 'blacklist'
            str_list +=  '    ' + str(i) + '. ' + filter['attr'] + ': ' + filter['key'] + " : " + is_whitelist + "\n"

        return str_list
    def check (self, ticket):
        for filter in self.filters:
            if ticket[3][filter['attr']] == filter['key']:
                if filter['whitelist'] == False:
                    return False
            else:
                if filter['whitelist'] == True:
                    return False
        return True
    def refresh_tickets(self):
        global trac
        trac.ticket_view(trac.ticket.current_ticket_id, True)
class TracTicketUI (UI):
    """ Trac Wiki User Interface Manager """
    def __init__(self):
        """ Initialize the User Interface """
        self.ticketwindow  = TicketWindow()
        self.tocwindow     = TicketTOContentsWindow()
        self.commentwindow = TicketCommentWindow()
        self.mode          = 0 #Initialised to default
    def destroy(self):
        """ destroy windows """
        
        vim.command ("call UnloadTicketCommands()")

        self.ticketwindow.destroy()
        self.tocwindow.destroy()
        self.commentwindow.destroy()
    def create(self):
        """ create windows """
        style = vim.eval ('g:tracTicketStyle') 
        if style == 'right':
            self.tocwindow.create("vertical belowright new")
            self.ticketwindow.create("belowright new")
            self.commentwindow.create("belowright new")
        elif style == 'left':
            self.commentwindow.create("vertical aboveleft new")
            self.ticketwindow.create("aboveleft new")
            self.tocwindow.create(" aboveleft new")
        elif style == 'top':
            self.commentwindow.create("aboveleft new")
            self.ticketwindow.create("vertical aboveleft new")
            self.tocwindow.create("vertical aboveleft new")
        elif style == 'bottom':
            self.tocwindow.create("belowright new")
            self.ticketwindow.create("vertical belowright new")
            self.commentwindow.create("vertical belowright new")
        else:
            self.tocwindow.create("belowright new")
            vim.command('only')
            self.ticketwindow.create("vertical  belowright 110 new")
            self.commentwindow.create("belowright 15 new")

        vim.command ("call LoadTicketCommands()")
class TicketWindow (VimWindow):
    """ Ticket Window """
    def __init__(self, name = 'TICKET_WINDOW'):
        VimWindow.__init__(self, name)
    def on_create(self):
        vim.command('setlocal noswapfile')
        #vim.command('nnoremap <buffer> <c-]> :python trac_ticket_view("CURRENTLINE") <cr>')
        #vim.command('resize +20')
        #vim.command('nnoremap <buffer> :w<cr> :TracSaveTicket<cr>')
        #vim.command('nnoremap <buffer> :wq<cr> :TracSaveTicket<cr>:TracNormalView<cr>')
        vim.command('nnoremap <buffer> :q<cr> :python trac.normal_view()<cr>')
        #vim.command('setlocal linebreak')
        vim.command('setlocal syntax=wiki')
class TicketCommentWindow (VimWindow):
    """ For adding Comments to tickets """
    def __init__ (self,name = 'TICKET_COMMENT_WINDOW'):
        VimWindow.__init__(self, name)

    def on_create(self):
        vim.command('nnoremap <buffer> :w<cr> :python trac.add_comment()<cr>')
        vim.command('nnoremap <buffer> :wq<cr> :python trac.add_comment()<cr>:python trac.normal_view()<cr>')
        vim.command('nnoremap <buffer> :q<cr> :python trac.normal_view()<cr>')
        vim.command('setlocal syntax=wiki')
        vim.command('setlocal noswapfile')
class TicketTOContentsWindow (VimWindow):
    """ Ticket Table Of Contents """
    def __init__(self, name = 'TICKETTOC_WINDOW'):
        VimWindow.__init__(self, name)

    def on_create(self):
        vim.command('nnoremap <buffer> <cr> :python trac.ticket_view  ("CURRENTLINE")<cr>')
        vim.command('nnoremap <buffer> :q<cr> :python trac.normal_view()<cr>')
        vim.command('setlocal cursorline')
        vim.command('setlocal linebreak')
        vim.command('setlocal syntax=wiki')
        vim.command('setlocal foldmethod=indent')
        vim.command('setlocal nowrap')
        vim.command('silent norm ggf: <esc>')
        vim.command('setlocal noswapfile')
#########################
# Trac Server (UI Not Implemented)
#########################
class TracServerUI (UI):
    """ Server User Interface View """
    def __init__(self):
        self.serverwindow = ServerWindow()
        self.mode       = 0 #Initialised to default
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
        vim.command('nnoremap <buffer> :q<cr> :python trac.normal_view()<cr>')
########################
# Timeline Module
########################
class TracTimeline:
    def read_timeline(self):
        """ Call the XML Rpc list """
        global trac 
        try: 
            import feedparser
        except ImportError: 
            print "Please install feedparser.py!"
            return False;

        from time import strftime
        import re

        feed = trac.wiki.server_url.replace('login/xmlrpc' , 'timeline?ticket=on&changeset=on&wiki=on&max=50&daysback=90&format=rss')
        d = feedparser.parse(feed)
        str_feed = "(Hit <enter> or <space >on a line containing Ticket:>>)\n"
        str_feed += "(feed: " + feed + ")\n\n"
        for item in d['items']:

            #Each item is a dictionary mapping properties to values
            str_feed +=  "Update: "  + strftime("%Y-%m-%d %H:%M:%S", item.updated_parsed ) + "\n"

            m = re.match(r"^Ticket #(\d+) (.*)$", item.title) 
            if m != None: 
                str_feed += "Ticket:>> " + m.group(1) + "\n" 
                str_feed += m.group(2) + "\n"
            m = re.match(r"^([\w\d]+) (edited by .*)$", item.title)
            if m != None: 
                str_feed += "Wiki:>> " + m.group(1) + "\n"
                str_feed += m.group(2) + "\n"
            m = re.match(r"^Changeset \[([\d]+)\]: (.*)$", item.title) 
            if m != None: 
                str_feed += "Changeset:>> " + m.group(1) + "\n"
                str_feed += m.group(2) + "\n"

            str_feed +=  "Link: "    + item.link + "\n"
            str_feed += '-----------------------------------------------------------------' + "\n"

        return str_feed

class TracTimelineUI(UI):
    """ UI Manager for Timeline View """
    def __init__(self):
        self.timeline_window = TracTimelineWindow()
        self.mode  = 0
    def create (self):
       style = vim.eval ('g:tracTimelineStyle') 

       if style == 'right':
           self.timeline_window.create("vertical belowright new")
       elif style == 'bottom':
           self.timeline_window.create("belowright new")
       else:
           self.timeline_window.create("vertical aboveleft new")
    def destroy (self):
        self.timeline_window.destroy()
class TracTimelineWindow(VimWindow):
    """ RSS Feed Window """

    def __init__(self, name = 'TIMELINE_WINDOW'):
        VimWindow.__init__(self, name)
    def on_create(self):
        vim.command('nnoremap <buffer> <c-]> :python trac.wiki_view("<cword>")<cr>')
        vim.command('nnoremap <buffer> :q<cr> :python trac.normal_view()<cr>')
        #vim.command('vertical resize +70')
        vim.command('setlocal syntax=wiki')
        vim.command('setlocal linebreak')
        vim.command('nnoremap <buffer> <cr> :python trac.search_open(False)<cr>')
        vim.command('nnoremap <buffer> <space> :python trac.search_open(True)<cr>')
        vim.command('setlocal noswapfile')
#########################
# Main Class
#########################
class Trac:
    """ Main Trac class """
    def __init__ (self, comment , server_list):
        """ initialize Trac """

        self.server_list     = server_list
        self.server_url      = server_list.values()[0]
        self.server_name     = server_list.keys()[0]

        self.default_comment = comment
        
        self.wiki            = TracWiki(self.server_url)
        self.search          = TracSearch(self.server_url)
        self.ticket          = TracTicket(self.server_url)
        self.timeline        = TracTimeline()

        self.uiwiki          = TracWikiUI()
        self.uiserver        = TracServerUI()
        self.uiticket        = TracTicketUI()
        self.uisearch        = TracSearchUI()
        self.uitimeline      = TracTimelineUI()

        self.user            = self.get_user(self.server_url)

        vim.command('sign unplace *')
    def wiki_view(self , page = 'WikiStart', b_create = False) :
        """ Creates The Wiki View """
        if page == 'CURRENTLINE':
            page = vim.current.line

        print 'Connecting...'
        self.normal_view()

        if (page == False):
            page = 'WikiStart'

        self.normal_view()

        self.uiwiki.open()
        self.uiwiki.tocwindow.clean()
        self.uiwiki.tocwindow.write(self.wiki.getAllPages())
        self.uiwiki.wikiwindow.clean()
        self.uiwiki.wikiwindow.write(self.wiki.getPage(page, b_create))

        self.wiki.listAttachments();

        if (self.wiki.current_attachments != []):
            self.uiwiki.wiki_attach_window.create('vertical belowright new')
            self.uiwiki.wiki_attach_window.write("\n".join(self.wiki.current_attachments))

    def ticket_view(self ,id = False, b_use_cache = False) :
        """ Creates The Ticket View """

        print 'Connecting...'

        if id == 'CURRENTLINE': 
            id = vim.current.line
            if (id.find('Ticket:>>') == -1):
                print "Hit enter on a line containing Ticket:>>"
                return False
            else :
                id = id.replace ('Ticket:>> ' ,'') 
        self.normal_view()
        self.uiticket.open()
        self.uiticket.tocwindow.clean()
        self.uiticket.tocwindow.write(self.ticket.getAllTickets(self.user, b_use_cache))
        self.uiticket.ticketwindow.clean()
        if (id == False):
            self.uiticket.ticketwindow.write("Select Ticket To Load")
            #This sets the cursor to the TOC if theres no active ticket
            vim.command("wincmd h")
        else:
            self.uiticket.ticketwindow.write(self.ticket.getTicket(id))
            #self.ticket.listAttachments()

        if self.ticket.a_option == []:
            self.ticket.getOptions()
    def server_view(self):
        """ Display's The Server list view """
        self.uiserver.server_mode()
        self.uiserver.serverwindow.clean()
        servers = "\n".join(self.server_list.keys())
        self.uiserver.serverwindow.write(servers)
    def search_open(self,keyword, b_preview = False):
        line = vim.current.line

        if (line.find('Ticket:>> ') != -1):
            self.ticket_view(line.replace('Ticket:>> ', ''))

        elif (line.find('Wiki:>> ')!= -1):
            if b_preview == False:
                self.wiki_view(line.replace('Wiki:>> ', ''))
            else:
                self.html_view(line.replace('Wiki:>> ', ''))

        elif (line.find('Changeset:>> ')!= -1):
            self.changeset_view(line.replace('Changeset:>> ', ''))
    def search_view (self, keyword):
        """  run a search """
        self.normal_view()
        output_string = self.search.search(keyword)
        self.uisearch.open()
        self.uisearch.searchwindow.clean()
        self.uisearch.searchwindow.write(output_string)
    def timeline_view(self):
        self.normal_view()
        output_string = self.timeline.read_timeline()
        self.uitimeline.open()
        self.uitimeline.timeline_window.clean()
        self.uitimeline.timeline_window.write((output_string))
    def set_current_server (self, server_key, quiet = False, view = False):
        """ Sets the current server key """ 

        self.server_url = self.server_list[server_key]
        self.server_name = server_key
        self.user = self.get_user(self.server_url)

        self.wiki.setServer(self.server_url)
        self.ticket.setServer(self.server_url)
        self.search.setServer(self.server_url)
        
        self.user = self.get_user(self.server_url)

        trac.normal_view()

        if quiet == False:
            print "SERVER SET TO : " + server_key
           
            #Set view to default or custom
            if view == False:
                view = vim.eval ('g:tracDefaultView') 

            { 'wiki'   : self.wiki_view,
            'ticket'   : self.ticket_view,
            'timeline' : self.timeline_view
            } [view]()
    def get_user (self, server_url):
        #TODO fix for https
        return re.sub('http://(.*):.*$',r'\1',server_url)
    def normal_view(self) :
        trac.uiserver.normal_mode()
        trac.uiwiki.normal_mode()
        trac.uiticket.normal_mode()
        trac.uisearch.normal_mode()
        trac.uitimeline.normal_mode()
    def add_attachment (self, file):
        """ add an attachment to current wiki / ticket """

        if self.uiwiki.mode == 1:
            print "Adding attachment to wiki " + self.wiki.currentPage + '...'
            self.wiki.addAttachment (file)
            print 'Done.'
        elif self.uiticket.mode == 1:
            print "Adding attachment to ticket #" + self.ticket.current_ticket_id + '...'
            self.ticket.addAttachment (file)
            print 'Done.'
        
        else:
            print "You need an active ticket or wiki open!"
    def get_attachment (self, file):
        ''' retrieves attachment '''

        if (file == 'CURRENTLINE'):
            file = vim.current.line 

        if self.uiwiki.mode == 1:
            print "Retrieving attachment from wiki " + self.wiki.currentPage + '...'
            self.wiki.getAttachment (file)
            print 'Done.'
        elif self.uiticket.mode == 1:
            print "Retrieving attachment from ticket #" + self.ticket.current_ticket_id + '...'
            self.ticket.getAttachment (file)
            print 'Done.'
        else:
            print "You need an active ticket or wiki open!"
    def list_attachments(self):
        if self.uiwiki.mode == 1:
            option = self.wiki.current_attachments
            print self.wiki.current_attachments
        elif self.uiticket.mode == 1:
            option = self.ticket.current_attachments
        else:
            print "You need an active ticket or wiki open!"
        
        vim.command ('let g:tracOptions = "' + "|".join (option) + '"')
    def preview (self, b_dump = False):
        ''' browser view of current wiki buffer '''
        global browser

        if self.uiwiki.mode == 1:
            print "Retrieving preview from wiki " + self.wiki.currentPage + '...'
            wikitext = self.uiwiki.wikiwindow.dump()
        elif self.uiticket.mode == 1:
            print "Retrieving preview from ticket #" + self.ticket.current_ticket_id + '...'
            wikitext = self.uiticket.commentwindow.dump()
        else:
            print "You need an active ticket or wiki open!"
            return False

        html = '<html><body>' + self.wiki.getWikiHtml (wikitext) +  '</body></html>'

        file_name = vim.eval ('g:tracTempHtml') 

        fp = open(file_name , 'w')
        fp.write (html) 
        fp.close()

        
        if b_dump == True:
            #self.normal_view()
            #vim.command ('split')
            vim.command ('enew')
            vim.command ('setlocal buftype=nofile')
            vim.command ('r!lynx -dump ' + file_name );
            vim.command ('set ft=text');
            vim.command ('norm gg');
        else:
            vim.command ('!' + browser +" file://" + file_name);    
    def changeset_view(self, changeset, b_full_path = False):
        #if b_full_path == True:
        changeset = self.wiki.server_url.replace('login/xmlrpc' , 'changeset/' + changeset)

        self.normal_view()
        vim.command ('belowright split')
        vim.command ('enew')
        vim.command("setlocal buftype=nofile")
        vim.command ('silent Nread ' + changeset + '?format=diff');
        vim.command ('set ft=diff');
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
