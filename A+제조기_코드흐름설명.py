import datetime

def welcome_message():
    """
    시스템에 처음 접속할 때 환영 메시지를 출력합니다.
    """
    print("학습 스케줄 관리 시스템에 오신 것을 환영합니다!")

def main_menu():
    """
    사용자로부터 스케줄 생성을 시작할지 여부를 입력받습니다.
    """
    while True:
        user_input = input("새로운 학습 스케줄을 생성하시겠습니까? (y/n): ").strip().lower()
        if user_input == 'y':
            start_schedule_creation()  # 스케줄 생성 프로세스 시작
        elif user_input == 'n':
            print("학습을 미루고 계신가요? 지금 시작하면 학습 효율을 극대화할 수 있습니다!")
        else:
            print("잘못된 입력입니다. 'y' 또는 'n'을 입력하세요.")

def start_schedule_creation():
    """
    사용자 입력을 받아 작업 리스트를 생성하고 스케줄을 배치합니다.
    """
    tasks = []
    while True:
        print("\n새로운 작업을 추가합니다.")
        task_type = input("작업 유형을 선택하세요 (과제/시험/exit): ").strip().lower()
        if task_type == "exit":
            break
        elif task_type not in ["과제", "시험"]:
            print("잘못된 작업 유형입니다. 다시 입력하세요.")
            continue

        task = {}
        task["type"] = task_type
        task["name"] = input("작업 이름을 입력하세요 (예: 팀 프로젝트 발표): ").strip()
        task["subject"] = input("과목 이름을 입력하세요 (예: 경영학개론): ").strip()
        task["deadline"] = input("마감일을 입력하세요 (YYYY-MM-DD): ").strip()
        task["difficulty"] = int(input("난이도를 입력하세요 (1: 매우 쉬움 ~ 10: 매우 어려움): ").strip())

        if task_type == "과제":
            # 과제의 세부 유형 선택
            print("과제 유형을 선택하세요:")
            print("1: 팀플\n2: 논문 작성\n3: 퀴즈 준비\n4: 발표 준비\n5: 기타")
            task["subtype"] = int(input("선택: ").strip())
        elif task_type == "시험":
            # 시험 복습 전략 선택
            print("복습 전략을 선택하세요:")
            print("1: 적당히 나누기\n2: 꾸준히")
            strategy = int(input("선택: ").strip())
            if strategy == 1:
                task["review_strategy"] = "adaptive"
            else:
                task["review_strategy"] = "steady"
                task["review_interval"] = int(input("복습 간격을 입력하세요 (단위: 일, 기본값: 2일): ").strip())

        task["estimated_hours"] = float(input("예상 시간을 입력하세요 (단위: 시간): ").strip())
        tasks.append(task)

    # 각 요일의 가용 시간 입력
    daily_available_hours = {}
    print("\n각 요일의 과제 수행 가능 시간을 입력하세요(단위: 시간):")
    for day in ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]:
        daily_available_hours[day] = float(input(f"{day}: ").strip())

    # 작업당 최대 가용 시간 입력
    print("\n날마다 한 작업에 사용할 수 있는 가용 시간을 입력하세요 (단위: 시간):")
    max_hours_per_task = float(input("시간 단위: ").strip())

    # 스케줄 생성
    schedule = generate_schedule(tasks, daily_available_hours, max_hours_per_task)
    print_schedule(schedule)

def generate_schedule(tasks, daily_available_hours, max_hours_per_task):
    """
    작업 리스트를 받아 스케줄을 생성합니다.
    
    :param tasks: 작업 리스트
    :param daily_available_hours: 각 요일별 가용 시간
    :param max_hours_per_task: 작업당 최대 가용 시간
    :return: 생성된 스케줄 딕셔너리
    """
    schedule = {}
    # 작업 정렬: 마감일 우선, 난이도 높은 순서
    tasks.sort(key=lambda x: (datetime.datetime.strptime(x["deadline"], "%Y-%m-%d"), -x["difficulty"]))

    current_day = datetime.date.today()
    end_day = max(datetime.datetime.strptime(task["deadline"], "%Y-%m-%d").date() for task in tasks)

    # 영어 요일을 한글 요일로 매핑
    day_mapping = {
        "Monday": "월요일",
        "Tuesday": "화요일",
        "Wednesday": "수요일",
        "Thursday": "목요일",
        "Friday": "금요일",
        "Saturday": "토요일",
        "Sunday": "일요일",
    }

    # 각 작업의 남은 작업 시간 추적
    remaining_tasks = {task["name"]: task["estimated_hours"] for task in tasks}
    completed_exams = set()  # 복습 일정 생성된 시험 추적

    while any(remaining_tasks.values()) and current_day <= end_day:
        day_name = day_mapping[current_day.strftime("%A")]
        if day_name in daily_available_hours and daily_available_hours[day_name] > 0:
            for task in tasks:
                task_name = task["name"]
                if remaining_tasks[task_name] > 0:
                    allocatable_hours = min(
                        remaining_tasks[task_name], daily_available_hours[day_name], max_hours_per_task
                    )
                    if allocatable_hours > 0:
                        if current_day not in schedule:
                            schedule[current_day] = []
                        schedule[current_day].append({
                            "task": f"{task_name} ({task['subject']})",
                            "hours": allocatable_hours,
                        })
                        daily_available_hours[day_name] -= allocatable_hours
                        remaining_tasks[task_name] -= allocatable_hours

                    # 시험의 복습 일정 생성
                    if task["type"] == "시험" and remaining_tasks[task_name] <= 0 and task_name not in completed_exams:
                        complete_date = current_day
                        exam_date = datetime.datetime.strptime(task["deadline"], "%Y-%m-%d").date()
                        strategy = 1 if task.get("review_strategy") == "adaptive" else 2
                        interval = task.get("review_interval", 2)
                        review_dates = calculate_review_schedule(complete_date, exam_date, strategy, interval)
                        schedule = integrate_review_schedule(schedule, review_dates, task_name, task["subject"])
                        completed_exams.add(task_name)

        current_day += datetime.timedelta(days=1)

    return schedule

def calculate_review_schedule(complete_date, exam_date, strategy=1, interval=2):
    """
    복습 일정을 생성합니다.
    
    :param complete_date: 시험 준비 완료 날짜
    :param exam_date: 시험 날짜
    :param strategy: 복습 전략
    :param interval: 일정 간격 (기본값: 2일)
    :return: 복습 일정 리스트
    """
    review_schedule = []
    remaining_days = (exam_date - complete_date).days

    if strategy == 1:  # 망각곡선 기반
        gaps = [1, 3, 7, 14, 21] if remaining_days > 30 else ([1, 3, 7, 10] if remaining_days > 14 else [1, 3, 5])
        current_date = complete_date
        for gap in gaps:
            next_date = current_date + datetime.timedelta(days=gap)
            if next_date < exam_date:
                review_schedule.append(next_date)
                current_date = next_date
            else:
                break
    elif strategy == 2:  # 일정 간격 기반
        current_date = complete_date + datetime.timedelta(days=interval)
        while current_date < exam_date:
            review_schedule.append(current_date)
            current_date += datetime.timedelta(days=interval)

    review_schedule.append(exam_date - datetime.timedelta(days=1))  # 시험 전날 복습
    return sorted(set(review_schedule))

def integrate_review_schedule(schedule, review_dates, task_name, subject):
    """
    복습 일정을 기존 스케줄에 통합합니다.
    """
    for review_date in review_dates:
        if review_date not in schedule:
            schedule[review_date] = []
        schedule[review_date].append({
            "task": f"복습: {task_name} ({subject})",
            "hours": 1.0,
        })
    return schedule

def print_schedule(schedule):
    """
    스케줄을 출력합니다.
    """
    print("\n스케줄 생성 결과:")
    for day, tasks in sorted(schedule.items()):
        print(day.strftime("%Y-%m-%d:"))
        for task_entry in tasks:
            print(f"  - {task_entry['task']} ({task_entry['hours']}시간)")

if __name__ == "__main__":
    welcome_message()
    main_menu()
