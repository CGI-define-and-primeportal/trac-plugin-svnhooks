# coding: utf-8
#
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
from trac.admin import *
from trac.core import *
from trac.web.main import IRequestFilter
from trac.env import IEnvironmentSetupParticipant
from trac.db.api import DatabaseManager
from trac.web.chrome import ITemplateProvider, add_javascript, add_stylesheet, Chrome
from trac.util.translation import _
from trac.admin.api import IAdminPanelProvider
from trac.web.chrome import Chrome, add_notice, add_warning
from model import SVNHooksModel
from trac.util.compat import sha1
from svnhooks.api import IConfigurableCommitHookProvider


class SVNHooks(Component):
    implements(IAdminPanelProvider,
               IEnvironmentSetupParticipant, ITemplateProvider)

    
    
    configurable_hooks = ExtensionPoint(IConfigurableCommitHookProvider)
    
    def is_enabled_for_changeset(self, component, changeset):
        component_name = self.env._component_name(component.__class__)
        obj = SVNHooksModel(self.env)
        svnhooks = obj.getall_path()
       
        changes = list(changeset.get_changes()) 
        for path, kind, action, base_path, base_rev in changes:
            for svnpath in svnhooks:
                if path.startswith(svnpath[1:]):
                    for row in svnhooks[svnpath]:
                        id, hook = row[0], row[1]
                        if hook == component_name:
                            self.log.debug("Changeset path %s matches commit hook %s for parent path %s" % (path, component_name, svnpath))
                            return True
                    return False
    
   # IAdminPanelProvider
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('access', _('Access Controls'), 'svnhooks', _('SVNHooks'))

    def render_admin_panel(self, req, cat, page, svnhooks_name):
        data = {}
        obj = SVNHooksModel(self.env)
        if req.method == 'POST':
            if req.args.get('add') :
                hook = req.args.get('hook').strip()
                path = req.args.get('path').strip()
                validate_path=obj.validate(path,hook)
                if validate_path > 0:
                    add_warning(req,_('Already exists'))
                else:
                    obj.insert( path, hook)
                    add_notice(req, _('Added SVN hook "%s" for path :%s successfully' %(hook, path)))               
            elif req.args.get('remove'):
                sel = req.args.get('sel')
                if not sel:
                    raise TracError(_('No hook selected'))
                if not isinstance(sel, list):
                    sel = [sel]
                for id in sel:
                    path, hook = obj.get_by_id(id)
                    obj.delete(id)
                    add_notice(req, _('Hooks "%s" for path :%s deleted successfully' %(hook, path)))
            req.redirect(req.href.admin(cat, page))
        add_stylesheet(req, 'svnhooks/css/svnhooks.css')
        add_javascript(req, 'svnhooks/js/svnhooks.js')
        
        data['svnhooks'] = obj.getall()
        data['svnhook_info'] = list(self._configurable_hooks_info())
        data['svnhook_names'] = {1:"Something"}
        return 'admin-svnhooks.html', data
    
    def _configurable_hooks_info(self):
        for hook_provider in self.configurable_hooks:
            for hook in hook_provider.get_hooks():
                hook_desc = hook_provider.get_hook_description(hook)
                yield (hook, hook_desc, hook_provider)

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

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('svnhooks', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

