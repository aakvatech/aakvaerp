// Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Radiology Examination', {
	onload: function (frm) {
		if (frm.is_new()) {
			frm.add_fetch('radiology_procedure', 'medical_department', 'medical_department');
			frappe.db.get_value('Healthcare Settings', '', 'default_practitioner_source', function (r) {
				if (r && r.default_practitioner_source) {
					frm.set_value('source', r.default_practitioner_source);
				}
				else {
					frm.set_value('source', '');
				}
			});
		}
	},
	inpatient_record: function (frm) {
		if (frm.doc.inpatient_record) {
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Inpatient Record',
					name: frm.doc.inpatient_record
				},
				callback: function (r) {
					if (r.message) {
						if (r.message.source) {
							frm.set_value('source', r.message.source);
							frm.set_df_property('source', 'read_only', 1);
						}
						else {
							frm.set_value('source', '');
							frm.set_df_property('source', 'read_only', 0);
						}
						if (r.message.referring_practitioner) {
							frm.set_value('referring_practitioner', r.message.referring_practitioner);
							frm.set_df_property('referring_practitioner', 'read_only', 1);
						}
						else {
							frm.set_value('referring_practitioner', '');
							frm.set_df_property('referring_practitioner', 'read_only', 0);
						}
						if (r.message.company) {
							frm.set_value('company', r.message.company)
						}
					}
				}
			});
		}
	},
	source: function (frm) {
		if (frm.doc.source == 'Direct') {
			frm.set_value('referring_practitioner', '');
			frm.set_df_property('referring_practitioner', 'hidden', 1);
		}
		else if (frm.doc.source == 'External Referral' || frm.doc.source == 'Referral') {
			if (frm.doc.practitioner) {
				frm.set_df_property('referring_practitioner', 'hidden', 0);
				if (frm.doc.source == 'External Referral') {
					frappe.db.get_value('Healthcare Practitioner', frm.doc.practitioner, 'healthcare_practitioner_type', function (r) {
						if (r && r.healthcare_practitioner_type && r.healthcare_practitioner_type == 'External') {
							frm.set_value('referring_practitioner', frm.doc.practitioner);
						}
						else {
							frm.set_value('referring_practitioner', '');
						}
					});
					frm.set_df_property('referring_practitioner', 'read_only', 0);
				}
				else {
					frappe.db.get_value('Healthcare Practitioner', frm.doc.practitioner, 'healthcare_practitioner_type', function (r) {
						if (r && r.healthcare_practitioner_type && r.healthcare_practitioner_type == 'Internal') {
							frm.set_value('referring_practitioner', frm.doc.practitioner);
							frm.set_df_property('referring_practitioner', 'read_only', 1);
						}
						else {
							frm.set_value('referring_practitioner', '');
							frm.set_df_property('referring_practitioner', 'read_only', 0);
						}
					});
				}
				frm.set_df_property('referring_practitioner', 'reqd', 1);
			}
			else {
				frm.set_df_property('referring_practitioner', 'read_only', 0);
				frm.set_df_property('referring_practitioner', 'hidden', 0);
				frm.set_df_property('referring_practitioner', 'reqd', 1);
			}
		}
	},
	refresh: function (frm) {
		frm.set_query('patient', function () {
			return {
				filters: { 'status': 'Active' }
			};
		});
		frm.set_query('service_unit', function () {
			return {
				filters: {
					'is_group': false
				}
			};
		});
		frm.set_query('referring_practitioner', function () {
			if (frm.doc.source == 'External Referral') {
				return {
					filters: {
						'healthcare_practitioner_type': 'External'
					}
				};
			}
			else {
				return {
					filters: {
						'healthcare_practitioner_type': 'Internal'
					}
				};
			}
		});
	}
});
