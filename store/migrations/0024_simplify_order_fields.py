from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0023_order_tracking_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='first_name',
            field=models.CharField(max_length=50, verbose_name='Nama Lengkap'),
        ),
        migrations.AlterField(
            model_name='order',
            name='address',
            field=models.CharField(max_length=250, verbose_name='Alamat Lengkap'),
        ),
        migrations.AlterField(
            model_name='order',
            name='last_name',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Nama Belakang'),
        ),
        migrations.AlterField(
            model_name='order',
            name='postal_code',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Kode Pos'),
        ),
    ]
