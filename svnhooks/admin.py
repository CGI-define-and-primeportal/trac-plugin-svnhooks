'''
Created on 11 Apr 2012

@author: karl
'''
from trac.core import *
from trac.admin.api import IAdminPanelProvider
from trac.web.chrome import ITemplateProvider, add_javascript, add_stylesheet, add_notice, add_warning
from trac.util.translation import _
from model import SVNHooksModel
from api import IConfigurableCommitHookProvider

class SVNHookAdmin(Component):
    
    implements(IAdminPanelProvider, ITemplateProvider)
    
    configurable_hooks = ExtensionPoint(IConfigurableCommitHookProvider)
    
    # IAdminPanelProvider
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('access', _("Access Controls"), 'svnhooks', _("File Archive Hooks"))

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
                    add_notice(req, _('Added SVN hook "%s" for path :%s successfully' %(self._hooks_info()[hook], path)))               
            elif req.args.get('remove'):
                sel = req.args.get('sel')
                if not sel:
                    raise TracError(_('No hook selected'))
                if not isinstance(sel, list):
                    sel = [sel]
                for id in sel:
                    path, hook = obj.get_by_id(id)
                    obj.delete(id)
                    add_notice(req, _('Hooks "%s" for path :%s deleted successfully' %(self._hooks_info()[hook], path)))
            req.redirect(req.href.admin(cat, page))
        add_stylesheet(req, 'svnhooks/css/svnhooks.css')
        add_javascript(req, 'svnhooks/js/svnhooks.js')
        
        data['svnhooks'] = obj.getall()
        data['svnhook_names'] = self._hooks_info(type='name')
        data['svnhook_descriptions'] = self._hooks_info(type='description')
        return 'admin-svnhooks.html', data
    
    def _hooks_info(self, type="name"):
        hook_info = {}
        for hook_provider in self.configurable_hooks:
            for hook in hook_provider.get_hooks():
                provider_name = self.env._component_name(hook_provider.__class__)
                if type == 'name':
                    hook_info[provider_name] =  hook   
                elif type == 'description':
                    hook_desc = hook_provider.get_hook_description(hook)
                    hook_info[provider_name] =  hook_desc
        return hook_info
                
        # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('svnhooks', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
