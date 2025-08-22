# Documentație Tehnică: Base Workflow Engine

Acest document oferă o perspectivă detaliată asupra arhitecturii, conceptelor și modului de extindere a modulului **Base Workflow Engine**. Este destinat dezvoltatorilor care doresc să înțeleagă, să contribuie sau să integreze acest motor de flux în alte aplicații Odoo.

---

## 1. Scopul și Sinteza Modulului

**Scopul principal** al acestui modul este de a oferi un motor de flux de lucru (workflow engine) care să permită definirea și impunerea unor procese de business complexe, fiind în același timp **flexibil, robust și complet non-intruziv**.

Spre deosebire de abordările care înlocuiesc funcționalități de bază, acest modul este proiectat să funcționeze **în paralel** cu mecanismele native Odoo, acționând ca un strat de validare și orchestrare care respectă integritatea platformei. Permite dezvoltatorilor să adauge logică de business avansată fără a rescrie sau a risca defectarea funcționalităților standard.

---

## 2. Arhitectura Centrală: Principiul de Funcționare

Principiul fundamental este cel al **mapării non-intruzive**. Motorul de flux nu înlocuiește câmpul nativ de etape (`stage_id`) al unui model, ci introduce un câmp paralel (`workflow_stage_id`) și menține o sincronizare constantă între cele două, validând fiecare mișcare.

Acest mecanism funcționează ca un **"gardian"** al procesului.

### Fluxul de Sincronizare

Există două scenarii principale în care motorul acționează:

#### a. Tranziție Inițiată de Workflow (Ex: Click pe un Buton Custom)
1.  Utilizatorul apasă un buton de acțiune (ex: "Aprobă").
2.  Butonul apelează o metodă pe modelul Python (ex: `execute_transition`).
3.  Această metodă, la rândul ei, apelează metoda centrală `_execute_transition` din `workflow.mixin`.
4.  `_execute_transition` efectuează validările în ordine:
    * Verifică dacă tranziția de la etapa curentă la cea nouă este permisă.
    * Evaluează toate constrângerile (`workflow.constraint`) asociate cu acea tranziție.
5.  Dacă toate validările trec:
    * Se actualizează câmpul `workflow_stage_id` al recordului.
    * Se caută etapa nativă corespunzătoare în modelul de mapare (`workflow.stage.mapping`).
    * Se actualizează câmpul nativ `stage_id` al recordului, pentru a reflecta vizual schimbarea în interfața Odoo (ex: Kanban).

#### b. Tranziție Inițiată Nativ (Ex: Drag-and-Drop în Kanban)
1.  Utilizatorul trage un card dintr-o coloană în alta. Această acțiune declanșează un apel la metoda `write` pe record, încercând să modifice câmpul nativ `stage_id`.
2.  Metoda `write` din `workflow.mixin` **interceptează** acest apel înainte ca schimbarea să fie salvată în baza de date.
3.  Logica din `write` folosește o mapare inversă (`reverse_mapping`) pentru a identifica ce `workflow_stage_id` corespunde noii etape native.
4.  Odată identificată tranziția de workflow, se apelează aceeași metodă centrală `_execute_transition` pentru a rula setul complet de validări (pașii de la punctul anterior).
5.  Dacă validările eșuează, metoda `write` ridică o excepție (`UserError` sau `ValidationError`), **anulând operațiunea de drag-and-drop** și afișând utilizatorului mesajul de eroare relevant. Dacă validările trec, scrierea este permisă.

Astfel, indiferent de calea aleasă de utilizator, regulile de business definite în flux sunt întotdeauna respectate.

---

## 3. Fundamentarea Conceptelor (Componentele Modulului)

Fiecare model din `base_workflow_engine` are un rol precis în această arhitectură.

### `workflow.flow`
* **Ce este?** Containerul principal pentru un proces de business.
* **Rol Tehnic:** Este rădăcina unui graf de stări. Câmpul său cel mai important este `model_name`, care specifică pe ce model Odoo (`res.model`) se vor aplica regulile fluxului. De asemenea, centralizează toate celelalte componente (etape, tranziții, mapări) printr-o relație `One2many`.

### `workflow.stage`
* **Ce este?** Un nod în graful de stări; reprezintă o etapă discretă în procesul personalizat.
* **Rol Tehnic:** Este un simplu record care definește o stare. Câmpurile `is_entry` (boolean) și `is_stop` (boolean, calculat) definesc punctele de început și de sfârșit ale fluxului. Fiecare `workflow.stage` este independent de etapele native Odoo până în momentul mapării.

### `workflow.stage.mapping`
* **Ce este?** "Adaptorul" sau "puntea de legătură" între motorul de flux și Odoo nativ.
* **Rol Tehnic:** Acesta este un model esențial care stochează o pereche formată dintr-un `workflow_stage_id` și un `native_stage_id`. Câmpul `native_stage_id` este de tip `Reference`, ceea ce îi permite să se lege la orice model de etape din Odoo (`crm.stage`, `project.task.type`, etc.), făcând motorul extrem de generic. Constrângerile SQL asigură că o etapă (atât de workflow, cât și nativă) nu poate fi mapată de mai multe ori în cadrul aceluiași flux.

### `workflow.transition`
* **Ce este?** O muchie orientată în graful de stări; definește o cale permisă între două `workflow.stage`.
* **Rol Tehnic:** O tranziție este definită de `from_stage_id` și `to_stage_id`. Rolul său principal este de a acționa ca un container pentru `constraint_ids`, permițând aplicarea regulilor de validare pe o anumită cale, nu pe o etapă în ansamblu.

### `workflow.constraint`
* **Ce este?** O regulă de business atomică, condiția care trebuie îndeplinită pentru a permite o tranziție.
* **Rol Tehnic:** Inima logicii de validare. Câmpul `domain` este un string care este evaluat în siguranță (`safe_eval`) în contextul recordului curent. Câmpul `error_message` oferă feedback esențial utilizatorului. Acest model decuplează definirea regulilor de codul Python, permițând configurarea lor direct din interfață.

### `workflow.mixin`
* **Ce este?** O clasă abstractă Python care injectează comportamentul de workflow în orice model Odoo.
* **Rol Tehnic:** Este componenta care implementează principiul de funcționare. Responsabilitățile sale cheie sunt:
    * Adăugarea câmpurilor paralele `workflow_id` și `workflow_stage_id` pe modelul țintă.
    * Suprascrierea metodelor `create` și `write` pentru a intercepta modificările și a impune validările.
    * Furnizarea metodei `_execute_transition`, care orchestrează validarea și sincronizarea stărilor.
    * Gestionarea mapărilor prin metoda ajutătoare `_get_mapping`.

---

## 4. Ghid de Extindere pentru Dezvoltatori

Urmați acești pași pentru a integra motorul de flux pe un nou model (ex: `helpdesk.ticket`).

1.  **Creați un modul "bridge"**: Acesta va depinde de modulul țintă (`helpdesk`) și de `base_workflow_engine`.

2.  **Moșteniți `workflow.mixin`**: Creați un fișier Python pentru a extinde modelul țintă. **Nu suprascrieți `stage_id`!**

    ```python
    # în helpdesk_workflow_engine/models/helpdesk_ticket.py
    from odoo import models, fields, api

    class HelpdeskTicket(models.Model):
        _name = 'helpdesk.ticket'
        _inherit = ['helpdesk.ticket', 'workflow.mixin']

        # Câmpul nativ `stage_id` rămâne neatins.

        # Implementați logica pentru a găsi fluxul corect.
        @api.depends('team_id')
        def _compute_workflow(self):
            for record in self:
                # Logica poate fi oricât de complexă, ex: un flux per echipă
                workflow = self.env['workflow.flow'].search([
                    ('model_name', '=', 'helpdesk.ticket'),
                    # ('team_id', '=', record.team_id.id)
                ], limit=1)
                record.workflow_id = workflow.id

        def get_possible_transitions(self):
            """ Returnează tranzițiile posibile pentru a fi afișate ca butoane. """
            self.ensure_one()
            if not self.workflow_stage_id:
                return self.env['workflow.transition']
            return self.workflow_stage_id.transition_ids

        def execute_workflow_transition(self, transition_id):
            """ Metodă apelată de butonul din vizualizare, care declanșează logica centrală. """
            self.ensure_one()
            transition = self.env['workflow.transition'].browse(transition_id)
            self._execute_transition(transition.to_stage_id)
    ```

3.  **Adaptați Vizualizarea Formular**: Adăugați butoane pentru a permite utilizatorului să inițieze tranziții.

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
                    name="execute_workflow_transition"
                    t-att-context="{'transition_id': transition.id}"
                    t-att-string="transition.name"
                    type="object"
                    class="btn-primary"
                />
            </xpath>
            <field name="team_id" position="after">
                <field name="workflow_id" options="{'no_create': True}"/>
                <field name="workflow_stage_id" readonly="1" force_save="1"/>
            </field>
        </field>
    </record>
    ```

4.  **Configurați Datele din Interfață**:
    * Creați un nou `workflow.flow` pentru modelul `helpdesk.ticket`.
    * Definiți `workflow.stage`-urile dorite.
    * **Crucial**: Completați `workflow.stage.mapping` pentru a lega fiecare `workflow.stage` de un `helpdesk.stage` nativ.
    * Definiți `workflow.transition`-urile și `workflow.constraint`-urile necesare.