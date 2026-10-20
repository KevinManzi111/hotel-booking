from django.db import migrations, models
from django.utils import timezone
import hotels.models

def populate_identifiers(apps, schema_editor):
    Room = apps.get_model("hotels", "Room")
    for room in Room.objects.all().iterator():
        room.identifier = hotels.models.generate_room_identifier()
        room.save(update_fields=["identifier"])

class Migration(migrations.Migration):
    dependencies = [("hotels", "0001_initial")]
    operations = [
        migrations.AddField(model_name="room", name="identifier", field=models.CharField(blank=True, max_length=40, null=True)),
        migrations.AddField(model_name="room", name="image", field=models.ImageField(blank=True, upload_to="rooms/%Y/%m/")),
        migrations.AddField(model_name="room", name="status", field=models.CharField(choices=[("available", "Available"), ("maintenance", "Maintenance"), ("inactive", "Inactive")], db_index=True, default="available", max_length=16)),
        migrations.AddField(model_name="room", name="created_at", field=models.DateTimeField(default=timezone.now)),
        migrations.AddField(model_name="room", name="updated_at", field=models.DateTimeField(default=timezone.now)),
        migrations.RunPython(populate_identifiers, migrations.RunPython.noop),
        migrations.AlterField(model_name="room", name="identifier", field=models.CharField(default=hotels.models.generate_room_identifier, help_text="Unique room number or inventory code", max_length=40, unique=True)),
        migrations.AlterField(model_name="room", name="created_at", field=models.DateTimeField(auto_now_add=True)),
        migrations.AlterField(model_name="room", name="updated_at", field=models.DateTimeField(auto_now=True)),
        migrations.RemoveField(model_name="room", name="active"),
        migrations.RemoveField(model_name="room", name="total_rooms"),
        migrations.AddConstraint(model_name="room", constraint=models.UniqueConstraint(fields=("hotel", "identifier"), name="unique_hotel_room_identifier")),
    ]
