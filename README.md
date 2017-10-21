# general_ledger_account_filter
Odoo General Ledger Report's Account filter with no limit of 80 account lines

This module is built and tested with odoo 9 enterprise.

This module depends on account_reports module.  


# How to use:

After installing this module, you need to do some little inconvenience to manually edit the account_reports js file.

Note: Although I have tried to inherit the js definations but it seems that it has some issues in inheriting those functions. I will appreciate if somebody has the proper knowledge of odoo js script inheritance and implement the js inheritance for this module. Thanks

Please include following code snippet in the module account_reports > static > js > account_report_backend.js 

1. Replace function get_html with following. This will add the available accounts in the general ledger report context:

    // Fetches the html and is previous report.context if any, else create it
    
        get_html: function() {
            var self = this;
            var defs = [];
            return new Model('account.report.context.common').call('return_context', [self.report_model, self.given_context, self.report_id]).then(function (result) {
                self.context_model = new Model(result[0]);
                self.context_id = result[1];
                if (self.given_context.force_fy) { // Force the financial year in the new context
                    self.given_context = {};
                }
                // Finally, actually get the html and various data
                return self.context_model.call('get_html_and_data', [self.context_id, self.given_context], {context: session.user_context}).then(function (result) {
                    self.report_type = result.report_type;
                    self.html = result.html;
                    self.xml_export = result.xml_export;
                    self.fy = result.fy;
                    self.report_context = result.report_context;
                
                if (result.available_journals) {
                    self.report_context.available_journals = result.available_journals;
                }
                
                // this will include available accounts in context used to populate fields in filter
                if (result.available_accounts){
                	self.report_context.available_accounts = result.available_accounts;
                }
                
                self.render_buttons();
                self.render_searchview_buttons();
                self.render_searchview();
                self.render_pager();
                defs.push(self.update_cp());
                return $.when.apply($, defs);
            });
        });
    }
    
    
2. In function render_searchview_buttons, add this extra if clause to bind on click to our custom filter.  


        if (this.report_context.account_ids) { // Same for th ecompany filter
            this.$searchview_buttons.find('.o_account_reports_one-account').bind('click', function (event) {
                var report_context = {};
                var value = $(event.target).parents('li').data('value');
                if(self.report_context.account_ids.indexOf(value) === -1){
                    report_context.add_account_ids = value;
                }
                else {
                    report_context.remove_account_ids = value;
                }
                self.restart(report_context);
            });
        }
        
        
Thats it. 
