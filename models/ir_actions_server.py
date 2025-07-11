from odoo import api, models, fields, _


class WAServerAction(models.Model):
    _inherit = 'ir.actions.server'
    _description = 'Server Action with WhatsApp Integration'

    name = fields.Char(compute='_compute_name', store=True, readonly=False)
    state = fields.Selection(
        selection_add=[('send_whatsapp_message', 'Send WhatsApp')],
        ondelete={'send_whatsapp_message': 'cascade'}
    )
    contact_ids = fields.Many2many(
        'res.partner',
        'ir_actions_server_contact_rel',  # Unique relational table
        'server_action_id',  # Column for this model
        'partner_id',  # Column for the related model
        string="Contacts",
        help="Select multiple contacts to send WhatsApp messages."
    )
    whatsapp_account_id = fields.Many2one(
        'wa.account',
        string="WhatsApp Account",
        ondelete='set null',
        help="Select the WhatsApp account to use for sending messages."
    )
    template_id = fields.Many2one(
        'wa.template',
        string="WhatsApp Template",
        help="Select a WhatsApp template to use for the message."
    )
    whatsapp_message = fields.Html(string="WhatsApp Message", help="Message to send via WhatsApp.")
    whatsapp_media = fields.Binary(string="Media File", help="Media file to send via WhatsApp.")
    whatsapp_media_filename = fields.Char(string="Media Filename", help="Filename of the media file.")
    send_to_model_partner = fields.Boolean(
        string="Send to Model Partner",
        help="If enabled, the partner linked to the model will also receive the WhatsApp message."
    )

    def _run_action_send_whatsapp_message(self, eval_context=None):
        mixin = self.env['wa.mixin']
        for record in self.env[self.model_id.model].browse(self.env.context.get('active_ids', [])):
            if self.template_id:
                message = self.template_id.render_template('message', record)
                media = self.template_id.whatsapp_media
                media_filename = self.template_id.whatsapp_media_filename
            else:
                message = self.whatsapp_message
                media = self.whatsapp_media
                media_filename = self.whatsapp_media_filename

            # Send to selected contacts
            for contact in self.contact_ids:
                mixin.send_whatsapp(
                    mobile=contact.mobile,
                    message=message,
                    media=media,
                    media_filename=media_filename,
                    res_model=self.model_id.model,
                    res_id=record.id,
                    whatsapp_account_id=self.whatsapp_account_id.id
                )
            # Optionally send to the partner of the model
            if self.send_to_model_partner and hasattr(record, 'partner_id') and record.partner_id:
                mixin.send_whatsapp(
                    mobile=record.partner_id.mobile,
                    message=message,
                    media=media,
                    media_filename=media_filename,
                    res_model=self.model_id.model,
                    res_id=record.id,
                    whatsapp_account_id=self.whatsapp_account_id.id
                )

    def run_action(self, eval_context=None):
        """
        Override the run_action method to handle the 'send_whatsapp_message' action type.
        """
        if self.state == 'send_whatsapp_message':
            self._run_action_send_whatsapp_message(eval_context=eval_context)
        else:
            super(WAServerAction, self).run_action(eval_context=eval_context)

    @api.depends('state')
    def _compute_name(self):
        """
        Generate a name for the 'Send WhatsApp Message' action.
        """
        super(WAServerAction, self)._compute_name()
        for action in self:
            if action.state == 'send_whatsapp_message':
                action.name = 'Send WhatsApp'
