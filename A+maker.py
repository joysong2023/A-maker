import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from datetime import datetime, timedelta
import openai
from google.oauth2 import service_account
from googleapiclient.discovery import build
import webbrowser


class ScheduleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("A+ 제조기")

        self.tasks = []
        self.daily_hours = {}
        self.max_hours_per_task = 0  
        self.current_task = {}
        self.show_welcome()

    def show_welcome(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="A+ 제조기에 오신 것을 환영합니다!").pack(pady=20)
        tk.Label(self.root, text="새로운 학습 스케줄을 생성하시겠습니까?").pack(pady=10)
        tk.Button(self.root, text="예", command=self.show_task_type).pack(side="left", padx=20)
        tk.Button(self.root, text="아니오", command=self.quit_app).pack(side="right", padx=20)

    def quit_app(self):
        self.root.quit()

    def show_task_type(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="작업 유형을 선택하세요 (과제/시험)").pack(pady=20)

        self.task_type = ttk.Combobox(self.root, values=["과제", "시험"], state="readonly")
        self.task_type.pack()

        def save_task_type():
            if self.task_type.get():
                self.current_task['type'] = self.task_type.get()
                self.show_task_details()
            else:
                messagebox.showerror("오류", "작업 유형을 선택하세요.")

        tk.Button(self.root, text="다음", command=save_task_type).pack(pady=20)

    def show_task_details(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="작업 이름을 입력하세요 (예: 팀 프로젝트 발표)").pack(pady=10)
        self.task_name = tk.Entry(self.root)
        self.task_name.pack()
        if 'name' in self.current_task:
            self.task_name.insert(0, self.current_task['name'])

        tk.Label(self.root, text="과목 이름을 입력하세요 (예: 지능형 콘텐츠 제작)").pack(pady=10)
        self.subject_name = tk.Entry(self.root)
        self.subject_name.pack()
        if 'subject' in self.current_task:
            self.subject_name.insert(0, self.current_task['subject'])

        def save_task_details():
            name = self.task_name.get().strip()
            subject = self.subject_name.get().strip()
            if not name or not subject:
                messagebox.showerror("오류", "작업 이름과 과목 이름을 입력하세요.")
                return

            self.current_task['name'] = name
            self.current_task['subject'] = subject
            self.show_task_difficulty()

        tk.Button(self.root, text="다음", command=save_task_details).pack(pady=20)
        tk.Button(self.root, text="이전", command=self.show_task_type).pack(side="left", padx=10)

    def show_task_difficulty(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="난이도를 입력하세요 (1~10)").pack(pady=10)
        self.difficulty = ttk.Combobox(self.root, values=list(range(1, 11)), state="readonly")
        self.difficulty.pack()

        tk.Label(self.root, text="예상 시간을 입력하세요 (단위: 시간)").pack(pady=10)
        self.estimated_hours = tk.Entry(self.root)
        self.estimated_hours.pack()

        def save_task_difficulty():
            difficulty = self.difficulty.get()
            estimated_hours = self.estimated_hours.get().strip()

            if not difficulty or not estimated_hours or not estimated_hours.isdigit():
                messagebox.showerror("오류", "난이도와 예상 시간을 올바르게 입력하세요.")
                return

            self.current_task['difficulty'] = difficulty
            self.current_task['estimated_hours'] = estimated_hours
            self.show_additional_inputs()

        tk.Button(self.root, text="다음", command=save_task_difficulty).pack(pady=20)
        tk.Button(self.root, text="이전", command=self.show_task_details).pack(side="left", padx=10)

    def show_additional_inputs(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        if self.current_task['type'] == "과제":
            tk.Label(self.root, text="과제 유형을 선택하세요").pack(pady=10)
            self.assignment_type = ttk.Combobox(self.root, values=["팀플", "논문 작성", "퀴즈 준비", "발표 준비", "기타"], state="readonly")
            self.assignment_type.pack()

            def save_assignment_type():
                assignment_type = self.assignment_type.get()
                if not assignment_type:
                    messagebox.showerror("오류", "과제 유형을 선택하세요.")
                    return

                self.current_task['assignment_type'] = assignment_type
                self.show_calendar()

            tk.Button(self.root, text="다음", command=save_assignment_type).pack(pady=20)

        elif self.current_task['type'] == "시험":
            tk.Label(self.root, text="복습 전략을 선택하세요").pack(pady=10)
            self.review_strategy = ttk.Combobox(self.root, values=["망각곡선 기반 분할", "균형 분할"], state="readonly")
            self.review_strategy.pack()

            # 복습 간격 입력 관련 위젯
            self.review_interval_label = tk.Label(self.root, text="복습 간격을 입력하세요 (일 단위)")
            self.review_interval = tk.Entry(self.root)

            def on_strategy_change(event):
                """
                복습 전략 변경 시 동적으로 복습 간격 입력창을 표시/숨김.
                """
                if self.review_strategy.get() == "균형 분할":
                    self.review_interval_label.pack(pady=5)  # 복습 간격 텍스트 표시
                    self.review_interval.pack(pady=5)       # 복습 간격 입력창 표시
                else:
                    self.review_interval_label.pack_forget()  # 복습 간격 텍스트 숨김
                    self.review_interval.pack_forget()        # 복습 간격 입력창 숨김

            # 복습 전략 선택 변경 이벤트 바인딩
            self.review_strategy.bind("<<ComboboxSelected>>", on_strategy_change)

            def save_review_strategy():
                strategy = self.review_strategy.get()

                if not strategy:
                    messagebox.showerror("오류", "복습 전략을 선택하세요.")
                    return

                # 균형 분할일 경우에만 복습 간격을 확인
                if strategy == "균형 분할":
                    interval = self.review_interval.get().strip()
                    if not interval or not interval.isdigit() or int(interval) <= 0:
                        messagebox.showerror("오류", "복습 간격을 올바르게 입력하세요. 양의 정수를 입력해야 합니다.")
                        return
                    self.current_task['review_interval'] = int(interval)
                else:
                    self.current_task['review_interval'] = None  # 망각곡선 기반에서는 필요 없음

                self.current_task['review_strategy'] = "adaptive" if strategy == "망각곡선 기반 분할" else "steady"
                self.show_calendar()

            tk.Button(self.root, text="다음", command=save_review_strategy).pack(pady=20)
            tk.Button(self.root, text="이전", command=self.show_task_difficulty).pack(side="left", padx=10)


    def show_calendar(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="마감일을 선택하세요").pack(pady=10)
        self.calendar = Calendar(self.root, selectmode="day", date_pattern="yyyy-mm-dd")
        self.calendar.pack(pady=20)

        tk.Button(self.root, text="작업 추가", command=self.add_task).pack(pady=10)
        tk.Button(self.root, text="이전", command=self.show_additional_inputs).pack(side="left", padx=10)

    def add_task(self):
        try:
            self.current_task['deadline'] = self.calendar.get_date()

            required_keys = ['name', 'subject', 'difficulty', 'estimated_hours', 'type']
            for key in required_keys:
                if key not in self.current_task or not self.current_task[key]:
                    messagebox.showerror("오류", f"{key} 값을 입력하세요.")
                    return

            if self.current_task['type'] == "과제" and not self.current_task.get('assignment_type'):
                messagebox.showerror("오류", "과제 유형을 입력하세요.")
                return
            if self.current_task['type'] == "시험" and not self.current_task.get('review_strategy'):
                messagebox.showerror("오류", "복습 전략을 입력하세요.")
                return

            self.tasks.append(self.current_task.copy())
            self.current_task = {}
            self.show_add_more()

        except Exception as e:
            messagebox.showerror("오류", f"작업 추가 중 오류: {e}")

    def show_add_more(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="작업이 성공적으로 추가되었습니다!").pack(pady=20)
        tk.Button(self.root, text="새 작업 추가", command=self.show_task_type).pack(pady=10)
        tk.Button(self.root, text="작업 입력 완료", command=self.show_daily_hours).pack(pady=10)

    def show_daily_hours(self):
        """
        요일별 가용 시간을 입력받는 창.
        """
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="요일별 가용 시간을 입력하세요 (단위: 시간)").pack(pady=10)
        self.daily_entries = {}
        days = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]

        for day in days:
            tk.Label(self.root, text=day).pack()
            self.daily_entries[day] = tk.Entry(self.root)
            self.daily_entries[day].pack()

        tk.Button(self.root, text="다음", command=self.show_max_hours_per_task).pack(pady=20)

        

    def show_max_hours_per_task(self):
        """
        한 작업당 가용 시간을 입력받는 창.
        """
        # 요일별 가용 시간을 저장합니다.
        self.save_daily_entries()

        # 이전 위젯 제거
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="날마다 한 작업에 사용할 수 있는 가용 시간을 입력하세요 (단위: 시간)").pack(pady=10)
        self.max_hours_entry = tk.Entry(self.root)
        self.max_hours_entry.pack()

        # 디버깅: 저장된 daily_entries 값 확인
        print("Daily Hours 저장 상태:", self.daily_hours)

        tk.Button(self.root, text="스케줄 제출", command=self.submit_schedule).pack(pady=20)

    def save_daily_entries(self):
        """
        현재 입력된 요일별 가용 시간을 저장합니다.
        """
        for day, entry in self.daily_entries.items():
            if entry.winfo_exists():
                value = entry.get().strip()
                if value and value.replace('.', '', 1).isdigit():
                    self.daily_hours[day] = float(value)
                else:
                    self.daily_hours[day] = 0

    def submit_schedule(self):
        """
        사용자 입력 데이터로 스케줄 생성 시작.
        """
        try:
            # 저장된 요일별 가용 시간 확인
            if not self.daily_hours:
                raise RuntimeError("요일별 가용 시간이 저장되지 않았습니다.")

            # 한 작업당 가용시간 저장
            max_hours_input = self.max_hours_entry.get().strip()
            if not max_hours_input or not max_hours_input.replace('.', '', 1).isdigit():
                raise ValueError("한 작업당 가용 시간을 올바르게 입력하세요.")
            self.max_hours_per_task = float(max_hours_input)
            if self.max_hours_per_task <= 0:
                raise ValueError("한 작업당 가용 시간은 양수여야 합니다.")

            # 스케줄 생성
            self.generate_schedule()
        except ValueError as e:
            messagebox.showerror("오류", f"입력값 오류: {e}")
        except RuntimeError as e:
            messagebox.showerror("오류", f"데이터 오류: {e}")
        except Exception as e:
            messagebox.showerror("오류", f"스케줄 제출 중 오류: {e}")


    def generate_schedule(self):
        """
        사용자 입력 데이터를 기반으로 스케줄을 생성.
        """
        try:
            tasks = self.tasks
            daily_available_hours = self.daily_hours.copy()

            # 요일 영어->한글 매핑
            day_mapping = {
                "Monday": "월요일",
                "Tuesday": "화요일",
                "Wednesday": "수요일",
                "Thursday": "목요일",
                "Friday": "금요일",
                "Saturday": "토요일",
                "Sunday": "일요일",
            }

            # 스케줄 계산 로직
            schedule = {}
            tasks.sort(key=lambda x: (datetime.strptime(x["deadline"], "%Y-%m-%d"), -int(x["difficulty"])))

            current_day = datetime.now().date()
            end_day = max(datetime.strptime(task["deadline"], "%Y-%m-%d").date() for task in tasks)

            remaining_tasks = {task["name"]: float(task["estimated_hours"]) for task in tasks}
            completed_exams = set()

            while any(remaining_tasks.values()) and current_day <= end_day:
                day_name = day_mapping.get(current_day.strftime("%A"), None)
                if not day_name:
                    raise ValueError(f"{current_day.strftime('%A')}는 지원되지 않는 요일입니다.")

                if day_name in daily_available_hours and daily_available_hours[day_name] > 0:
                    for task in tasks:
                        task_name = task["name"]
                        if remaining_tasks[task_name] > 0:
                            # 작업 시간 계산
                            allocatable_hours = min(
                                remaining_tasks[task_name],
                                daily_available_hours[day_name],
                                self.max_hours_per_task  # 한 작업당 가용시간
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

                            # 복습 일정 생성
                            if (
                                task["type"] == "시험"
                                and remaining_tasks[task_name] <= 0
                                and task_name not in completed_exams
                            ):
                                complete_date = current_day
                                exam_date = datetime.strptime(task["deadline"], "%Y-%m-%d").date()
                                review_strategy = task.get("review_strategy", "steady")
                                review_interval = task.get("review_interval", 2)
                                review_dates = self.calculate_review_schedule(
                                    complete_date, exam_date, strategy=review_strategy, interval=review_interval
                                )
                                schedule = self.integrate_review_schedule(schedule, review_dates, task_name, task["subject"])
                                completed_exams.add(task_name)

                current_day += timedelta(days=1)

            self.schedule = schedule  # 클래스 속성으로 저장
            self.show_schedule(schedule)

        except Exception as e:
            messagebox.showerror("오류", f"스케줄 생성 중 오류: {e}")
            raise  # 디버깅을 위해 원본 예외 다시 발생

    def calculate_review_schedule(self, complete_date, exam_date, strategy="steady", interval=2):

        review_schedule = []
        remaining_days = (exam_date - complete_date).days

        if strategy == "adaptive":  # 망각곡선 기반 전략
            if remaining_days > 30:
                gaps = [1, 3, 7, 14, 21]
            elif 14 < remaining_days <= 30:
                gaps = [1, 3, 7, 10]
            else:
                gaps = [1, 3, 5] if remaining_days > 7 else [1]

            current_date = complete_date
            for gap in gaps:
                next_date = current_date + timedelta(days=gap)
                if next_date < exam_date:
                    review_schedule.append(next_date)
                    current_date = next_date

        elif strategy == "steady":  # 일정 간격 기반 전략
            next_date = complete_date + timedelta(days=interval)
            while next_date < exam_date:
                review_schedule.append(next_date)
                next_date += timedelta(days=interval)

        # 시험 전날 복습 일정 추가
        if exam_date - timedelta(days=1) not in review_schedule:
            review_schedule.append(exam_date - timedelta(days=1))

        return sorted(set(review_schedule))



    def integrate_review_schedule(self, schedule, review_dates, task_name, subject):
        """
        복습 일정을 기존 스케줄에 통합.
        """
        for review_date in review_dates:
            if review_date not in schedule:
                schedule[review_date] = []
            schedule[review_date].append({"task": f"복습: {task_name} ({subject})", "hours": 1.0})
        return schedule

    def show_schedule(self, schedule):
        """
        스케줄을 tkinter 창에 표시.
        """
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="계획된 스케줄").pack(pady=10)

        schedule_frame = tk.Frame(self.root)
        schedule_frame.pack()

        for date, tasks in sorted(schedule.items()):
            tk.Label(schedule_frame, text=f"{date.strftime('%Y-%m-%d')}:").pack(anchor="w")
            for task in tasks:
                tk.Label(schedule_frame, text=f"  - {task['task']} ({task['hours']}시간)").pack(anchor="w")

        tk.Button(self.root, text="종료", command=self.quit_app).pack(pady=20)


    def show_schedule(self, schedule):
        """
        스케줄을 tkinter 창에 표시하며 스크롤바를 추가.
        """
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="계획된 스케줄").pack(pady=10)

        # 스크롤바가 포함된 Canvas 생성
        frame_container = tk.Frame(self.root)
        frame_container.pack(fill="both", expand=True)

        canvas = tk.Canvas(frame_container)
        scrollbar = tk.Scrollbar(frame_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 스크롤바와 캔버스 배치
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 스케줄 데이터 출력
        for date, tasks in sorted(schedule.items()):
            tk.Label(scrollable_frame, text=f"{date.strftime('%Y-%m-%d')}").pack(anchor="w")
            for task in tasks:
                tk.Label(scrollable_frame, text=f"  - {task['task']} ({task['hours']}시간)").pack(anchor="w")

        # 버튼 배치
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="Google Calendar 업데이트", command=self.update_google_calendar).pack(side="left", padx=10)
        tk.Button(button_frame, text="과제 팁 보기", command=self.show_task_tips).pack(side="right", padx=10)


    def update_google_calendar(self):
        try:
            credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
            service = build('calendar', 'v3', credentials=credentials)

            for date, tasks in self.schedule.items():
                task_list = '\n'.join([f"- {task['task']} ({task['hours']}시간)" for task in tasks])
                event = {
                    'summary': f"{date.strftime('%Y-%m-%d')}의 하루 일정",
                    'description': task_list,
                    'start': {'date': date.strftime('%Y-%m-%d'), 'timeZone': 'Asia/Seoul'},
                    'end': {'date': (date + timedelta(days=1)).strftime('%Y-%m-%d'), 'timeZone': 'Asia/Seoul'}
                }
                service.events().insert(calendarId=CALENDAR_ID, body=event).execute()

            messagebox.showinfo("완료", "Google Calendar에 일정이 성공적으로 업데이트되었습니다.")

            # 구글 캘린더 웹사이트 열기
            webbrowser.open("https://calendar.google.com/")
        except Exception as e:
            messagebox.showerror("오류", f"Google Calendar 업데이트 중 오류 발생: {e}")

    def show_task_tips(self):
        """
        과제 및 시험 팁을 보여주는 창.
        """
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="과제 및 시험 팁", font=("Arial", 16)).pack(pady=10)

        tips_frame = tk.Frame(self.root)
        tips_frame.pack(padx=20, pady=10, fill="both", expand=True)

        # 각 과제 및 시험별 팁 표시
        for task in self.tasks:
            tk.Label(tips_frame, text=f"{task['name']} ({task['subject']})", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
            tips = self.generate_task_tips(task)
            for tip in tips:
                # 긴 글자를 wraplength로 줄바꿈
                tk.Label(tips_frame, text=f"- {tip}", wraplength=500, justify="left").pack(anchor="w", padx=10)

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="돌아가기", command=lambda: self.show_schedule(self.schedule)).pack(padx=10, side="left")

    def generate_task_tips(self, task):
        """
        OpenAI API를 사용하여 과제 팁 3가지를 간결하게 생성.
        """
        try:
            prompt = f"""
            {task['type']} 과제 "{task['name']}"를 성공적으로 수행하기 위한 간단하고 간결한 팁 3가지를 작성해 주세요.
            각각의 팁은 한 문장으로 제한해 주세요.
            """
            # OpenAI API 호출
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            tips = response['choices'][0]['message']['content']

            # 응답 텍스트를 줄 단위로 나눔
            tips_list = [tip.lstrip("-1234567890. ").strip() for tip in tips.split("\n") if tip.strip()]

            # 최대 3개만 반환
            return tips_list[:3]
        except Exception as e:
            return [f"팁 생성 중 오류: {e}"]


if __name__ == "__main__":
    root = tk.Tk()
    app = ScheduleApp(root)
    root.mainloop()
