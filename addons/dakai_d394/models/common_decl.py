def months():
    return [
        ('1', 'Ianuarie'),
        ('2', 'Februarie'),
        ('3', 'Martie'),
        ('4', 'Aprilie'),
        ('5', 'Mai'),
        ('6', 'Iunie'),
        ('7', 'Iulie'),
        ('8', 'August'),
        ('9', 'Septembrie'),
        ('10', 'Octombrie'),
        ('11', 'Noiembrie'),
        ('12', 'Decembrie'),
        ]

def period():
    return [
        ('L', 'Lunar'),
        ('T', 'Trimestrial'),
        ('S', 'Semetrial'),
        ('A', 'Anual')
        ]

def sistemTVA():
    return [
        ('0', 'Sistem normal de TVA'),
        ('1', 'Sistem de TVA la incasare')
        ]

def tipPersoana():
    return [
        ('0', 'Persoana Juridica'),
        ('1', 'Persoana Fizica')
        ]

def inv_origin():
    return [
            ("1", "facturi"),
            ("2", "borderouri"),
            ("3", "file carnet comercializare"),
            ("4", "contracte"),
            ("5", "alte documente"),
        ]

def op_type():
    return [
            ("L", "[L] Customer Invoice"),
            ("A", "[A] Supplier Invoice"),
            ("LS", "[LS] Special Customer Invoice"),
            ("AS", "[AS] Special Supplier Invoice"),
            ("AI", "[AI] VAT on Payment Supplier Invoice"),
            ("V", "[V] Inverse Taxation Customer Invoice"),
            ("C", "[C] Inverse Taxation Supplier Invoice"),
            ("N", "[N] Fizical Persons Supplier Invoice"),
        ]

def partner_type():
    return [
            ("1", "[1] Inregistrat in scopuri de TVA"),
            ("2", "[2] Neinregistrat in scopuri de TVA"),
            ("3", "[3] Extern, neinregistrat/neobligat inregistrare in scopuri de TVA."),
            ("4", "[4] Extern UE, neinregistrat/neobligat inregistrare in scopuri de TVA."),
        ]

def sumed_columns():
    return {
        "total_base": ["base_19", "base_9", "base_5", "base_exig"],
        "total_vat": ["tva_19", "tva_9", "tva_5", "tva_exig"],
    }

def journal_sequence_type():
    return [
        ("normal", "Invoice"),
        ("autoinv1", "Customer Auto Invoicing"),
        ("autoinv2", "Supplier  Auto Invoicing")
    ]
