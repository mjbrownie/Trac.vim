" Trac client: A interface to a Trac Wiki Repository
"
" Script Info and Documentation  {{{
"=============================================================================
"    Copyright: Copyright (C) 2008 Michael Brown
"      License:	The MIT License
"				
"				Permission is hereby granted, free of charge, to any person obtaining
"				a copy of this software and associated documentation files
"				(the "Software"), to deal in the Software without restriction,
"				including without limitation the rights to use, copy, modify,
"				merge, publish, distribute, sublicense, and/or sell copies of the
"				Software, and to permit persons to whom the Software is furnished
"				to do so, subject to the following conditions:
"				
"				The above copyright notice and this permission notice shall be included
"				in all copies or substantial portions of the Software.
"				
"				THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
"				OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
"				MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
"				IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
"				CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
"				TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
"				SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
" Name Of File: trac.vim , trac.py
"  Description: Wiki Client to the Trac Project Manager (trac.edgewall.org)
"   Maintainer: Michael Brown <michael <at> ascetinteractive.com>
"  Last Change: 
"          URL: 
"      Version: 0.1
"
"        Usage: 
"
"               You must have a working Trac repository version 0.10 or later
"               complete with the xmlrpc plugin and a user with suitable
"               access rights.
"
"               Fill in the server login details in the config section below.
"
"               Defatult key mappings: 
"
"               <leader>to : Opens the Trac wiki view
"               <leader>tq : Closes the Trac wiki View
"               <leader>tw : Writes the Current Wiki Page (Uses default update
"               Comment)
"
"               or
"
"               :TracWikiView <WikiPage>    - Open the wiki View
"               :TracNormalView             - Close the wiki View
"               :TracSaveWiki "<Comment>"   - Saves the Active Wiki Page
"               :TracTicketView <Ticket ID> - Open Trac Ticket Browser
"
"               In the Wiki TOC View Pages can be loaded by hitting <enter> 
"
"               In the Wiki View Window a Page Will go to the wiki page if
"               you hit ctrl+] but will throw an error if you arent on a
"               proper link.
"
"               Wikis can now be saved with :w and :wq. 
"               In all Trac windows :q will return to the normal view
"
"				In the Ticket List window j and k jump to next ticket
"				enter will select a ticket if it is hovering over a number
"
"               Wiki Syntax will work with this wiki syntax file
"               http://www.vim.org/scripts/script.php?script_id=725
"         Bugs:
"
"               Ocassionally when a wiki page/ticket is loaded it will throw an error.
"               Just try and load it again
"
"        To Do: 
"               - Complete Error handling for missing Files/Trac Error States
"               - Add a new Wiki Page Option
"               - Improve the toc scrolling (highlight current line)
"               - Improve Ticket Viewing option 
"               - Add support for multiple trac servers
"
"
"Configuration
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
if !exists('g:tracServer')
let g:tracServer = ''              " ADD YOUR SERVER HERE
endif
if !exists('g:tracUser')
let g:tracUser = ''                " ADD YOUR USERNAME HERE
endif

if !exists('g:tracPassword')
let g:tracPassword = ''             " ADD YOUR PASSWORD HERE
endif

if !exists('g:tracProtocol')
let g:tracProtocol = 'http://'      " ADD YOUR PROTOCOL HERE (http://, https://)
endif

if !exists('g:tracLoginPath')
let g:tracLoginPath    = '/login/xmlrpc'    " CHANGE IF NEEDED
endif
  
if !exists('g:tracDefaultComment')
let g:tracDefaultComment = 'VimTrac update' " DEFAULT COMMENT CHANGE
endif

if !exists('g:tracHideTracWiki')
let g:tracHideTracWiki = 'no' " SET TO yes/no IF YOU WANT TO HIDE 
                               " ALL THE INTERNAL TRAC WIKI PAGES (^Wiki*/^Trac*)
endif


if !exists('g:tracServerList')

let g:tracServerList = {} 

"Add Server Repositories as Dictionary entries
let g:tracServerList['Vim Trac']             = 'http://vimtracuser:wibble@www.ascetinteractive.com.au/vimtrac/login/xmlrpc'

endif





"Leader Short CUTS
map <leader>to <esc>:TracWikiView<cr>
map <leader>tw <esc>:TracSaveWiki<cr>
map <leader>tq <esc>:TracNormalView<cr>
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"End Configuration 

"
"
" Load trac.py either from the runtime directory (usually
" /usr/local/share/vim/vim71/plugin/ if you're running Vim 7.1) or from the
" home vim directory (usually ~/.vim/plugin/).
"
if g:tracServer == ''
    finish
endif

if filereadable($VIMRUNTIME."/plugin/trac.py")
  pyfile $VIMRUNTIME/plugin/trac.py
elseif filereadable($HOME."/.vim/plugin/trac.py")
  pyfile $HOME/.vim/plugin/trac.py
else
  call confirm('trac.vim: Unable to find trac.py. Place it in either your home vim directory or in the Vim runtime directory.', 'OK')
  finish
endif

if !has("python")
    finish
endif

com! -nargs=* TracWikiView   python trac_wiki_view  (<f-args>)
com! -nargs=* TracTicketView python trac_ticket_view  (<f-args>)
com! -nargs=* TracNormalView python trac_normal_view(<f-args>)
com! -nargs=* TracSaveWiki   python trac_save_wiki  (<q-args>)
com! -nargs=* -complete=customlist,CompleteTracServers TracServer python trac_server  (<q-args>)


fun CompleteTracServers (A,L,P)
	return keys(g:tracServerList) 
endfun

python trac_init()
