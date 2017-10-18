//odoo.define('account_reports_user_filter.account_report_generic', function(require) {
//	'use strict';
//
//	var core = require('web.core');
//	var account_report_generic = require('account_reports.account_report_generic');
//	var Model = require('web.Model');
//	var session = require('web.session');
//	var QWeb = core.qweb;
//
//	var account_reports_user_filter_generic = account_report_generic.extend({
//		
//		render_searchview_buttons : function() {
//			var self = this;
//			
////			this.$searchview_buttons = this._super();
//			this.$searchview_buttons = $(QWeb.render("accountReports.searchView", {report_type: this.report_type, context: this.report_context}));
//
////			this.$searchview_buttons = $(QWeb.render("accountReports.searchView", {
////				report_type : this.report_type,
////				context : this.report_context
////			}))
////			this.$searchview_buttons.find(".o_account_reports_analytic_account_auto_complete").select2();
////			this.$searchview_buttons.find(".o_account_reports_customer_auto_complete").select2();
////			this.$searchview_buttons.find(".o_account_reports_business_unit_auto_complete").select2();
//
//			this.$searchview_buttons.find('.o_account_reports_users').bind('click', function(event) {
//				var report_context = {};
//				var user_id = $(event.target).parents('li').data('user-id');
//				if (self.report_context.user_ids.indexOf(user_id) === -1) {
//					report_context.add_user_ids = user_id;
//				} else {
//					report_context.remove_user_ids = user_id;
//				}
//				self.restart(report_context);
//			});
//
//			return this.$searchview_buttons;
//		},
//		
//		get_html : function() {
//			var result = this._super();
//			if (result.report_context) {
//				result.report_context.user_ids = result.user_ids;
//				result.report_context.available_users = result.available_users;
//			}
//			return result;
//		},
//	});
//
//	core.action_registry.add("account_reports_user_filter_generic", account_reports_user_filter_generic);
//	return account_reports_user_filter_generic;
//	
//});