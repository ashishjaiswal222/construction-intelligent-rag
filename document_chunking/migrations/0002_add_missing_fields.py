# Generated manually

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('document_chunking', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chunkingjob',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('PROCESSING', 'Processing'), ('COMPLETED', 'Completed'), ('FAILED', 'Failed'), ('PARTIAL', 'Partial'), ('AGGREGATING', 'Aggregating')], default='PENDING', max_length=20),
        ),
        migrations.AddField(
            model_name='documentchunk',
            name='is_current',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AddField(
            model_name='documentchunk',
            name='doc_type',
            field=models.CharField(blank=True, db_index=True, max_length=50),
        ),
        migrations.AddField(
            model_name='documentchunk',
            name='revision',
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
