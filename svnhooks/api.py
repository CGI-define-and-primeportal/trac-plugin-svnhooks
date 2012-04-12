'''
Created on 10 Apr 2012

@author: karl
'''
# Copyright (c) 2010, Logica
# 
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#     * Redistributions of source code must retain the above copyright 
#       notice, this list of conditions and the following svnhooks.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following svnhooks in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the <ORGANIZATION> nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------
# Created on 5 January 2012
# @author prabu subramanian

from pkg_resources import resource_filename
import re

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.db.api import DatabaseManager
from trac.versioncontrol.api import IRepositoryChangeListener

from svnhooks.model import SVNHooksModel

class IConfigurableCommitHookProvider(Interface):
    
    def get_hooks():
        """Return an iterable that provides the names of the provided hooks.
        """

    def get_hook_description(name):
        """Return a plain text description of the hook with the specified
        name."""
        
class SVNHookSystem(Component):
    implements(IEnvironmentSetupParticipant)
    
    def is_enabled_for_changeset(self, component, changeset):
        provider_name = self.env._component_name(type(component))
        obj = SVNHooksModel(self.env)
        svnhooks = obj.getall_path()
        try:
            fobj = open('/home/karl/svnlog', 'a')
            fobj.write("="*30)
            fobj.write("\n")
            changes = list(changeset.get_changes()) 
            for path, kind, action, base_path, base_rev in changes:
                for svnpath in svnhooks:
                    if path.startswith(svnpath[1:]):
                        for row in svnhooks[svnpath]:
                            id, hook = row[0], row[1]
                            if hook == provider_name:
                                fobj.write("Changeset path %s matches commit hook %s for parent path %s END\n" % (path, provider_name, svnpath))
                                self.log.debug("Changeset path %s matches commit hook %s for parent path %s" % (path, provider_name, svnpath))
                                return True
                        fobj.write("Changeset path %s doesn't match commit hook %s for parent path %s END\n" % (path, provider_name, svnpath))
                        return False
        finally:
            fobj.close()
    
   
    # IEnvironmentSetupParticipant
    def environment_created(self):
        self.upgrade_environment(self.env.get_db_cnx())

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("select count(*) from svnhooks")
            cursor.fetchone()
            return False
        except:
            db.rollback()
            return True

    def upgrade_environment(self, db):
        self.log.debug("Upgrading schema for svnhooks plugin")
        db_backend, _ = DatabaseManager(self.env).get_connector()
        cursor = db.cursor()
        for table in SVNHooksModel.svnhooks_schema:
            for stmt in db_backend.to_sql(table):
                self.log.debug(stmt)
                cursor.execute(stmt)



class RequireMessageCommitHook(Component):
    implements(IConfigurableCommitHookProvider, IRepositoryChangeListener)
    
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
        from genshi.builder import Markup
        return Markup(self.hook_info[name])
    
    ### IRepositoryChangeListener methods
    def changeset_pending(self, repos, changeset):
        if self.env.is_component_enabled('svnhooks'):
            hooks_mgr = SVNHookSystem(self.env)
            if hooks_mgr.is_enabled_for_changeset(self, changeset):
                if not changeset.message or len(changeset.message.strip())<5:
                    raise TracError("""The Repository restricts commits with no messages.
                    Please Check in with an appropriate message.""")
    
                                
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

    
    def changeset_modified(self, repos, changeset):
        pass
    
    def changeset_added(self, repos, changeset):
        pass
    
    
class RequireTicketCommitHook(Component):
    implements(IConfigurableCommitHookProvider, IRepositoryChangeListener)
    
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
        from genshi.builder import Markup
        return Markup(self.hook_info[name])
    
    ### IRepositoryChangeListener methods
    def changeset_pending(self, repos, changeset):
        if self.env.is_component_enabled('svnhooks'):
            hooks_mgr = SVNHookSystem(self.env)
            if hooks_mgr.is_enabled_for_changeset(self, changeset):
                if not changeset.message and len(changeset.message)<1:
                    log = "EMPTY"
                else:
                    log = changeset.message
                self._check_require_ticket(log)
    
    def changeset_modified(self, repos, changeset):
        pass
    
    def changeset_added(self, repos, changeset):
        pass  
    
    




