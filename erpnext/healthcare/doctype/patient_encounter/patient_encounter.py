# -*- coding: utf-8 -*-
# Copyright (c) 2015, ESS LLP and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr
from erpnext.healthcare.utils import make_cpoe

class PatientEncounter(Document):
	def validate(self):
		self.set_title()

	def on_update(self):
		if self.appointment:
			frappe.db.set_value('Patient Appointment', self.appointment, 'status', 'Closed')
		update_encounter_medical_record(self)

	def after_insert(self):
		insert_encounter_to_medical_record(self)

	def on_submit(self):
		update_encounter_medical_record(self)
		create_therapy_plan(self)
		create_cpoe(self)

	def on_cancel(self):
		if self.appointment:
			frappe.db.set_value('Patient Appointment', self.appointment, 'status', 'Open')
		delete_medical_record(self)

	def set_title(self):
		self.title = _('{0} with {1}').format(self.patient_name or self.patient,
			self.practitioner_name or self.practitioner)[:100]

def create_therapy_plan(encounter):
	if len(encounter.therapies):
		doc = frappe.new_doc('Therapy Plan')
		doc.patient = encounter.patient
		doc.start_date = encounter.encounter_date
		for entry in encounter.therapies:
			doc.append('therapy_plan_details', {
				'therapy_type': entry.therapy_type,
				'no_of_sessions': entry.no_of_sessions
			})
		doc.save(ignore_permissions=True)
		if doc.get('name'):
			encounter.db_set('therapy_plan', doc.name)
			frappe.msgprint(_('Therapy Plan {0} created successfully.').format(frappe.bold(doc.name)), alert=True)

def insert_encounter_to_medical_record(doc):
	subject = set_subject_field(doc)
	medical_record = frappe.new_doc('Patient Medical Record')
	medical_record.patient = doc.patient
	medical_record.subject = subject
	medical_record.status = 'Open'
	medical_record.communication_date = doc.encounter_date
	medical_record.reference_doctype = 'Patient Encounter'
	medical_record.reference_name = doc.name
	medical_record.reference_owner = doc.owner
	medical_record.save(ignore_permissions=True)

def update_encounter_medical_record(encounter):
	medical_record_id = frappe.db.exists('Patient Medical Record', {'reference_name': encounter.name})

	if medical_record_id and medical_record_id[0][0]:
		subject = set_subject_field(encounter)
		frappe.db.set_value('Patient Medical Record', medical_record_id[0][0], 'subject', subject)
	else:
		insert_encounter_to_medical_record(encounter)

def delete_medical_record(encounter):
	frappe.delete_doc_if_exists('Patient Medical Record', 'reference_name', encounter.name)

def set_subject_field(encounter):
	subject = frappe.bold(_('Healthcare Practitioner: ')) + encounter.practitioner + '<br>'
	if encounter.symptoms:
		subject += frappe.bold(_('Symptoms: ')) + '<br>'
		for entry in encounter.symptoms:
			subject += cstr(entry.complaint) + '<br>'
	else:
		subject += frappe.bold(_('No Symptoms')) + '<br>'

	if encounter.diagnosis:
		subject += frappe.bold(_('Diagnosis: ')) + '<br>'
		for entry in encounter.diagnosis:
			subject += cstr(entry.diagnosis) + '<br>'
	else:
		subject += frappe.bold(_('No Diagnosis')) + '<br>'

	if encounter.drug_prescription:
		subject += '<br>' + _('Drug(s) Prescribed.')
	if encounter.lab_test_prescription:
		subject += '<br>' + _('Test(s) Prescribed.')
	if encounter.procedure_prescription:
		subject += '<br>' + _('Procedure(s) Prescribed.')

	return subject
def create_cpoe(encounter):
	if encounter.drug_prescription:
		for drug in encounter.drug_prescription:
			medication = frappe.get_doc('Medication', drug.drug_code)
			args={
				'cpoe_category': medication.get_value('cpoe_category'),
				'patient_care_type': medication.get_value('patient_care_type'),
				'order_date': encounter.get_value('encounter_date'),
				'ordered_by': encounter.get_value('practitioner'),
				'order_group': encounter.name,
				'replaces': drug.get_value('replaces'),
				'patient': encounter.get_value('patient'),
				'order_doctype': 'Medication',
				'order': medication.name,
				'order_description': medication.get_value('description'),
				'intent': drug.get_value('intent'),
				'priority': drug.get_value('priority'),
				'reason': drug.get_value('reason'),
				'reason_reference_doctype': drug.get_value('reason_reference_doctype'),
				'reason_reference': drug.get_value('reason_reference'),
				'quantity': drug.get_value('quantity'),
				'sequence': drug.get_value('sequence'),
				'expected_date': drug.get_value('expected_date'),
				'as_needed': drug.get_value('as_needed'),
				'occurrence': drug.get_value('occurrence'),
				'occurence_period': drug.get_value('occurence_period'),
				'body_part': drug.get_value('body_part'),
				'staff_role': medication.get_value('staff_role'),
				'note': drug.get_value('note'),
				'patient_instruction': drug.get_value('patient_instruction'),
				}
			make_cpoe(args)
	if encounter.lab_test_prescription:
		for labtest in encounter.lab_test_prescription:
			lab_template = frappe.get_doc('Lab Test Template', labtest.lab_test_code)
			args={
				'cpoe_category': lab_template.get_value('cpoe_category'),
				'patient_care_type': lab_template.get_value('patient_care_type'),
				'order_date': encounter.get_value('encounter_date'),
				'ordered_by': encounter.get_value('practitioner'),
				'order_group': encounter.name,
				'replaces': labtest.get_value('replaces'),
				'patient': encounter.get_value('patient'),
				'order_doctype': 'Lab Test Template',
				'order': lab_template.name,
				'order_description': lab_template.get_value('lab_test_description'),
				'intent': labtest.get_value('intent'),
				'priority': labtest.get_value('priority'),
				'reason': labtest.get_value('reason'),
				'reason_reference_doctype': labtest.get_value('reason_reference_doctype'),
				'reason_reference': labtest.get_value('reason_reference'),
				'quantity': labtest.get_value('quantity'),
				'sequence': labtest.get_value('sequence'),
				'expected_date': labtest.get_value('expected_date'),
				'as_needed': labtest.get_value('as_needed'),
				'occurrence': labtest.get_value('occurrence'),
				'occurence_period': labtest.get_value('occurence_period'),
				'body_part': labtest.get_value('body_part'),
				'staff_role': lab_template.get_value('staff_role'),
				'note': labtest.get_value('note'),
				'patient_instruction': labtest.get_value('patient_instruction')
				}
			make_cpoe(args)
	if encounter.procedure_prescription:
		for procedure in encounter.procedure_prescription:
			procedure_template = frappe.get_doc('Clinical Procedure Template', procedure.procedure)
			args={
				'cpoe_category': procedure_template.get_value('cpoe_category'),
				'patient_care_type': procedure_template.get_value('patient_care_type'),
				'order_date': encounter.get_value('encounter_date'),
				'ordered_by': encounter.get_value('practitioner'),
				'order_group': encounter.name,
				'replaces': procedure.get_value('replaces'),
				'patient': encounter.get_value('patient'),
				'order_doctype': 'Clinical Procedure Template',
				'order': procedure_template.name,
				'order_description': procedure_template.get_value('description'),
				'intent': procedure.get_value('intent'),
				'priority': procedure.get_value('priority'),
				'reason': procedure.get_value('reason'),
				'reason_reference_doctype': procedure.get_value('reason_reference_doctype'),
				'reason_reference': procedure.get_value('reason_reference'),
				'quantity': procedure.get_value('quantity'),
				'sequence': procedure.get_value('sequence'),
				'expected_date': procedure.get_value('expected_date'),
				'as_needed': procedure.get_value('as_needed'),
				'occurrence': procedure.get_value('occurrence'),
				'occurence_period': procedure.get_value('occurence_period'),
				'body_part': procedure.get_value('body_part'),
				'staff_role': procedure_template.get_value('staff_role'),
				'note': procedure.get_value('note'),
				'patient_instruction': procedure.get_value('patient_instruction')
				}
			make_cpoe(args)
