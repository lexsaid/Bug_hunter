from django.db import migrations


CRITERIA = [
    "Identificador del CU.",
    "Nombre claro.",
    "Actor definido.",
    "Descripción clara.",
    "Precondiciones definidas.",
    "Poscondiciones definidas.",
    "Flujo principal numerado.",
    "Pasos claros.",
    "Flujo lógico.",
    "Sin ambigüedades.",
    "Actor inicia acciones.",
    "Sistema responde acciones.",
    "Flujo alterno definido.",
    "Flujo de error definido.",
    "Lenguaje consistente.",
    "Nivel de detalle adecuado.",
    "Relación con otros CU.",
    "Actores correctamente definidos.",
    "Objetivo del CU claro.",
    "Caso de uso completo.",
]


def populate_v2_checklist(apps, schema_editor):
    Checklist = apps.get_model("checklist", "Checklist")
    Criterio = apps.get_model("checklist", "Criterio")
    database = schema_editor.connection.alias

    checklists = Checklist.objects.using(database).all()
    for checklist in checklists:
        normalized_name = " ".join(checklist.nombre.split()).casefold()
        if normalized_name != "caminata (casos de uso srs v2 )":
            continue

        criterios = list(
            Criterio.objects.using(database)
            .filter(checklist_id=checklist.pk)
            .order_by("creado_en", "pk")
        )

        for index, descripcion in enumerate(CRITERIA):
            if index < len(criterios):
                criterio = criterios[index]
                criterio.descripcion = descripcion
                criterio.estado = "cumple"
                criterio.observaciones = ""
                criterio.save(
                    using=database,
                    update_fields=["descripcion", "estado", "observaciones"],
                )
            else:
                Criterio.objects.using(database).create(
                    checklist_id=checklist.pk,
                    descripcion=descripcion,
                    estado="cumple",
                    observaciones="",
                )


class Migration(migrations.Migration):

    dependencies = [
        ("checklist", "0004_populate_use_case_walkthrough"),
    ]

    operations = [
        migrations.RunPython(
            populate_v2_checklist,
            migrations.RunPython.noop,
        ),
    ]
