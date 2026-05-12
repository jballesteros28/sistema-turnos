from django.db import migrations


def migrar_dias_semana(apps, schema_editor):
    Disponibilidad = apps.get_model("disponibilidad", "Disponibilidad")
    disponibilidades = []

    for disponibilidad in Disponibilidad.objects.all():
        dia_semana = disponibilidad.dia_semana
        if isinstance(dia_semana, int) and 0 <= dia_semana <= 6:
            disponibilidad.dias_semana = [dia_semana]
        else:
            disponibilidad.dias_semana = []
        disponibilidades.append(disponibilidad)

    if disponibilidades:
        Disponibilidad.objects.bulk_update(disponibilidades, ["dias_semana"])


def revertir_dias_semana(apps, schema_editor):
    Disponibilidad = apps.get_model("disponibilidad", "Disponibilidad")
    disponibilidades = []

    for disponibilidad in Disponibilidad.objects.all():
        dias_semana = disponibilidad.dias_semana or []
        if dias_semana:
            try:
                dia_semana = int(dias_semana[0])
            except (TypeError, ValueError):
                continue
            if 0 <= dia_semana <= 6:
                disponibilidad.dia_semana = dia_semana
                disponibilidades.append(disponibilidad)

    if disponibilidades:
        Disponibilidad.objects.bulk_update(disponibilidades, ["dia_semana"])


class Migration(migrations.Migration):

    dependencies = [
        ("disponibilidad", "0002_disponibilidad_dias_semana"),
    ]

    operations = [
        migrations.RunPython(migrar_dias_semana, revertir_dias_semana),
    ]
