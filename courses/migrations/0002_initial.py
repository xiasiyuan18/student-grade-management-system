

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('courses', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseenrollment',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_enrollments', to='users.student', verbose_name='学生'),
        ),
        migrations.AddField(
            model_name='teachingassignment',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='courses.course', verbose_name='所授课程'),
        ),
        migrations.AddField(
            model_name='teachingassignment',
            name='teacher',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='users.teacher', verbose_name='授课教师'),
        ),
        migrations.AddField(
            model_name='courseenrollment',
            name='teaching_assignment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='courses.teachingassignment', verbose_name='授课安排'),
        ),
        migrations.AlterUniqueTogether(
            name='teachingassignment',
            unique_together={('teacher', 'course', 'semester')},
        ),
        migrations.AlterUniqueTogether(
            name='courseenrollment',
            unique_together={('student', 'teaching_assignment')},
        ),
    ]
