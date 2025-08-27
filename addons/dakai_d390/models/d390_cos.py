from odoo import api, fields, models, Command


class DeclaratiaD390Cos(models.Model):
    _name = "report.d390.cos"
    _description = "Declaratia D390 Cos"

    name = fields.Char(compute="_compute_name", store=True)

    @api.depends('tip', 'picking_id')
    def _compute_name(self):
        for s in self:
            s.name = f"Cos_{s.tip} - {s.picking_id.name}"

    d390_id = fields.Many2one('l10_romania.report.d390')
    picking_id = fields.Many2one("stock.picking")

    tara_m1 = fields.Char(string="Tara partner", compute="_partner_data", store=True)
    cod_m1 = fields.Char(string="Cod partner", compute="_partner_data", store=True)

    motiv = fields.Char(string="Motivul modificarii", compute="_partner_data", store=True)
    tara_m2 = fields.Char(string="Tara partner modificat", compute="_partner_data", store=True)
    cod_m2 = fields.Char(string="Cod partner modificat", compute="_partner_data", store=True)

    tip = fields.Selection([
        ('A', 'A'),
        ('B', 'B')
    ], string="Operation Type", compute="_compute_tip", store=True)

    @api.depends("cod_m2")
    def _compute_tip(self):
        for s in self:
            s.tip = s.cod_m2 and "B" or "A"

    @api.depends("picking_id")
    def _partner_data(self):
        for s in self:
            s.tara_m1 = s.picking_id.partner_id.country_id.code
            s.cod_m1 = s.picking_id.partner_id.l10n_ro_vat_number

            #TODO
            s.motiv = False #s.picking_id.l10n_ro_new_contact and "2" or False
            s.tara_m2 = False #s.picking_id.l10n_ro_new_contact.name
            s.cod_m2 = False #s.picking_id.l10n_ro_new_contact.l10n_ro_vat_number

    @api.model
    def generate(self, d390_id):
        d390_id.cos_ids.unlink()
        pickings = d390_id.picking_ids
        for picking in pickings:
            self.create({
                'd390_id': d390_id.id,
                'picking_id': picking.id,
            })


