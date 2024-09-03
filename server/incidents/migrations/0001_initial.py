# Generated by Django 5.1 on 2024-09-03 20:38

import django.db.models.deletion
import phonenumber_field.modelfields
import server.incidents.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Includes file extension', max_length=100, unique=True)),
                ('data', models.BinaryField()),
            ],
        ),
        migrations.CreateModel(
            name='IncidentType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, default='')),
            ],
        ),
        migrations.CreateModel(
            name='Link',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, default='', max_length=100)),
                ('url', models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name='SourceType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, default='')),
            ],
        ),
        migrations.CreateModel(
            name='Extra',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('value', models.TextField()),
                ('attachment', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='extras', to='incidents.attachment')),
            ],
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(unique=True)),
                ('group', models.OneToOneField(help_text='The group that controls this region', on_delete=django.db.models.deletion.CASCADE, related_name='region', to='auth.group')),
            ],
        ),
        migrations.CreateModel(
            name='SchoolDistrict',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('url', models.URLField(blank=True)),
                ('twitter', models.URLField(blank=True, default='')),
                ('facebook', models.URLField(blank=True, default='')),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(blank=True, default='', max_length=128, region=None)),
                ('superintendent_name', models.CharField(max_length=100)),
                ('superintendent_email', models.EmailField(blank=True, max_length=254)),
                ('civil_rights_url', models.URLField(blank=True)),
                ('civil_rights_contact_name', models.CharField(blank=True, max_length=100)),
                ('civil_rights_contact_email', models.EmailField(blank=True, max_length=254)),
                ('hib_url', models.URLField(blank=True)),
                ('hib_form_url', models.URLField(blank=True)),
                ('hib_contact_name', models.CharField(blank=True, max_length=100)),
                ('hib_contact_email', models.EmailField(blank=True, max_length=254)),
                ('board_url', models.URLField(blank=True)),
                ('extras', models.ManyToManyField(blank=True, related_name='district_extras', to='incidents.extra')),
                ('logo', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='logos_of_districts', to='incidents.attachment')),
            ],
        ),
        migrations.CreateModel(
            name='School',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('url', models.URLField()),
                ('street', models.CharField(blank=True, max_length=100)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('state', models.CharField(blank=True, max_length=2)),
                ('zip_code', models.CharField(blank=True, max_length=5)),
                ('latitude', models.FloatField(blank=True, default=None, null=True)),
                ('longitude', models.FloatField(blank=True, default=None, null=True)),
                ('is_public', models.BooleanField()),
                ('is_elementary', models.BooleanField()),
                ('is_middle', models.BooleanField()),
                ('is_high', models.BooleanField()),
                ('extras', models.ManyToManyField(blank=True, related_name='school_extras', to='incidents.extra')),
                ('district', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='schools', to='incidents.schooldistrict')),
            ],
        ),
        migrations.CreateModel(
            name='Incident',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('notes', models.TextField(blank=True, default='', help_text='Administrative notes (never shown publicly)')),
                ('submitted_at', models.DateTimeField()),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('published_at', models.DateTimeField(blank=True, default=None, null=True)),
                ('occurred_at', server.incidents.fields.PartialDateField(help_text='When the incident occurred')),
                ('reported_to_school', models.BooleanField(default=False)),
                ('reported_at', server.incidents.fields.PartialDateField(default='')),
                ('school_responded_at', server.incidents.fields.PartialDateField(default='')),
                ('school_response', models.TextField(blank=True, default='')),
                ('extras', models.ManyToManyField(to='incidents.extra')),
                ('published_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='publisher', to=settings.AUTH_USER_MODEL)),
                ('school_response_materials', models.ManyToManyField(blank=True, related_name='school_response_materials', to='incidents.attachment')),
                ('supporting_materials', models.ManyToManyField(blank=True, related_name='supporting_materials', to='incidents.attachment')),
                ('incident_types', models.ManyToManyField(to='incidents.incidenttype')),
                ('related_links', models.ManyToManyField(blank=True, related_name='incidents', to='incidents.link')),
                ('region', models.ForeignKey(help_text='The region that this incident belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='incidents', to='incidents.region')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incidents', to='incidents.school')),
                ('source_types', models.ManyToManyField(to='incidents.sourcetype')),
            ],
        ),
    ]
