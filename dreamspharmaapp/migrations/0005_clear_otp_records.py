# Generated migration to clear OTP records before field alteration

from django.db import migrations, models


def clear_otp_records(apps, schema_editor):
    """Clear all OTP records"""
    OTP = apps.get_model('dreamspharmaapp', 'OTP')
    OTP.objects.all().delete()


def reverse_clear_otp_records(apps, schema_editor):
    """Reverse operation - nothing to do"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('dreamspharmaapp', '0003_remove_otp_contact_info_remove_otp_otp_type_and_more'),
    ]

    operations = [
        migrations.RunPython(clear_otp_records, reverse_clear_otp_records),
        migrations.AlterField(
            model_name='otp',
            name='otp_code',
            field=models.CharField(max_length=4),
        ),
    ]
