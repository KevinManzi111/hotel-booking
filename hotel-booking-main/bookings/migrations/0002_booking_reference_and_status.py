from django.db import migrations, models
from django.utils import timezone
import bookings.models

def populate_references(apps, schema_editor):
    Booking = apps.get_model("bookings", "Booking")
    for booking in Booking.objects.all().iterator():
        booking.reference = bookings.models.generate_booking_reference()
        booking.save(update_fields=["reference"])

class Migration(migrations.Migration):
    dependencies = [("bookings", "0001_initial")]
    operations = [
        migrations.AddField(model_name="booking", name="reference", field=models.CharField(blank=True, db_index=True, max_length=16, null=True)),
        migrations.AddField(model_name="booking", name="updated_at", field=models.DateTimeField(default=timezone.now)),
        migrations.AlterField(model_name="booking", name="status", field=models.CharField(choices=[("pending", "Pending"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled"), ("completed", "Completed")], default="confirmed", max_length=12)),
        migrations.RunPython(populate_references, migrations.RunPython.noop),
        migrations.AlterField(model_name="booking", name="reference", field=models.CharField(db_index=True, default=bookings.models.generate_booking_reference, editable=False, max_length=16, unique=True)),
        migrations.AlterField(model_name="booking", name="updated_at", field=models.DateTimeField(auto_now=True)),
    ]
