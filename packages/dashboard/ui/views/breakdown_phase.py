"""Breakdown Phase 视图组件"""

import os
from string import Template

from loguru import logger
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..components import DirectorySelectorBuilder, FileSelectorBuilder, TrioRunnerBuilder, SoloRunnerBuilder


class BreakdownPhaseView(QWidget):
    """Breakdown Phase Tab 视图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.working_directory = os.path.expanduser("~")
        
        # 初始化各个选择器和运行器
        self.workspace_selector = None
        self.do_plan_selector = None
        self.do_phase_selector = None
        self.do_skills_selector = None
        self.do_output_selector = None
        self.check_scoring_selector = None
        self.act_accept_selector = None
        
        self.do_runner = None
        self.check_runner = None
        self.act_runner = None
        
        self.prepare_button = None
        self.start_button = None
        self.do_button = None
        self.check_button = None
        self.act_button = None
        
        self.pid_group = None
        self.pid_value_label = None
        self.timer_group = None
        self.timer_value_label = None
        
        # 设置布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addSpacing(48)
        
        self._setup_control_rows(layout)
        
        layout.addSpacing(20)
        layout.addStretch()

    def _setup_control_rows(self, main_layout: QVBoxLayout):
        """设置多横排控制区域"""
        # 第一行：选择目录按钮 + cwd 文本框 + 预备按钮 + 开始按钮
        self.workspace_selector = DirectorySelectorBuilder()
        row1_layout = self.workspace_selector.build(
            parent=self,
            on_select_callback=self._on_directory_selected,
            default_value=self.working_directory,
            button_text="选择工作目录",
        )

        # 预备按钮
        self.prepare_button = QPushButton("预备")
        self.prepare_button.clicked.connect(self._on_prepare_button_clicked)
        self.prepare_button.setFixedWidth(80)
        row1_layout.addWidget(self.prepare_button)

        # 开始按钮
        self.start_button = QPushButton("开始")
        self.start_button.clicked.connect(self._on_start_button_clicked)
        self.start_button.setFixedWidth(80)
        row1_layout.addWidget(self.start_button)

        # 框间距
        row1_layout.addSpacing(8)

        # PID 框（QGroupBox）
        self.pid_group = QGroupBox("PID")
        self.pid_group.setFixedWidth(80)
        self.pid_value_label = QLabel("--")
        self.pid_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pid_layout = QVBoxLayout(self.pid_group)
        pid_layout.setContentsMargins(6, 6, 6, 6)
        pid_layout.addWidget(self.pid_value_label)
        row1_layout.addWidget(self.pid_group)

        # 耗时框（QGroupBox）
        self.timer_group = QGroupBox("耗时")
        self.timer_group.setFixedWidth(90)
        self.timer_value_label = QLabel("--:--:--")
        self.timer_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_layout = QVBoxLayout(self.timer_group)
        timer_layout.setContentsMargins(6, 6, 6, 6)
        timer_layout.addWidget(self.timer_value_label)
        row1_layout.addWidget(self.timer_group)

        main_layout.addLayout(row1_layout)
        main_layout.addSpacing(10)

        # Do-Input 行
        self.do_plan_selector = FileSelectorBuilder()
        do_input_layout = self.do_plan_selector.build(
            parent=self,
            working_directory=self.working_directory,
            default_value=".workspace/plan-context.md",
            button_text="Do-Input",
            placeholder_text="选择输入文件",
        )
        main_layout.addLayout(do_input_layout)
        main_layout.addSpacing(5)

        # Do-Phase 行
        self.do_phase_selector = FileSelectorBuilder()
        do_phase_layout = self.do_phase_selector.build(
            parent=self,
            working_directory=self.working_directory,
            default_value=".workspace/phase-context.md",
            button_text="Do-Phase",
            placeholder_text="选择输入文件",
        )
        main_layout.addLayout(do_phase_layout)
        main_layout.addSpacing(5)

        # Do-Skills 行
        self.do_skills_selector = FileSelectorBuilder()
        do_skills_layout = self.do_skills_selector.build(
            parent=self,
            working_directory=self.working_directory,
            default_value=".agents/commands/breakdown-phase-to-task/COMMAND.md",
            button_text="Do-Skills",
            placeholder_text="选择技能文件",
        )
        main_layout.addLayout(do_skills_layout)
        main_layout.addSpacing(5)

        # Do-Output 行
        self.do_output_selector = FileSelectorBuilder()
        do_output_layout = self.do_output_selector.build(
            parent=self,
            working_directory=self.working_directory,
            default_value=".workspace/current-phase-draft-$RUNNER_ID.md",
            button_text="Do-Output",
            placeholder_text="选择输出文件",
        )
        main_layout.addLayout(do_output_layout)
        main_layout.addSpacing(5)

        # Do 行
        do_plan = self.do_plan_selector.get_value()
        do_phase = self.do_phase_selector.get_value()
        do_skills = self.do_skills_selector.get_value()
        do_output = self.do_output_selector.get_value()
        
        prompt_do = Template(f"""## Do
- 加载: {do_plan}
- 加载: {do_phase}
- 使用技能: {do_skills}
- 输出: {do_output}
""")

        self.do_runner = TrioRunnerBuilder()
        do_layout = self.do_runner.build(
            working_directory=self.working_directory,
            session_ids=[],
            session_offset=0,
            prompt=prompt_do,
            on_start_callback=self._disable_runner_buttons,
            on_end_callback=self._enable_runner_buttons,
            button_text="Do",
            default_value="05:23",
        )
        self.do_button = self.do_runner.get_button()
        main_layout.addLayout(do_layout)
        main_layout.addSpacing(5)

        # Check-Scoring 行
        self.check_scoring_selector = FileSelectorBuilder()
        check_scoring_layout = self.check_scoring_selector.build(
            parent=self,
            working_directory=self.working_directory,
            default_value=".agents/commands/breakdown-scoring/COMMAND.md",
            button_text="Check-Scoring",
            placeholder_text="选择 Scoring 文件",
        )
        main_layout.addLayout(check_scoring_layout)
        main_layout.addSpacing(5)

        # Check 行
        check_scoring = self.check_scoring_selector.get_value()
        prompt_check = Template(f"""## Check
- 指定文档 {do_output} 是用 AI 生成的，需要交叉复核。
- 使用技能: {check_scoring} 进行复核，执行评审和评分。
""")

        self.check_runner = TrioRunnerBuilder()
        check_layout = self.check_runner.build(
            working_directory=self.working_directory,
            session_ids=[],
            session_offset=1,
            prompt=prompt_check,
            on_start_callback=self._disable_runner_buttons,
            on_end_callback=self._enable_runner_buttons,
            button_text="Check",
            default_value="05:23",
        )
        self.check_button = self.check_runner.get_button()
        main_layout.addLayout(check_layout)
        main_layout.addSpacing(5)

        # Act-Accept 行
        self.act_accept_selector = FileSelectorBuilder()
        act_accept_layout = self.act_accept_selector.build(
            parent=self,
            working_directory=self.working_directory,
            default_value=".workspace/current-phase.md",
            button_text="Act-Accept",
            placeholder_text="选择 Accept 文件",
        )
        main_layout.addLayout(act_accept_layout)
        main_layout.addSpacing(5)

        act_accept = self.act_accept_selector.get_value()
        do_output_template = Template(do_output)
        prompt_act = Template(f"""## Act
检查下列文件的综合评分：
- {do_output_template.substitute(RUNNER_ID='s1')} 
- {do_output_template.substitute(RUNNER_ID='s2')} 
- {do_output_template.substitute(RUNNER_ID='s3')} 

找到其中得分最高的，把内容写入 {act_accept} 表示接受。
""")

        # Act 行
        self.act_runner = SoloRunnerBuilder()
        act_layout = self.act_runner.build(
            working_directory=self.working_directory,
            session_ids=[],
            session_offset=0,
            prompt=prompt_act,
            on_start_callback=self._disable_runner_buttons,
            on_end_callback=self._enable_runner_buttons,
            button_text="Act",
            default_value="05:23",
        )
        self.act_button = self.act_runner.get_button()
        main_layout.addLayout(act_layout)
        main_layout.addSpacing(10)

    def _on_directory_selected(self, selected_dir: str):
        """目录选择回调"""
        self.working_directory = selected_dir
        self.do_plan_selector.set_working_directory(selected_dir)
        self.do_phase_selector.set_working_directory(selected_dir)
        self.do_skills_selector.set_working_directory(selected_dir)
        self.do_output_selector.set_working_directory(selected_dir)
        self.do_runner.set_working_directory(selected_dir)
        self.check_scoring_selector.set_working_directory(selected_dir)
        self.check_runner.set_working_directory(selected_dir)
        self.act_accept_selector.set_working_directory(selected_dir)
        self.act_runner.set_working_directory(selected_dir)
        logger.info(f"工作目录已更新: {selected_dir}")

    def _on_prepare_button_clicked(self):
        """预备按钮点击事件处理"""
        logger.info("预备按钮被点击")
        logger.info(f"工作目录: {self.working_directory}")

    def _on_start_button_clicked(self):
        """开始按钮点击事件处理"""
        logger.info("开始按钮被点击")
        logger.info(f"工作目录: {self.working_directory}")

    def _disable_runner_buttons(self):
        """禁用所有 Runner 按钮"""
        self.do_runner.set_button_enabled(False)
        self.check_runner.set_button_enabled(False)
        self.act_runner.set_button_enabled(False)

    def _enable_runner_buttons(self):
        """启用所有 Runner 按钮"""
        self.do_runner.set_button_enabled(True)
        self.check_runner.set_button_enabled(True)
        self.act_runner.set_button_enabled(True)

    def set_working_directory(self, directory: str):
        """设置工作目录"""
        self.working_directory = directory
        self._on_directory_selected(directory)

    def update_status_display(self, pid: int, elapsed_seconds: int):
        """更新状态显示"""
        self.pid_value_label.setText(str(pid))
        hours = elapsed_seconds // 3600
        minutes = (elapsed_seconds % 3600) // 60
        seconds = elapsed_seconds % 60
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.timer_value_label.setText(time_str)

    def reset_status_display(self):
        """重置状态显示为默认值"""
        self.pid_value_label.setText("--")
        self.timer_value_label.setText("--:--:--")
