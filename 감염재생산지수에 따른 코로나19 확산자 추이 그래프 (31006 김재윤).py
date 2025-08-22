# 설치가 필요한 경우 (최초 1회만 실행)
# !pip install ipywidgets

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'  # 맑은 고딕
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

class InfectionAnimationGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("코로나19 감염재생산지수 시뮬레이션")
        self.root.geometry("1400x900")
        
        # 애니메이션 객체
        self.anim = None
        self.is_animating = False
        
        self.setup_gui()
        
    def setup_gui(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 제목
        title_label = ttk.Label(main_frame, text="코로나19 감염재생산지수 시뮬레이션", 
                               font=("맑은 고딕", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 입력 프레임
        input_frame = ttk.LabelFrame(main_frame, text="시뮬레이션 설정", padding="10")
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 감염재생산지수 입력
        ttk.Label(input_frame, text="감염재생산지수 R:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.r_var = tk.DoubleVar(value=0.8)
        r_entry = ttk.Entry(input_frame, textvariable=self.r_var, width=10)
        r_entry.grid(row=0, column=1, padx=(10, 0), pady=5)
        ttk.Label(input_frame, text="(0.1 ~ 3.0)").grid(row=0, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        # 모집단 크기 입력
        ttk.Label(input_frame, text="모집단 크기:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.population_var = tk.IntVar(value=50000000)  # 한국 인구수
        population_entry = ttk.Entry(input_frame, textvariable=self.population_var, width=15)
        population_entry.grid(row=1, column=1, padx=(10, 0), pady=5)
        ttk.Label(input_frame, text="명").grid(row=1, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        # 초기 감염자 수 입력
        ttk.Label(input_frame, text="초기 감염자 수:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.initial_var = tk.IntVar(value=1000)
        initial_entry = ttk.Entry(input_frame, textvariable=self.initial_var, width=10)
        initial_entry.grid(row=2, column=1, padx=(10, 0), pady=5)
        ttk.Label(input_frame, text="명").grid(row=2, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        # 시나리오 선택
        ttk.Label(input_frame, text="시나리오:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.scenario_var = tk.StringVar(value="대한민국 확산 추이")
        scenario_combo = ttk.Combobox(input_frame, textvariable=self.scenario_var, 
                                     values=["대한민국 확산 추이", "확산 움직임", "극단적 확산", "완전 통제"], 
                                     state="readonly", width=15)
        scenario_combo.grid(row=3, column=1, padx=(10, 0), pady=5)
        scenario_combo.bind('<<ComboboxSelected>>', self.on_scenario_change)
        
        # 버튼들
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        self.start_button = ttk.Button(button_frame, text="애니메이션 시작", 
                                      command=self.start_animation, style="Accent.TButton")
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="정지", 
                                     command=self.stop_animation, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.reset_button = ttk.Button(button_frame, text="초기화", 
                                      command=self.reset_animation)
        self.reset_button.pack(side=tk.LEFT)
        
        # 설명 텍스트
        info_text = """
R값 해석:
• R < 1: 감염 감소 (좋음)
• R = 1: 안정적 유지
• R > 1: 감염 확산 (나쁨)

한국 코로나19 R값:
• 일반적: 0.7~0.9
• 확산기: 1.2~1.5
• 극단적: 2.0 이상
        """
        info_label = ttk.Label(input_frame, text=info_text, justify=tk.LEFT)
        info_label.grid(row=5, column=0, columnspan=3, pady=20, sticky=tk.W)
        
        # 그래프 프레임
        graph_frame = ttk.LabelFrame(main_frame, text="감염자 추이 그래프", padding="10")
        graph_frame.grid(row=1, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # matplotlib 그래프
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(10, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 통계 프레임
        stats_frame = ttk.LabelFrame(main_frame, text="실시간 통계", padding="10")
        stats_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.stats_text = tk.Text(stats_frame, width=40, height=15, font=("맑은 고딕", 10))
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        # 초기 그래프 설정
        self.setup_initial_graph()
        
        # 로그 스케일 체크박스 추가
        self.log_var = tk.BooleanVar(value=False)
        log_check = ttk.Checkbutton(input_frame, text="로그 스케일(y축)", variable=self.log_var, command=self.reset_animation)
        log_check.grid(row=6, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # 시뮬레이션 기간 입력
        ttk.Label(input_frame, text="시뮬레이션 기간(일):").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.days_var = tk.IntVar(value=365)
        days_entry = ttk.Entry(input_frame, textvariable=self.days_var, width=10)
        days_entry.grid(row=7, column=1, padx=(10, 0), pady=5)
        ttk.Label(input_frame, text="일").grid(row=7, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        # 감염률 확대 체크박스 추가
        self.enhance_rate_var = tk.BooleanVar(value=False)
        enhance_rate_check = ttk.Checkbutton(input_frame, text="감염률 확대(0~5%)", variable=self.enhance_rate_var, command=self.reset_animation)
        enhance_rate_check.grid(row=8, column=0, columnspan=3, sticky=tk.W, pady=5)
        # 전체 기간 보기 체크박스 제거
        
    def setup_initial_graph(self):
        self.ax1.clear()
        self.ax2.clear()
        
        self.ax1.set_title("감염자 수 변화", fontsize=12, fontweight='bold')
        self.ax1.set_xlabel("시간 (일)")
        self.ax1.set_ylabel("인원 수")
        self.ax1.grid(True, alpha=0.3)
        
        self.ax2.set_title("감염률 변화 (%)", fontsize=12, fontweight='bold')
        self.ax2.set_xlabel("시간 (일)")
        self.ax2.set_ylabel("감염률 (%)")
        self.ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        self.canvas.draw()
        
    def on_scenario_change(self, event=None):
        scenario = self.scenario_var.get()
        if scenario == "대한민국 확산 추이":
            self.r_var.set(0.8)
            self.population_var.set(50000000)
            self.initial_var.set(1000)
        elif scenario == "확산 움직임":
            self.r_var.set(1.3)
            self.population_var.set(50000000)
            self.initial_var.set(5000)
        elif scenario == "극단적 확산":
            self.r_var.set(2.0)
            self.population_var.set(50000000)
            self.initial_var.set(10000)
        elif scenario == "완전 통제":
            self.r_var.set(0.5)
            self.population_var.set(50000000)
            self.initial_var.set(500)
            
    def calculate_SIR(self, R, population, initial_infected, days=365, gamma=0.1):
        S = [population - initial_infected]
        I = [initial_infected]
        R_list = [0]
        beta = R * gamma  # 감염률
        for t in range(1, days+1):
            new_infected = beta * S[-1] * I[-1] / population
            new_recovered = gamma * I[-1]
            S.append(S[-1] - new_infected)
            I.append(I[-1] + new_infected - new_recovered)
            R_list.append(R_list[-1] + new_recovered)
        # 누적 확진자: 감염자 + 회복자
        C = [i + r for i, r in zip(I, R_list)]
        return S, I, R_list, C

    def animate(self, frame):
        R = self.r_var.get()
        population = self.population_var.get()
        initial = self.initial_var.get()
        days = 365
        S, I, R_t, C = self.calculate_SIR(R, population, initial, days=days)
        self.t_data = np.arange(len(S))
        self.I_data = I
        self.current_data = I
        self.R_data = R_t
        self.C_data = C
        self.attack_rate_data = (np.array(self.C_data) / population) * 100
        self.window_size = 30  # y축 자동조정용
        # 그래프 초기화
        self.ax1.clear()
        self.ax2.clear()
        # y축 최대값 자동 조정 (최근 window_size 구간)
        y_start = max(0, frame - self.window_size + 1)
        y_max = max(
            max(self.I_data[y_start:frame+1]),
            max(self.R_data[y_start:frame+1]),
            max(self.C_data[y_start:frame+1]),
            100
        )
        if self.log_var.get():
            self.ax1.set_yscale('log')
            y_min = 1 if population > 1 else 0.1
            self.ax1.set_ylim(y_min, population)
        else:
            self.ax1.set_yscale('linear')
            self.ax1.set_ylim(0, population)
        # x축: 0~365로 고정
        self.ax1.set_xlim(0, 365)
        self.ax2.set_xlim(0, 365)
        self.ax1.set_xticks(np.arange(0, 366, step=30))
        self.ax2.set_xticks(np.arange(0, 366, step=30))
        self.ax1.xaxis.set_major_locator(ticker.MaxNLocator(nbins=10, integer=True))
        self.ax2.xaxis.set_major_locator(ticker.MaxNLocator(nbins=10, integer=True))
        self.ax1.yaxis.set_major_locator(ticker.MaxNLocator(nbins=8, integer=True))
        self.ax2.yaxis.set_major_locator(ticker.MaxNLocator(nbins=8))
        self.ax1.tick_params(axis='x', rotation=0)
        self.ax2.tick_params(axis='x', rotation=0)
        self.ax1.tick_params(axis='y', rotation=0)
        self.ax2.tick_params(axis='y', rotation=0)
        self.ax1.set_title(f"감염재생산지수 R={R:.2f}, 모집단 {population:,}명", fontsize=12, fontweight='bold')
        self.ax1.set_xlabel("시간 (일)")
        self.ax1.set_ylabel("인원 수")
        self.ax1.grid(True, alpha=0.3, which='both')
        # 감염률 y축 범위 결정
        self.ax2.set_ylim(0, 100)
        self.ax2.set_title("누적 감염률(%)", fontsize=12, fontweight='bold')
        self.ax2.set_xlabel("시간 (일)")
        self.ax2.set_ylabel("누적 감염률 (%)")
        self.ax2.grid(True, alpha=0.3)
        self.ax1.axhline(y=population, color='gray', linestyle='--', alpha=0.7, label=f'모집단 크기 ({population:,}명)')
        # 선: 0~현재 프레임까지 누적해서 그림
        self.line1, = self.ax1.plot(self.t_data[:frame+1], self.I_data[:frame+1], 'r-', linewidth=2, label='현재 감염자 수')
        self.line2, = self.ax1.plot(self.t_data[:frame+1], self.R_data[:frame+1], 'g-', linewidth=2, label='회복자 수')
        self.line3, = self.ax1.plot(self.t_data[:frame+1], self.C_data[:frame+1], 'b-', linewidth=2, label='누적 확진자 수')
        self.line4, = self.ax2.plot(self.t_data[:frame+1], self.attack_rate_data[:frame+1], 'purple', linewidth=2, label='누적 감염률')
        self.ax1.legend(fontsize=9)
        self.ax2.legend(fontsize=9)
        plt.tight_layout()
        if frame > 0:
            self.update_statistics(frame)
        return self.line1, self.line2, self.line3, self.line4

    def update_statistics(self, idx):
        R = self.r_var.get()
        population = self.population_var.get()
        initial = self.initial_var.get()
        current_infected = self.I_data[idx]
        recovered = self.R_data[idx]
        cumulative = self.C_data[idx]
        attack_rate = self.attack_rate_data[idx]
        stats_text = f"""=== 실시간 통계 (Day {idx}) ===
감염재생산지수 (R): {R:.2f}
모집단 크기: {population:,}명
초기 감염자 수: {initial:,}명

현재 감염자 수: {current_infected:,.0f}명
회복자 수: {recovered:,.0f}명
누적 확진자 수: {cumulative:,.0f}명
누적 감염률: {attack_rate:.2f}%

예상 최대 감염자 수: {np.max(self.I_data):,.0f}명
예상 최대 누적 확진자 수: {np.max(self.C_data):,.0f}명
예상 최대 누적 감염률: {np.max(self.attack_rate_data):.2f}%

상태: {'⚠️ 확산 중' if R > 1 else '✅ 감소 중' if R < 1 else '⚖️ 안정적'}
        """
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)
    
    def start_animation(self):
        try:
            if self.is_animating:
                self.stop_animation()
            self.is_animating = True
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.frame = 0
            def update(frame):
                if not self.is_animating:
                    return self.line1, self.line2, self.line3, self.line4
                self.frame = frame
                if frame > 365:
                    self.stop_animation()
                    return self.line1, self.line2, self.line3, self.line4
                return self.animate(frame)
            self.anim = FuncAnimation(self.fig, update, frames=366, interval=100, blit=True, repeat=False)
            self.canvas.draw()
        except Exception as e:
            messagebox.showerror("오류", f"애니메이션 시작 중 오류가 발생했습니다: {str(e)}")

    @property
    def infinite_frames(self):
        i = 0
        while True:
            yield i
            i += 1

    def stop_animation(self):
        self.is_animating = False
        if self.anim:
            self.anim.event_source.stop()
            self.anim = None  # 애니메이션 객체 완전 해제
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
    
    def reset_animation(self):
        self.stop_animation()
        # 시뮬레이션 변수 초기화
        self.current_day = 0
        self.infected = [self.initial_var.get()]
        # 그래프 초기화
        self.setup_initial_graph()
        self.stats_text.delete(1.0, tk.END)
        # 버튼 상태 초기화
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
    
    def run(self):
        self.root.mainloop()

# 실행
if __name__ == "__main__":
    app = InfectionAnimationGUI()
    app.run() 