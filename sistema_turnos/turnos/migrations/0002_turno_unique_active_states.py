# Generated manually to align active appointment uniqueness with business rules.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("turnos", "0001_initial"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="turno",
            name="uniq_turno_prof_inicio_act",
        ),
        migrations.AddConstraint(
            model_name="turno",
            constraint=models.UniqueConstraint(
                condition=models.Q(estado__in=["solicitado", "confirmado"]),
                fields=("profesional", "fecha_hora_inicio"),
                name="uniq_turno_prof_inicio_act",
            ),
        ),
    ]
