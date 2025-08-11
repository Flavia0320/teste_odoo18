# Base Workflow Engine pentru Odoo 18

Acest modul oferă o fundație tehnică pentru crearea de fluxuri de lucru (workflows) dinamice și condiționate, aplicabile oricărui model din Odoo. A fost conceput pentru a fi abstract, flexibil și ușor de extins, permițând definirea de etape, tranziții, reguli de acces, constrângeri și acțiuni automate.

## Funcționalități Principale

### 1. Motor de Flux Abstract și Extensibil
Modulul nu depinde de nicio aplicație de business (CRM, Proiect, etc.). Logica este complet abstractizată, permițând integrarea cu orice model Odoo printr-un mecanism de moștenire (mixin).

### 2. Fluxuri, Etape și Tranziții Dinamice
Utilizatorii pot defini vizual, din interfața Odoo:
- **Fluxuri (`workflow.flow`):** Un container pentru un proces de business, legat de un model specific (ex: `crm.lead`).
- **Etape (`workflow.stage`):** Pașii individuali ai unui flux (ex: Nou, Calificare, Propunere, Câștigat).
- **Tranziții (`workflow.transition`):** Regulile care dictează mișcarea permisă între etape (ex: de la "Calificare" se poate trece doar la "Propunere" sau "Pierdut").

### 3. Constrângeri la Intrarea în Etape (Cerința #2)
Pentru a condiționa trecerea într-o nouă etapă, se poate defini un set de constrângeri.
- **Domeniu de validare:** Fiecare constrângere folosește un widget de domeniu Odoo, permițând crearea de reguli complexe bazate pe câmpurile modelului țintă (ex: `['|', ('email', '!=', False), ('phone', '!=', False)]`).
- **Mesaj de eroare personalizat:** Dacă un record nu îndeplinește condițiile domeniului, tranziția este blocată și se afișează un mesaj de eroare specificat de utilizator.
- **Tip de constrângere:** Poate fi `Restrict` (blochează) sau `Warning` (doar avertizează).

### 4. Acțiuni Server Automate la Intrarea în Etape (Cerința #4)
La intrarea cu succes a unui record într-o etapă nouă, se pot declanșa automat una sau mai multe Acțiuni Server. Acestea pot fi folosite pentru:
- Trimiterea de email-uri (template-uri de email).
- Crearea de activități pentru anumiți utilizatori.
- Executarea de cod Python pentru logică de business avansată.

### 5. Controlul Accesului pe Bază de Grupuri (Cerința #6)
Fiecare etapă are un câmp `Allowed Groups`. Doar utilizatorii care aparțin grupurilor specificate în acest câmp pot muta un record *din* etapa respectivă. Acest mecanism asigură că doar personalul autorizat poate avansa un proces.

### 6. Tranziții Automate (Opțional - Cerința #7)
Modulul include o logică de bază pentru automatizarea tranzițiilor. Dacă un record se află într-o etapă care are o singură tranziție posibilă și toate constrângerile pentru etapa următoare sunt îndeplinite, sistemul poate muta automat recordul la pasul următor. Această funcționalitate poate fi activată sau extinsă printr-o acțiune automată (`ir.cron`).

## Configurare și Utilizare

1.  **Navigați la `Workflow Engine -> Configuration -> Workflows`.**
2.  **Creați un nou flux:**
    -   Dați-i un nume (ex: "Proces Vânzare Lead-uri").
    -   Selectați Modelul (`ir.model`) pe care se va aplica (ex: `crm.lead`).
3.  **Definiți Etapele în tab-ul "Stages & Transitions":**
    -   Creați fiecare etapă necesară (Nou, Contactat, Negociere, etc.).
    -   Stabiliți ordinea cu ajutorul `drag-and-drop` (handle-ul de secvență).
    -   Bifați `Is Final Stage` pentru etapele terminale.
    -   În formularul fiecărei etape, puteți adăuga **Constrângeri**, **Acțiuni Server** și **Grupuri Permise**.
4.  **Definiți Tranzițiile:**
    -   În formularul unei etape, mergeți la tab-ul "Allowed Transitions" și adăugați etapele următoare permise.

## Cum se Extinde pe un Modul Nou (Exemplu: `fleet.vehicle`)

Pentru a aplica motorul de flux pe un model nou, urmați pașii de mai jos.

1.  **Creați un nou modul "bridge"** (ex: `fleet_workflow_engine`) care depinde de `fleet` și `base_workflow_engine`.

2.  **Moșteniți `workflow.mixin` în modelul țintă:**

    ```python
    # In fleet_workflow_engine/models/fleet_vehicle.py
    from odoo import models, fields, api

    class FleetVehicle(models.Model):
        _name = 'fleet.vehicle'
        _inherit = ['fleet.vehicle', 'workflow.mixin']

        # 1. Suprascrieți câmpul de etapă standard cu cel din workflow.
        #    Numele câmpului trebuie să fie 'stage_id' pentru ca mixin-ul
        #    să funcționeze corect.
        stage_id = fields.Many2one(
            'workflow.stage',
            string='Stage',
            ondelete='restrict',
            tracking=True,
            domain="[('flow_id', '=', workflow_id)]",
            copy=False,
            index=True,
            group_expand='_read_group_stage_ids' # Necesar pentru vizualizarea Kanban
        )

        # 2. Implementați logica pentru a găsi fluxul corect.
        @api.depends('company_id') # Adăugați câmpurile relevante
        def _compute_workflow(self):
            """ Găsește fluxul corespunzător pentru acest vehicul. """
            for record in self:
                # Căutați un flux definit pentru modelul 'fleet.vehicle'
                workflow = self.env['workflow.flow'].search([
                    ('model_name', '=', 'fleet.vehicle'),
                    # Puteți adăuga condiții suplimentare, ex: pe companie
                    # ('company_id', '=', record.company_id.id)
                ], limit=1)
                record.workflow_id = workflow.id

        # 3. Suprascrieți metoda read_group pentru a afișa etapele în Kanban.
        @api.model
        def _read_group_stage_ids(self, stages, domain, order):
            """ Returnează etapele pentru vizualizarea Kanban. """
            # Găsiți fluxul cel mai probabil pe baza contextului/domeniului
            workflow = self.env['workflow.flow'].search([
                ('model_name', '=', 'fleet.vehicle')
            ], limit=1)
            if workflow:
                return workflow.stage_ids
            return self.env['workflow.stage'].search([])
    ```

3.  **Adaptați vizualizările** pentru a folosi noul câmp `stage_id` și, opțional, pentru a afișa `workflow_id`.

4.  **Instalați noul modul `fleet_workflow_engine`**.

## Autor

Dakai SOFT SRL