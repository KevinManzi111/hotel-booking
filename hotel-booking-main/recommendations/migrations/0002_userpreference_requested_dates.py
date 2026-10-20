from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("recommendations", "0001_initial")]
    operations = [
        migrations.AddField(model_name="userpreference", name="requested_check_in", field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name="userpreference", name="requested_check_out", field=models.DateField(blank=True, null=True)),
    ]
