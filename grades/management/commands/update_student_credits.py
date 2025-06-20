from django.core.management.base import BaseCommand
from users.models import Student
from grades.services import calculate_and_update_student_credits

class Command(BaseCommand):
    help = '为所有学生重新计算并更新学分统计'

    def add_arguments(self, parser):
        parser.add_argument(
            '--student-id',
            type=str,
            help='指定学号，只更新特定学生的学分（可选）',
        )

    def handle(self, *args, **options):
        if options['student_id']:
            # 更新特定学生
            try:
                student = Student.objects.get(student_id_num=options['student_id'])
                result = calculate_and_update_student_credits(student)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"成功更新学生 {student.name} ({student.student_id_num}): "
                        f"主修 {result['major_credits']} 学分, "
                        f"辅修 {result['minor_credits']} 学分, "
                        f"总计 {result['total_credits']} 学分"
                    )
                )
            except Student.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'学号为 {options["student_id"]} 的学生不存在')
                )
        else:
            # 更新所有学生
            students = Student.objects.all()
            updated_count = 0
            
            self.stdout.write(f'开始为 {students.count()} 名学生更新学分...')
            
            for student in students:
                try:
                    result = calculate_and_update_student_credits(student)
                    updated_count += 1
                    self.stdout.write(
                        f"✓ {student.name} ({student.student_id_num}): "
                        f"主修 {result['major_credits']} 学分, "
                        f"辅修 {result['minor_credits']} 学分"
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"✗ 更新学生 {student.name} 时出错: {str(e)}")
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'成功更新了 {updated_count} 名学生的学分统计')
            )