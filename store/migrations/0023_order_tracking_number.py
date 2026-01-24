from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0022_fix_variant_sizes'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='tracking_number',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Nomor Resi'),
        ),
        migrations.AddField(
            model_name='order',
            name='shipped_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Tanggal Pengiriman'),
        ),
    ]
