import pytest
from django.contrib.auth.models import Group

from apps.lab_results.models import Analyte


@pytest.mark.django_db
def test_role_groups_are_seeded():
    names = set(Group.objects.values_list("name", flat=True))
    assert {"Patient", "Physician", "LabAdmin"}.issubset(names)


@pytest.mark.django_db
def test_all_14_cbc_analytes_are_seeded():
    expected = {
        "HCT",
        "HGB",
        "RBC",
        "MCV",
        "MCH",
        "MCHC",
        "RDW",
        "WBC",
        "NEUT_PCT",
        "LYMPH_PCT",
        "MONO_PCT",
        "EOS_PCT",
        "BASO_PCT",
        "PLT",
    }
    assert set(Analyte.objects.values_list("code", flat=True)) == expected


@pytest.mark.django_db
def test_analytes_have_categories_assigned():
    by_category = {}
    for code, category in Analyte.objects.values_list("code", "category"):
        by_category.setdefault(category, set()).add(code)
    assert {"HCT", "HGB", "RBC"} <= by_category["red_cells"]
    assert {"MCV", "MCH", "MCHC", "RDW"} <= by_category["red_indices"]
    assert {"WBC", "NEUT_PCT", "LYMPH_PCT", "MONO_PCT", "EOS_PCT", "BASO_PCT"} <= by_category[
        "white_cells"
    ]
    assert {"PLT"} <= by_category["platelets"]
