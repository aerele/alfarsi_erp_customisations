import frappe


def execute():

    item_groups = frappe.get_all(
        "Item Group",
        filters={"route": ["like", "%medical/medical-laboratory%"]},
        fields=["name", "route"]
    )

    for ig in item_groups:
        old_route = ig.route
        new_route = old_route.replace("medical/medical-laboratory", "medical-laboratory")

        if new_route != old_route:
            doc = frappe.get_doc("Item Group", ig.name)
            doc.route = new_route
            doc.save()

    item_group_list = [
        'Medical Laboratory IVD', 'Clinical Chemistry', 'Clinical Chemistry Controls & Calibrators',
        'Clinical Chemistry Equipments', 'Clinical Chemistry Reagents', 'Genomics Molecular Testing',
        'Genomics Molecular Consumables', 'Genomics Molecular Equipments', 'Genomics Molecular Reagents',
        'VTM Swabs', 'Hematology', 'Hematology Controls & Calibrators', 'Hematology Equipment',
        'Hematology Reagents', 'ImmunoChemistry', 'ImmunoChemistry Control & Calibrators',
        'ImmunoChemistry Equipments', 'ImmunoChemistry Reagents', 'IVD UA', 'Lab Furniture',
        'Laboratory Equipment', 'Laboratory Centrifuges', 'Laboratory Glassware', 'Beakers', 'Flasks',
        'Funnels', 'Laboratory Supplies', 'IVD Supplies', 'Pipettes & Pipette Tips', 'Tubes',
        'Microbiology', 'Antibiotic Sensitivity Discs', 'Culture Media', 'Microbiology Equipements',
        'Petri Dish and Petrifilm', 'Pathology & Histology', 'Staining Solutions', 'Urinalysis',
        'Point of Care', 'Rapid Diagnostic Test Kits', 'Serology'
    ]

    website_items = frappe.get_all(
        "Website Item",
        filters={"item_group": ["in", item_group_list]},
        fields=["name", "route"]
    )

    for wi in website_items:
        if wi.route and "medical/medical-laboratory" in wi.route:
            new_route = wi.route.replace("medical/medical-laboratory", "medical-laboratory")
            doc = frappe.get_doc("Website Item", wi.name)
            doc.route = new_route
            doc.save()
