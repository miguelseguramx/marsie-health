from django.db import migrations

# code, name_es, name_en, default_unit, category, loinc_code
ANALYTES = [
    ("HCT", "Hematocrito", "Hematocrit", "%", "red_cells", "4544-3"),
    ("HGB", "Hemoglobina", "Hemoglobin", "g/dL", "red_cells", "718-7"),
    ("RBC", "Glóbulos rojos", "Red blood cells", "10^6/uL", "red_cells", "789-8"),
    ("MCV", "VCM", "Mean corpuscular volume", "fL", "red_indices", "787-2"),
    ("MCH", "HCM", "Mean corpuscular hemoglobin", "pg", "red_indices", "785-6"),
    ("MCHC", "CHCM", "Mean corpuscular hemoglobin concentration", "%", "red_indices", "786-4"),
    ("RDW", "RDW", "Red cell distribution width", "%", "red_indices", "788-0"),
    ("WBC", "Glóbulos blancos", "White blood cells", "10^3/uL", "white_cells", "6690-2"),
    ("NEUT_PCT", "Neutrófilos", "Neutrophils percent", "%", "white_cells", "770-8"),
    ("LYMPH_PCT", "Linfocitos", "Lymphocytes percent", "%", "white_cells", "736-9"),
    ("MONO_PCT", "Monocitos", "Monocytes percent", "%", "white_cells", "5905-5"),
    ("EOS_PCT", "Eosinófilos", "Eosinophils percent", "%", "white_cells", "713-8"),
    ("BASO_PCT", "Basófilos", "Basophils percent", "%", "white_cells", "706-2"),
    ("PLT", "Recuento plaquetario", "Platelets", "10^3/uL", "platelets", "777-3"),
]


def seed_analytes(apps, schema_editor):
    Analyte = apps.get_model("lab_results", "Analyte")
    for code, name_es, name_en, unit, category, loinc in ANALYTES:
        Analyte.objects.update_or_create(
            code=code,
            defaults={
                "name_es": name_es,
                "name_en": name_en,
                "default_unit": unit,
                "category": category,
                "loinc_code": loinc,
            },
        )


def remove_analytes(apps, schema_editor):
    Analyte = apps.get_model("lab_results", "Analyte")
    Analyte.objects.filter(code__in=[a[0] for a in ANALYTES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("lab_results", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_analytes, remove_analytes),
    ]
