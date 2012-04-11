'''
Created on 10 Apr 2012

@author: karl
'''

from trac.core import *
from svnhooks.web_ui import SVNHooks
import re

class IConfigurableCommitHookProvider(Interface):
    
    def get_hooks():
        """Return an iterable that provides the names of the provided hooks.
        """

    def get_hook_description(name):
        """Return a plain text description of the hook with the specified
        name."""


class RequireMessageCommitHook(Component):
    implements(IConfigurableCommitHookProvider)
    
    hook_info = {"Require Commit Message": """<p>
                      Select the paths below that will require commits to contain a commit
                      message. If activated on root no further options are needed as all
                      commits will require messages to be present.
                    </p><p>
                      To avoid some meaningless messages it is required that the commit message
                      has 5 non blank characters present. There is no other restrictions on the
                      message.
                    </p>""",
                #3:"Scan for Ticket number in Commit Message"
                }
    ### IConfigurableCommitHookProvider methods
    def get_hooks(self):
        return self.hook_info.keys()

    def get_hook_description(self, name):
        return self.hook_info[name]
    
    ### IRepositoryChangeListener methods
    def changeset_pending(self, repos, changeset):
        if self.env.is_component_enabled('svnhooks'):
            hooks_mgr = SVNHooks(self.env)
            if hooks_mgr.is_enabled_for_changeset(self.__class__, changeset):
                if not changeset.message and len(changeset.message)<1:
                    log = "EMPTY"
                else:
                    log = changeset.message
                self._check_require_ticket(log)
                                
    def _check_require_ticket(self, log):
    
        ticket_prefix = '(?:#|(?:ticket|issue|bug)[: ]?)'
        ticket_re = re.compile(ticket_prefix + '([0-9]+)')
        tickets = []
        
        tickets += ticket_re.findall(log.lower())
        # At least one ticket has to be mentioned in the log message
        if tickets == []:
            raise TracError("""Failed to commit as You are checking in files into a repository that restricts
            commits without a reference to an issue. Please refer to an issue with #<num>
            in your commit message.""") 
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(id) FROM ticket WHERE "
                       "status <> 'closed' AND id IN (%s)" % ','.join(tickets))
        row = cursor.fetchone()
        # At least one of the tickets mentioned in the log messages has to
        # be open
        if not row or row[0] < 1:
            raise TracError("""Failed to commit as You are checking in files into a repository that restricts
            commits without a reference to a open ticket. Please refer to an ticket with #<num>
            in your commit message.""")

    
    def changeset_modified(self):
        pass
    
    def changeset_added(self):
        pass
    
    
class RequireTicketCommitHook(Component):
    implements(IConfigurableCommitHookProvider)
    
    hook_info = {"Require for Ticket number in Commit Message": """<p>
                  This Subversion Hook will scan each commit message and will require commits to contain a Ticket
                  number.
                    </p><p>
                  It is possible to enable this hook on a specific folder. Any commits
                  with at least one file below this directory will be subject to the 
                  rule.
                    </p><p>
                  Required Ticket number means that a commit without connection to an
                  Ticket will fail. A failure message will state that this repository
                  or path requires commit messages that has Ticket numbers.
                    </p>""",
                }
    ### IConfigurableCommitHookProvider methods
    def get_hooks(self):
        return self.hook_info.keys()

    def get_hook_description(self, name):
        return self.hook_info[name]
    
    ### IRepositoryChangeListener methods
    def changeset_pending(self, repos, changeset):
        if self.env.is_component_enabled('svnhooks'):
            hooks_mgr = SVNHooks(self.env)
            if hooks_mgr.is_enabled_for_changeset(self.__class__, changeset):
                if not changeset.message or len(changeset.message.strip())<5:
                    raise TracError("""The Repository restricts commits with no messages.
                    Please Check in with an appropriate message.""")
    
    def changeset_modified(self):
        pass
    
    def changeset_added(self):
        pass  
    
    

