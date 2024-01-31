# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ApplicantManagement(models.Model):
    _inherit = "hr.applicant"

    state_real = fields.Selection([
        ('1', 'Initial Qualification'),
        ('2', 'First Interview'),
        ('3', 'Second Interview'),
        ('4', 'Contract Proposal'),
        ('5', 'Contract Signed'),
    ], string='State', track_visibility='onchange')
    user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)
    client_id = fields.Many2one('res.partner', "Client")
    employment_ids = fields.One2many('employment.data', 'applicant_id', 'Employment data')

    @api.model
    def create(self, vals):
        request = super(ApplicantManagement, self).create(vals)
        if request.stage_id:
            if request.stage_id.sequence == 1:
                request.state_real = '1'
            if request.stage_id.sequence == 2:
                request.state_real = '2'
            if request.stage_id.sequence == 3:
                request.state_real = '3'
            if request.stage_id.sequence == 4:
                request.state_real = '4'
            if request.stage_id.sequence == 5:
                request.state_real = '5'
        return request

    def write(self, vals):
        if vals and 'stage_id' in vals:
            stage_id = vals.get('stage_id')
            obj_stage_id = self.env['hr.recruitment.stage'].search([('id', '=', stage_id)])
            if obj_stage_id:
                for obj_stage in obj_stage_id:
                    if obj_stage.sequence == 1:
                        self.write({'state_real': '1'})
                    if obj_stage.sequence == 2:
                        self.write({'state_real': '2'})
                    if obj_stage.sequence == 3:
                        self.write({'state_real': '3'})
                    if obj_stage.sequence == 4:
                        self.write({'state_real': '4'})
                    if obj_stage.sequence == 5:
                        self.write({'state_real': '5'})
        res = super(ApplicantManagement, self).write(vals)
        return res


class Employee(models.Model):
    _inherit = "hr.employee"

    grade_school = fields.Char('Grade/Class')
    major_subject = fields.Char('Major Subjects')


class EmploymentData(models.Model):
    _name = "employment.data"
    _description = "Employment Data"

    name = fields.Char('Organization', index=True, required=True)
    start_date = fields.Date('Date init', help='Initial date range to update')
    end_date = fields.Date('Date Top', help='End date range to update')
    responsibilities = fields.Char('Responsibilities')
    supervisor = fields.Char('Supervisor')
    applicant_id = fields.Many2one('hr.applicant', 'Applicant', track_visibility='onchange', index=True)

