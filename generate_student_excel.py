import pandas as pd
from faker import Faker
import random
import string

# --- 配置 ---
NUM_ROWS = 200  # 您想生成的学生记录数量
OUTPUT_FILE = 'students_final_from_image.xlsx' # 输出的Excel文件名

# 初始化 Faker 以生成中文数据
fake = Faker('zh_CN')

# --- 数据源 (严格按照您图片中的信息) ---
MAJORS_AND_DEPARTMENTS = [
    ("曾娘演化史", "历史学院"),
    ("电子猫娘养成", "大数据学院"),
    ("烈焰法术学院", "法学院"),
    ("国际贸易", "经济学院"),
    ("软件工程", "计算机科学与技术系"),
    ("鉴证学", "马克思主义学院")
]

# 宿舍楼栋列表
DORM_BUILDINGS = ["紫荆公寓", "文华公寓", "启航东楼", "启航西楼", "知行书院", "明德书院"]


# --- 初始化，用于确保唯一性 ---
used_student_ids = set()
used_id_cards = set()


# --- 开始生成数据 ---
all_students_data = []
print(f"正在严格按照最新要求生成 {NUM_ROWS} 条学生数据...")
print(f"--> 使用的专业/院系信息来源: 您提供的图片")


for i in range(NUM_ROWS):
    # --- 1. 生成唯一的学号和用户名 ---
    while True:
        year = random.randint(2023, 2025)
        student_id = f"{year}{random.randint(1000, 9999)}{str(i).zfill(4)}"
        if student_id not in used_student_ids:
            used_student_ids.add(student_id)
            break
    username = student_id

    # --- 2. 生成唯一身份证号 ---
    while True:
        id_card = fake.ssn()
        if id_card not in used_id_cards:
            used_id_cards.add(id_card)
            break

    # --- 3. 生成主修专业信息 (来自图片) ---
    major_name, major_department = random.choice(MAJORS_AND_DEPARTMENTS)

    # --- 4. 生成辅修专业信息 (同有同无, 且不与主修相同) ---
    minor_department = None
    minor_major = None
    if random.random() < 0.25:
        potential_minors = [pair for pair in MAJORS_AND_DEPARTMENTS if pair[0] != major_name]
        if potential_minors:
            minor_major, minor_department = random.choice(potential_minors)

    # --- 5. 生成其他字段 ---
    dormitory = f"{random.choice(DORM_BUILDINGS)}{random.randint(1, 20)}号楼-{random.randint(101, 618)}"

    # --- 6. 组装单条学生记录 ---
    student = {
        'username': username,
        'password': ''.join(random.choices(string.ascii_letters + string.digits, k=12)),
        'name': fake.name(),
        'student_id_num': student_id,
        'department_name': major_department,
        'major_name': major_name,
        'minor_department_name': minor_department,
        'minor_major_name': minor_major,
        'id_card': id_card if random.random() < 0.9 else None,
        'gender': random.choice(['男', '女']) if random.random() < 0.9 else None,
        'birth_date': fake.date_of_birth(minimum_age=17, maximum_age=24).strftime('%Y-%m-%d') if random.random() < 0.9 else None,
        'phone': fake.phone_number() if random.random() < 0.9 else None,
        'home_address': fake.address() if random.random() < 0.8 else None,
        'dormitory': dormitory if random.random() < 0.95 else None,
    }
    all_students_data.append(student)

# --- 创建DataFrame ---
df = pd.DataFrame(all_students_data)

# --- 按要求的顺序排列列 (使用简单英文名) ---
final_column_order = [
    'username',
    'password',
    'name',
    'student_id_num',
    'department_name',
    'major_name',
    'minor_department_name',
    'minor_major_name',
    'id_card',
    'gender',
    'birth_date',
    'phone',
    'home_address',
    'dormitory'
]
df = df[final_column_order]

# --- 导出到Excel文件 ---
try:
    df.to_excel(OUTPUT_FILE, index=False, engine='openpyxl')
    print("-" * 50)
    print(f"✅ 成功! {NUM_ROWS} 条测试数据已保存到 '{OUTPUT_FILE}' 文件中。")
    print("   - 专业/院系信息已严格按照您的图片生成。")
    print("   - 学号、用户名、身份证号已确保唯一。")
    print("   - 文件列名已使用简单的英文格式以便导入。")
    print("-" * 50)
except Exception as e:
    print(f"❌ 生成文件时出错: {e}")
    print("请确保已安装必要的库: pip install pandas openpyxl Faker")