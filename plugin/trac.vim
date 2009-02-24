" Trac client: A interface to a Trac Wiki Repository
"
" Script Info and Documentation  {{{
"=============================================================================
"    Copyright: Copyright (C) 2008 Michael Brown
"      License: The MIT License
"
"               Permission is hereby granted, free of charge, to any person obtaining
"               a copy of this software and associated documentation files
"               (the "Software"), to deal in the Software without restriction,
"               including without limitation the rights to use, copy, modify,
"               merge, publish, distribute, sublicense, and/or sell copies of the
"               Software, and to permit persons to whom the Software is furnished
"               to do so, subject to the following conditions:
"
"               The above copyright notice and this permission notice shall be included
"               in all copies or substantial portions of the Software.
"
"               THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
"               OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
"               MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
"               IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
"               CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
"               TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
"               SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
" Name Of File: trac.vim , trac.py
"  Description: Wiki Client to the Trac Project Manager (trac.edgewall.org)
"   Maintainer: Michael Brown <michael <at> ascetinteractive.com>
"  Last Change:
"          URL:
"      Version: 0.3.4
"
"        Usage:
"
"               You must have a working Trac repository version 0.10 or later
"               complete with the xmlrpc plugin and a user with suitable
"               access rights.
"
"               To use the summary view you need to have the Align plugin
"               installed for the layout.
"
"               http://www.vim.org/scripts/script.php?script_id=294
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
"               :TServer <server name   - Sets the current trac Server
"               (use tab complete)
"               :TClose             - Close VimTrac to the normal View
"
"               """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"
"               Trac Wiki Commands
"
"               :TWOpen <WikiPage>    - Open the wiki View
"               :TWSave "<Comment>"   - Saves the Active Wiki Page
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
"               Wiki Syntax will work with this wiki syntax file
"               http://www.vim.org/scripts/script.php?script_id=725
"
"               """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"
"               Trac Ticket Commands
"
"               :TTOpen <Ticket ID> - Open Trac Ticket Browser
"
"               Trac current ticket option modifications (use tab complete)
"
"               :TTSetMilestone <Milestone>
"               :TTSetType <Type
"               :TTSetStatus <Status>
"               :TTSetResolution <Resolution>
"               :TTSetPriority <Priority >
"               :TTSetSeverity <Severity >
"               :TTSetComponent <Component>
"               :TTSetSummary <Summary >
"
"
"               :TTAddComment               - Add the comment to the current
"                                             ticket
"
"
"               In the Ticket List window j and k jump to next ticket
"               enter will select a ticket if it is hovering over a number
"
"         Bugs:
"
"               Ocassionally when a wiki page/ticket is loaded it will throw an error.
"               Just try and load it again
"
"               Please log any issues at http://www.ascetinteractive.com.au/vimtrac
"
"        To Do:
"               - Complete Error handling for missing Files/Trac Error States
"               - Add a new Wiki Page Option
"               - Improve the toc scrolling (highlight current line)
"               - Improve Ticket Viewing option
"               - Add support for multiple trac servers
"
"}}}
"Configuration
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

" Load trac.py either from the runtime directory (usually
" /usr/local/share/vim/vim71/plugin/ if you're running Vim 7.1) or from the
" home vim directory (usually ~/.vim/plugin/).
"
if g:tracServerList == {}
    finish
endif

if !has("python")
    call confirm('Trac.vim needs vim python 2.4.4 support. Wont load', 'OK')
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

python import sys
python if sys.version_info[:3] < (2,4,4):vim.command('let g:tracPythonVersionFlag = 1')

if exists('g:tracPythonVersionFlag')
    call confirm  ( "Trac.vim requires python 2.4.4 or later to work correctly" )
    finish
endif

if !exists('g:tracDefaultComment')
let g:tracDefaultComment = 'VimTrac update' " DEFAULT COMMENT CHANGE
endif

if !exists('g:tracHideTracWiki')
    let g:tracHideTracWiki = 'yes' " SET TO yes/no IF YOU WANT TO HIDE
                                   " ALL THE INTERNAL TRAC WIKI PAGES (^Wiki*/^Trac*)
endif

if !exists('g:tracTempHtml')
    let g:tracTempHtml = '/tmp/trac_wiki.html'
endif

if !exists('g:tracSessionDirectory')
    let g:tracSessionDirectory = expand ('$HOME') . '/.vimtrac_session'
endif

if !exists('g:tracBrowser')
    let g:tracBrowser = 'lynx'         " For Setting up Browser view (terminal)
    "let g:tracBrowser = 'firefox'     " For Setting up Browser view (linux gui  - not tested)
    "let g:tracBrowser = '"C:\Program Files\Mozilla Firefox\firefox.exe"' "GVim on Windows not tested
endif

if !exists('g:tracServerList')

let g:tracServerList = {}

"Add Server Repositories as Dictionary entries
let g:tracServerList['Vim Trac']             = 'http://vimtracuser:wibble@www.ascetinteractive.com.au/vimtrac/login/xmlrpc'
let g:tracServerList['(ServerName)']         = 'http://(User):(Pass)@(ServerPath)/login/xmlrpc'

endif

"This can be modified to speed up queries
if !exists('g:tracTicketClause')
    let g:tracTicketClause = 'status!=closed'
endif            

"Set this to 1 if you wan the ticket view to ignore attribute changes which
"can clutter up the view
"
if !exists('g:tracTicketBriefDescription')
    let g:tracTicketBriefDescription = 1
endif


"Layouts can be modified here
if !exists('g:tracWikiStyle')
    let g:tracWikiStyle     = 'full'    " 'bottom' 'top' 'full'
endif
if !exists('g:tracSearchStyle')
    let g:tracSearchStyle   = 'left'   " 'right'
endif
if !exists('g:tracTimelineStyle')
    let g:tracTimelineStyle = 'bottom'   " 'left' 'right'
endif
" Ticket view styles note the summary style needs the Align plugin
if !exists('g:tracTicketStyle')
    let g:tracTicketStyle   = 'summary' " 'full'  'top' 'left' 'right' 'full'
endif

"Leader Short CUTS (Uncomment or add and customise to yout vimrc)
"Open Wiki
" map <leader>to :TWOpen<cr>
" Save Wiki
" map <leader>tw :TWSave<cr>
" Close wiki/ticket view
" map <leader>tq :TClose<cr>
" resize
" map <leader>tt :python trac_window_resize()<cr>
" preview window
" map <leader>tp :python trac_preview()<cr>
"
" map <leader>tp :python trac.ticket.summary_view()<cr>

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"End Configuration

"
"


"Commmand Declarations
"
"NOTE: Due to the command list increasing as of version 0.3 of the plugin several command names
"have been renamed. The ':Trac' command prefix has been cut down to :T and the first inital of
"the module eg :TW... for TracWiki commands :TT... for Trac ticket commands
"
"The trac.py file no longer references these commands directly so you are free
"to change them if they clash with another plugin.
"
"WIKI MODULE COMMANDS

let g:tracDefaultView = 'wiki' " 'ticket' 'timeline'
com! -nargs=+ -complete=customlist,ComTracServers TWServer  python trac.set_current_server  (<q-args>)
com! -nargs=+ -complete=customlist,ComTracServers TTServer  python trac.set_current_server  (<q-args>, False, 'ticket')
com! -nargs=+ -complete=customlist,ComTracServers TTLServer python trac.set_current_server  (<q-args>, False ,'timeline')

"QuickTicket Option (modify this command for your own servers) - Note Ticket #12
com! -nargs=+ TQTaskOnVimTrac    python trac.ticket.create(<q-args> , 'task'        , 'Vim Trac')
com! -nargs=+ TQDefectOnVimTrac  python trac.ticket.create(<q-args> , 'defect'      , 'Vim Trac')
com! -nargs=+ TQEnhanceOnVimTrac python trac.ticket.create(<q-args> , 'enhancement' , 'Vim Trac')

com! -nargs=? -complete=customlist,ComWiki        TWOpen          python trac.wiki_view  (<f-args>)

fun LoadWikiCommands()
    "NOTE: TWSave is referenced in trac.py
    com! -nargs=*                                     TWSave          python trac.wiki.save(<q-args>)
    com! -nargs=?                                     TWCreate        python trac.wiki_view  (<f-args>, True)
    com! -nargs=? -complete=customlist,ComAttachments TWGetAttachment python trac.get_attachment (<f-args>)
    com! -nargs=? -complete=file                      TWAddAttachment python trac.add_attachment(<f-args>)
    "HTML Preview/Dumps
    com! -nargs=0                                     TWPreview       python trac.preview(False)
    com! -nargs=0                                     TWDump          python trac.preview(True)
    com! -nargs=?                                     TWVimDiff       python trac.wiki.vim_diff(<f-args>)
endfun

fun UnloadWikiCommands()
    try
        delc TWSave
        delc TWCreate
        delc TWGetAttachment
        delc TWAddAttachment
        delc TWPreview
        delc TWDump
        delc TWVimDiff
    endtry
endfun


"TICKET MODULE COMMANDS
com! -nargs=?                                     TTOpen          python trac.ticket_view  (<f-args>)

fun LoadTicketCommands()
    "Trac Ticket modifications
    com! -nargs=+                                     TTCreateTask        python trac.ticket.create(<q-args>, 'task')
    com! -nargs=+                                     TTCreateDefect      python trac.ticket.create(<q-args>, 'defect')
    com! -nargs=+                                     TTCreateEnhancement python trac.ticket.create(<q-args>, 'enhancement')

    com! -nargs=0                                     TTAddComment        python trac.ticket.add_comment()
    "Ticket Attributes
    com! -nargs=? -complete=customlist,ComMilestone   TTSetMilestone      python trac.ticket.set_attr(<f-args>, 'milestone' )
    com! -nargs=? -complete=customlist,ComType        TTSetType           python trac.ticket.set_attr(<f-args>, 'type' )
    com! -nargs=? -complete=customlist,ComStatus      TTSetStatus         python trac.ticket.set_attr(<f-args>, 'status' )
    com! -nargs=? -complete=customlist,ComResolution  TTSetResolution     python trac.ticket.set_attr(<f-args>, 'resolution' )
    com! -nargs=? -complete=customlist,ComPriority    TTSetPriority       python trac.ticket.set_attr(<f-args>, 'priority' )
    com! -nargs=? -complete=customlist,ComSeverity    TTSetSeverity       python trac.ticket.set_attr(<f-args>, 'severity' )
    com! -nargs=? -complete=customlist,ComComponent   TTSetComponent      python trac.ticket.set_attr(<f-args>, 'component' )
    com! -nargs=?                                     TTSetOwner          python trac.ticket.set_attr(<f-args>, 'owner' )
    com! -nargs=+                                     TTSetSummary        python trac.ticket.set_summary(<q-args>)

    com! -nargs=0                                     TTUpdateDescrption  python trac.ticket.update_description()

    com! -nargs=? -complete=customlist,ComMilestone   TTFilterMilestone   python trac.ticket.filter.add(<f-args>, 'milestone' )
    com! -nargs=? -complete=customlist,ComType        TTFilterType        python trac.ticket.filter.add(<f-args>, 'type' )
    com! -nargs=? -complete=customlist,ComStatus      TTFilterStatus      python trac.ticket.filter.add(<f-args>, 'status' )
    com! -nargs=? -complete=customlist,ComResolution  TTFilterResolution  python trac.ticket.filter.add(<f-args>, 'resolution' )
    com! -nargs=? -complete=customlist,ComPriority    TTFilterPriority    python trac.ticket.filter.add(<f-args>, 'priority' )
    com! -nargs=? -complete=customlist,ComSeverity    TTFilterSeverity    python trac.ticket.filter.add(<f-args>, 'severity' )
    com! -nargs=? -complete=customlist,ComComponent   TTFilterComponent   python trac.ticket.filter.add(<f-args>, 'component' )
    com! -nargs=?                                     TTFilterOwner       python trac.ticket.filter.add(<f-args>, 'owner' )

    com! -nargs=? -complete=customlist,ComMilestone   TTFilterNoMilestone python trac.ticket.filter.add('', 'milestone' )
    com! -nargs=?                                     TTFilterNoOwner     python trac.ticket.filter.add('', 'owner' )

    com! -nargs=? -complete=customlist,ComMilestone   TTIgnoreMilestone   python trac.ticket.filter.add(<f-args>, 'milestone' ,False)
    com! -nargs=? -complete=customlist,ComType        TTIgnoreType        python trac.ticket.filter.add(<f-args>, 'type' ,False)
    com! -nargs=? -complete=customlist,ComStatus      TTIgnoreStatus      python trac.ticket.filter.add(<f-args>, 'status' ,False)
    com! -nargs=? -complete=customlist,ComResolution  TTIgnoreResolution  python trac.ticket.filter.add(<f-args>, 'resolution' ,False)
    com! -nargs=? -complete=customlist,ComPriority    TTIgnorePriority    python trac.ticket.filter.add(<f-args>, 'priority' ,False)
    com! -nargs=? -complete=customlist,ComSeverity    TTIgnoreSeverity    python trac.ticket.filter.add(<f-args>, 'severity' ,False)
    com! -nargs=? -complete=customlist,ComComponent   TTIgnoreComponent   python trac.ticket.filter.add(<f-args>, 'component' ,False)
    com! -nargs=?                                     TTIgnoreOwner       python trac.ticket.filter.add(<f-args>, 'owner' ,False)

    com! -nargs=? -complete=customlist,ComMilestone   TTIgnoreNoMilestone python trac.ticket.filter.add('', 'milestone' ,False)
    com! -nargs=?                                     TTIgnoreNoOwner     python trac.ticket.filter.add('', 'owner' ,False)

    com! -nargs=0                                     TTClearAllFilters   python trac.ticket.filter.clear()
    com! -nargs=*                                     TTClearFilter       python trac.ticket.filter.delete(<f-args>)
    com! -nargs=*                                     TTListFilters       python trac.ticket.filter.list()
    "Ticket Sorting
    com! -nargs=? -complete=customlist,ComSort        TTSortby            python trac.ticket.sort.set_sortby(<f-args>)

    "Ticket Attachments
    com! -nargs=? -complete=customlist,ComAttachments TTGetAttachment     python trac.get_attachment (<f-args>)
    com! -nargs=? -complete=file                      TTAddAttachment     python trac.add_attachment(<f-args>)
    "Html Preview
    com! -nargs=0                                     TTPreview           python trac.preview()

    com! -nargs=0                                     TTLoadTicketSession python trac.ticket.session_load()
    com! -nargs=0                                     TTSaveTicketSession python trac.ticket.session_save()

    com! -nargs=? -complete=customlist,ComComponent   TTSaveCompSession   python trac.ticket.session_component_save(<q-args>)
    com! -nargs=* -complete=customlist,ComComponent   TTLoadCompSession   python trac.ticket.session_component_load(<q-args>)

    "Ticket resolution
    com! -nargs=*                                     TTCloseTicket       python trac.ticket.close_ticket(<q-args>)
    com! -nargs=*                                     TTResolveFixed      python trac.ticket.resolve_ticket(<q-args>,'fixed')
    com! -nargs=*                                     TTResolveWontfix    python trac.ticket.resolve_ticket(<q-args>,'wontfix')
    com! -nargs=*                                     TTResolveDuplicate  python trac.ticket.resolve_ticket(<q-args>,'duplicate')
    com! -nargs=*                                     TTResolveInvalid    python trac.ticket.resolve_ticket(<q-args>,'invalid')
    com! -nargs=*                                     TTResolveWorksForMe python trac.ticket.resolve_ticket(<q-args>,'worksforme')
endfun

fun UnloadTicketCommands()
    "Trac Ticket modifications
    try
        delc TTCreateTask
        delc TTCreateDefect
        delc TTCreateEnhancement
        delc TTAddComment
        "Ticket Attributes
        delc TTSetMilestone
        delc TTSetStatus
        delc TTSetType
        delc TTSetResolution
        delc TTSetPriority
        delc TTSetSeverity
        delc TTSetComponent
        delc TTSetOwner
        delc TTSetSummary

        delc TTUpdateDescrption

        delc TTFilterMilestone
        delc TTFilterType
        delc TTFilterStatus
        delc TTFilterResolution
        delc TTFilterPriority
        delc TTFilterSeverity
        delc TTFilterComponent
        delc TTFilterOwner
        delc TTClearFilter
        delc TTClearAllFilters

        delc TTSortby

        delc TTIgnoreMilestone
        delc TTIgnoreType
        delc TTIgnoreStatus
        delc TTIgnoreResolution
        delc TTIgnorePriority
        delc TTIgnoreSeverity
        delc TTIgnoreComponent
        delc TTIgnoreOwner

        delc TTIgnoreNoMilestone
        delc TTIgnoreNoOwner

        "Ticket Attachments
        delc TTGetAttachment
        delc TTAddAttachment
        "Html Preview
        delc TTPreview
        delc TTLoadTicketSession
        delc TTSaveTicketSession
        delc TTCloseTicket
        delc TTListFilters
        delc TTFilterNoMilestone
        delc TTFilterNoOwner
        "resolution
        delc TTResolveFixed
        delc TTResolveWontfix
        delc TTResolveDuplicate
        delc TTResolveInvalid
        delc TTResolveWorksForMe
    endtry
endfun

"MISCELLANEOUS
com! -nargs=+                                     TSearch         python trac.search_view(<q-args>)
com! -nargs=1                                     TChangesetOpen  python trac.changeset_view(<f-args>, True)
com! -nargs=0                                     TTimelineOpen   python trac.timeline_view()
com! -nargs=0                                     TClose          python trac.normal_view(<f-args>)

"FUNCTION COMPLETES
fun ComTracServers (A,L,P)
    return filter (keys(g:tracServerList), 'v:val =~ "^'.a:A.'"')
endfun

let g:tracOptions = 1

fun ComAttachments (A,L,P)
    python trac.list_attachments()

    return filter (split (g:tracOptions, '|' ), 'v:val =~ "^' . a:A . '"')
endfun

fun ComWiki  (A,L,P)
    python trac.wiki.get_options()

    return filter (split (g:tracOptions, '|' ), 'v:val =~ "^' . a:A . '"')
endfun

"COMMAND COMPLETES
fun ComMilestone  (A,L,P)
    python trac.ticket.get_options(0)

    return filter (split (g:tracOptions, '|' ), 'v:val =~ "^' . a:A . '"')
endfun

fun ComType  (A,L,P)
    python trac.ticket.get_options(1)
    return filter (split (g:tracOptions, '|' ), 'v:val =~ "^' . a:A . '"')
endfun

fun ComStatus  (A,L,P)
    python trac.ticket.get_options(2)
    return filter (split (g:tracOptions, '|' ), 'v:val =~ "^' . a:A . '"')
endfun

fun ComResolution  (A,L,P)
    python trac.ticket.get_options(3)
    return filter (split (g:tracOptions, '|' ), 'v:val =~ "^' . a:A . '"')
endfun

fun ComPriority  (A,L,P)
    python trac.ticket.get_options(4)
    return filter (split (g:tracOptions, '|' ), 'v:val =~ "^' . a:A . '"')
endfun

fun ComSeverity  (A,L,P)
    python trac.ticket.get_options(5)
    return filter (split (g:tracOptions, '|' ), 'v:val =~ "^' . a:A . '"')
endfun

fun ComComponent  (A,L,P)
    python trac.ticket.get_options(6)
    return filter (split (g:tracOptions, '|' ), 'v:val =~ "^' . a:A . '"')
endfun

fun ComSort (A,L,P)
    return filter (['priority','milestone'], 'v:val =~ "^' . a:A . '"')
endfun


"Callback Function for Minibufexplorer et al windows that dont like being
"closed by the :only command
"TODO add other common plugins that may be affected 
"see OpenCloseCallbacks in the wiki
fun TracOpenViewCallback()
    try
        CMiniBufExplorer
    catch
        return 0
    endt

    return 1
endfun

fun TracCloseViewCallback()
    try
        MiniBufExplorer
    catch
        return 0
    endt
    return 1
endfun

python trac_init()
