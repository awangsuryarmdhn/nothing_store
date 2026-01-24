# Generated manually - add midtrans_order_id field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0024_simplify_order_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='midtrans_order_id',
            field=models.CharField(blank=True, help_text='ID transaksi di Midtrans untuk lookup status', max_length=100, null=True, verbose_name='Midtrans Order ID'),
        ),
    ]
