# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.healthcare.utils import manage_healthcare_doc_cancel
from frappe.utils import cstr


class RadiologyExamination(Document):
	def after_insert(self):
		if self.radiology_procedure_prescription:
			frappe.db.set_value('Radiology Procedure Prescription',
			                    self.radiology_procedure_prescription, 'radiology_examination_created', True)

	def on_cancel(self):
		manage_healthcare_doc_cancel(self)

	def on_submit(self):
		insert_to_medical_record(self)

	def validate(self):
		set_title_field(self)
		ref_company = False
		if self.inpatient_record:
			ref_company = frappe.db.get_value(
				'Inpatient Record', self.inpatient_record, 'company')
		elif self.service_unit:
			ref_company = frappe.db.get_value(
				'Healthcare Service Unit', self.service_unit, 'company')
		if ref_company:
			self.company = ref_company

def set_title_field(self):
	self.title = _('{0} - {1}').format(self.patient, self.radiology_examination_template)[:100]

def insert_to_medical_record(doc):
    subject = cstr(doc.radiology_examination_template)
    if doc.practitioner:
        subject += ' '+doc.practitioner
    if subject and doc.notes:
        subject += '<br/>'+doc.notes

    medical_record = frappe.new_doc('Patient Medical Record')
    medical_record.patient = doc.patient
    medical_record.subject = subject
    medical_record.status = 'Open'
    medical_record.communication_date = doc.start_date
    medical_record.reference_doctype = 'Radiology Examination'
    medical_record.reference_name = doc.name
    medical_record.reference_owner = doc.owner
    medical_record.save(ignore_permissions=True)
