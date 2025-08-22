# Base Workflow Engine pentru Odoo 18

Acest modul oferă o fundație tehnică pentru crearea de fluxuri de lucru (workflows) dinamice, condiționate și, cel mai important, **non-intruzive**, aplicabile oricărui model din Odoo. A fost conceput pentru a rula în paralel cu funcționalitățile native ale Odoo, păstrând intactă logica de business existentă.

---

## Arhitectura de Mapare: Păstrarea Etapelor Native

Spre deosebire de alte abordări care înlocuiesc câmpurile de etape native ale modelelor Odoo, acest motor de flux utilizează o arhitectură de **mapare**. Acest lucru înseamnă că etapele originale ale unui model (ex: `crm.stage` pentru Oportunități) **rămân nemodificate**.

**Avantaje:**
* **Non-Intruziv:** Funcționalitățile native Odoo (rapoarte, acțiuni automate, vizualizări Kanban) care se bazează pe etapele originale continuă să funcționeze fără probleme.
* **Flexibilitate:** Permite definirea unor procese de business complexe în motorul de flux, care apoi sunt sincronizate cu stările native ale recordurilor.
* **Sincronizare Bidirecțională:** Motorul de flux acționează ca un "gardian". O schimbare de etapă inițiată prin butoanele de workflow este validată și sincronizată cu etapa nativă. Invers, o schimbare a etapei native (ex: prin drag-and-drop în Kanban) este interceptată și validată de regulile motorului de flux înainte de a fi permisă.

---

## Funcționalități Principale

### 1. Motor de Flux Abstract și Extensibil
Logica este complet abstractizată, permițând integrarea cu orice model Odoo printr-un mecanism de moștenire (`workflow.mixin`).

### 2. Fluxuri, Etape și Tranziții Dinamice
Utilizatorii pot defini vizual, din interfața Odoo:
- **Fluxuri (`workflow.flow`):** Un proces de business, legat de un model specific (ex: `crm.lead`).
- **Etape de Workflow (`workflow.stage`):** Pașii individuali ai procesului personalizat.
- **Tranziții (`workflow.transition`):** Căile permise între etapele de workflow.

### 3. Constrângeri Avansate la Tranziții
Pentru a condiționa trecerea între etape, se poate defini un set de constrângeri pe fiecare tranziție.
- **Domeniu de validare:** Fiecare constrângere folosește un widget de domeniu Odoo, permițând crearea de reguli complexe (ex: `[('expected_revenue', '>', 10000)]`).
- **Mesaj de eroare personalizat:** Dacă un record nu îndeplinește condițiile, tranziția este blocată și se afișează un mesaj de eroare specific.
- **Control pe bază de Grupuri:** Tranzițiile pot fi restricționate doar pentru anumite grupuri de utilizatori.

### 4. Acțiuni Automate la Intrarea în Etape
La intrarea cu succes a unui record într-o etapă nouă, se pot declanșa automat una sau mai multe Acțiuni Server Odoo.

### 5. Mapare Vizuală a Etapelor
Un ecran dedicat în formularul de flux permite utilizatorilor să mapeze fiecare etapă din `workflow.stage` la o etapă nativă corespunzătoare a modelului țintă (ex: se leagă etapa de workflow "Calificat" de etapa nativă CRM "Qualification").

---

## Configurare și Utilizare

1.  **Navigați la `Settings -> Technical -> Workflow Engine -> Flows`.**
2.  **Creați un nou flux:**
    * Dați-i un nume (ex: "Proces Vânzare Corporate").
    * Selectați Modelul (`ir.model`) pe care se va aplica (ex: `crm.lead`).
3.  **Definiți Etapele de Workflow** în tab-ul "Stages".
4.  **Definiți Mapările** în tab-ul "Stage Mappings":
    * Pentru fiecare etapă de workflow creată, selectați etapa nativă corespunzătoare din modelul țintă. Acesta este un pas critic.
5.  **Definiți Tranzițiile și Constrângerile** în tab-ul "Transitions".

---

## Cum se Extinde pe un Modul Nou (Ghid pentru Dezvoltatori)

Pentru a aplica motorul de flux pe un model nou (ex: `helpdesk.ticket`), urmați pașii de mai jos.

1.  **Creați un nou modul "bridge"** (ex: `helpdesk_workflow_engine`) care depinde de `helpdesk` și `base_workflow_engine`.

2.  **Moșteniți `workflow.mixin` în modelul țintă:**
    * **IMPORTANT:** NU suprascrieți câmpul `stage_id` nativ. Arhitectura de mapare se bazează pe păstrarea acestuia intact.

    ```python
    # în helpdesk_workflow_engine/models/helpdesk_ticket.py
    from odoo import models, fields, api

    class HelpdeskTicket(models.Model):
        _name = 'helpdesk.ticket'
        _inherit = ['helpdesk.ticket', 'workflow.mixin']

        # Câmpul nativ `stage_id` rămâne neatins.
        # Mixin-ul adaugă în paralel câmpul `workflow_stage_id`.

        # Implementați logica pentru a găsi fluxul corect.
        @api.depends('team_id', 'company_id') # Adăugați câmpurile relevante
        def _compute_workflow(self):
            """ Găsește fluxul corespunzător pentru acest tichet. """
            for record in self:
                workflow = self.env['workflow.flow'].search([
                    ('model_name', '=', 'helpdesk.ticket'),
                    # Puteți adăuga condiții suplimentare aici
                ], limit=1)
                record.workflow_id = workflow.id

        def get_possible_transitions(self):
            """ Metodă ajutătoare pentru a afișa butoane în vizualizare. """
            if not self.workflow_stage_id:
                return []
            return self.workflow_stage_id.transition_ids

        def execute_transition(self, transition_id):
            """ Metodă apelată de butonul din vizualizare. """
            transition = self.env['workflow.transition'].browse(transition_id)
            self._execute_transition(transition.to_stage_id)

    ```

3.  **Adaptați vizualizările** pentru a adăuga butoane de acțiune pentru workflow.

    ```xml
    <record id="helpdesk_ticket_view_form_inherit_workflow" model="ir.ui.view">
        <field name="name">helpdesk.ticket.form.inherit.workflow</field>
        <field name="model">helpdesk.ticket</field>
        <field name="inherit_id" ref="helpdesk.helpdesk_ticket_view_form"/>
        <field name="arch" type="xml">
            <xpath expr="//header" position="inside">
                <button 
                    t-foreach="record.get_possible_transitions()"
                    t-as="transition"
                    t-att-name="execute_transition"
                    t-att-context="{'transition_id': transition.id}"
                    t-att-string="transition.name"
                    type="object"
                    class="btn-primary"
                />
            </xpath>
            <field name="team_id" position="after">
                <field name="workflow_id"/>
                <field name="workflow_stage_id" readonly="1"/>
            </field>
        </field>
    </record>
    ```

4.  **Configurați Datele:**
    * Asigurați-vă că etapele native (`helpdesk.stage`) există.
    * Creați un nou flux pentru `helpdesk.ticket`.
    * Creați etapele de workflow și, cel mai important, **mapările** între etapele de workflow și etapele native `helpdesk.stage`.

5.  **Instalați noul modul `helpdesk_workflow_engine`**.