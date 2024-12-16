import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from cpu_scheduler import CPUScheduler, Process
from threading import Thread
import time
import json
import os

class SchedulerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CPU Scheduler Visualizer")
        
        # Theme options
        self.available_themes = ['darkly', 'cosmo', 'flatly', 'litera', 'lumen', 'pulse', 'sandstone', 'yeti']
        self.style = ttk.Style(theme="darkly")  # Default theme
        
        # Remove menu bar initialization
        # Create main layout frames
        self.top_frame = ttk.Frame(self.root)
        self.top_frame.grid(row=0, column=0, sticky="nsew")
        
        # Scrollable container
        self.scroll_canvas = ttk.Canvas(self.top_frame)
        self.scrollbar = ttk.Scrollbar(self.top_frame, orient="vertical", command=self.scroll_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.scroll_canvas)
        
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Grid layout for scroll components
        self.scroll_canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Create window in canvas
        self.scroll_window = self.scroll_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Bottom frame for CPU meter (always visible)
        self.bottom_frame = ttk.Frame(self.root)
        self.bottom_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        # Configure weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.top_frame.grid_columnconfigure(0, weight=1)
        self.top_frame.grid_rowconfigure(0, weight=1)
        
        # Initialize variables
        self.scheduler = CPUScheduler()
        
        # Initialize StringVar variables using ttk
        self.cpu_util_var = ttk.StringVar(value="CPU: 0%")
        self.throughput_var = ttk.StringVar(value="Throughput: 0/s")
        self.context_switches_var = ttk.StringVar(value="Switches: 0")
        self.arrival_var = ttk.StringVar()
        self.burst_var = ttk.StringVar()
        self.priority_var = ttk.StringVar()
        self.algo_var = ttk.StringVar(value="rr")
        
        # Initialize other variables
        self.animation_speed = 1.0
        self.current_time = 0
        self.is_running = False
        self.paused = False
        self.step_mode = False
        self.context_switches = 0
        self.cpu_utilization = 0
        self.last_process_state = None
        self.gantt_history = []
        self.current_process = None

        # Bind scroll region updates
        self.scrollable_frame.bind("<Configure>", self.on_frame_configure)
        self.scroll_canvas.bind("<Configure>", self.on_canvas_configure)
        
        self.setup_gui()
        self.setup_enhanced_gui()
        self.setup_metrics_labels()
        self.setup_cpu_meter()

        # Clear any existing process table
        if hasattr(self, 'process_table'):
            self.process_table.destroy()
            
        # Add process table with scrollbar
        self.table_frame = ttk.Frame(self.scrollable_frame)
        self.table_frame.grid(row=6, column=0, sticky="nsew", padx=5, pady=5)
        
        self.process_table = ttk.Treeview(self.table_frame, columns=(
            "PID", "Arrival", "Burst", "Priority", "State", "Remaining", "Wait", "Turnaround"
        ), show="headings", height=10)
        
        # Configure table headers with fixed widths
        headers = {
            "PID": 60, "Arrival": 80, "Burst": 80, "Priority": 80,
            "State": 100, "Remaining": 100, "Wait": 80, "Turnaround": 100
        }
        
        for col, width in headers.items():
            self.process_table.heading(col, text=col)
            self.process_table.column(col, width=width, anchor="center")
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.process_table.yview)
        x_scrollbar = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.process_table.xview)
        self.process_table.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Grid layout for table and scrollbars
        self.process_table.grid(row=0, column=0, sticky="nsew")
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        x_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Configure frame weights
        self.table_frame.grid_columnconfigure(0, weight=1)
        self.table_frame.grid_rowconfigure(0, weight=1)

        # Add validation
        self.validate_command = self.root.register(self.validate_input)
        
        # Clear any existing process table
        if hasattr(self, 'process_table'):
            self.process_table.destroy()
            
        # Setup table
        self.setup_process_table()

    def on_frame_configure(self, event=None):
        """Reset the scroll region to encompass the scrollable frame"""
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def on_canvas_configure(self, event):
        """When canvas is resized, resize the inner frame to match"""
        canvas_width = event.width
        self.scroll_canvas.itemconfig(self.scroll_window, width=canvas_width)

    def setup_gui(self):
        # Process Control Panel
        control_frame = ttk.Labelframe(self.scrollable_frame, text="Process Control", padding="10")
        control_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Make columns expandable
        for i in range(7):
            control_frame.grid_columnconfigure(i, weight=1)

        # Input fields with bootstrap-style labels
        labels = ["Arrival Time:", "Burst Time:", "Priority:"]
        vars = [self.arrival_var, self.burst_var, self.priority_var]
        
        for i, (label, var) in enumerate(zip(labels, vars)):
            ttk.Label(control_frame, text=label).grid(row=0, column=i*2, padx=5)
            ttk.Entry(control_frame, textvariable=var).grid(row=0, column=i*2+1, padx=5, sticky="ew")

        # Add process button with bootstyle
        add_btn = ttk.Button(control_frame, text="Add Process", 
                           command=self.add_process,
                           style="primary.TButton")
        add_btn.grid(row=0, column=6, padx=5)

        # Algorithm Selection Panel with modern styling
        algo_frame = ttk.Labelframe(self.scrollable_frame, text="Algorithm Selection", padding="10")
        algo_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        algorithms = [
            ("Round Robin", "rr"),
            ("SJF (Non-preemptive)", "sjf"),
            ("SJF (Preemptive)", "sjf_p"),
            ("Priority (Non-preemptive)", "priority"),
            ("Priority (Preemptive)", "priority_p")
        ]
        
        for i, (text, value) in enumerate(algorithms):
            ttk.Radiobutton(algo_frame, text=text, value=value, 
                          variable=self.algo_var).grid(row=0, column=i, padx=5)
            algo_frame.grid_columnconfigure(i, weight=1)

        # Start simulation button
        start_btn = ttk.Button(algo_frame, text="Start Simulation",
                             command=self.start_simulation,
                             style="success.TButton")
        start_btn.grid(row=1, column=0, columnspan=5, pady=10)

        # Process Visualization Area
        vis_frame = ttk.Labelframe(self.scrollable_frame, text="Process Visualization", padding="10")
        vis_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        vis_frame.grid_columnconfigure(0, weight=1)
        vis_frame.grid_rowconfigure(0, weight=1)
        
        # Canvas for visualization
        self.canvas = ttk.Canvas(vis_frame)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Statistics Area
        self.stats_frame = ttk.Labelframe(self.scrollable_frame, text="Statistics", padding="10")
        self.stats_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        
        self.stats_text = ttk.Text(self.stats_frame, height=5, width=70)
        self.stats_text.grid(row=0, column=0, sticky="ew")
        
        # Time label
        self.time_label = ttk.Label(self.scrollable_frame, text="Time: 0")
        self.time_label.grid(row=4, column=0, sticky="w", padx=5, pady=5)

        # State canvas for visualization
        self.state_canvas = ttk.Canvas(self.scrollable_frame, height=150)
        self.state_canvas.grid(row=5, column=0, sticky="ew", padx=5, pady=5)

    def show_theme_selector(self):
        """Show theme selection dialog"""
        theme_window = ttk.Toplevel(self.root)
        theme_window.title("Select Theme")
        theme_window.geometry("300x400")
        
        # Create scrollable frame for themes
        canvas = ttk.Canvas(theme_window)
        scrollbar = ttk.Scrollbar(theme_window, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        
        # Create window in canvas
        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        
        # Add theme buttons
        for theme in self.available_themes:
            ttk.Button(scroll_frame, 
                      text=theme.title(),
                      command=lambda t=theme: [self.change_theme(t), theme_window.destroy()],
                      style="primary.TButton"
            ).pack(fill="x", padx=5, pady=2)
            
        # Configure scrolling
        scroll_frame.bind("<Configure>", 
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
            lambda e: canvas.itemconfig(canvas_window, width=e.width))
            
        # Make window modal
        theme_window.transient(self.root)
        theme_window.grab_set()

    def setup_enhanced_gui(self):
        """Setup enhanced GUI elements"""
        # Control panel
        control_panel = ttk.LabelFrame(self.root, text="Simulation Control")
        control_panel.grid(row=6, column=0, sticky=(W, E), pady=5)
        
        # Control buttons
        ttk.Button(control_panel, text="Start", command=self.start_simulation).grid(row=0, column=0, padx=5)
        ttk.Button(control_panel, text="Pause/Resume", command=self.toggle_pause).grid(row=0, column=1, padx=5)
        ttk.Button(control_panel, text="Step", command=self.step_simulation).grid(row=0, column=2, padx=5)
        ttk.Button(control_panel, text="Reset", command=self.reset_simulation).grid(row=0, column=3, padx=5)
        ttk.Button(control_panel, text="Save", command=self.save_config).grid(row=0, column=4, padx=5)
        ttk.Button(control_panel, text="Load", command=self.load_config).grid(row=0, column=5, padx=5)
        ttk.Button(control_panel, text="Help", command=self.show_help).grid(row=0, column=6, padx=5)
        ttk.Button(control_panel, text="Team", command=self.show_credits).grid(row=0, column=7, padx=5)
        ttk.Button(control_panel, text="Theme", command=self.show_theme_selector).grid(row=0, column=8, padx=5)
        
        # Metrics panel
        metrics_frame = ttk.LabelFrame(self.root, text="Performance Metrics")
        metrics_frame.grid(row=7, column=0, sticky=(W, E), pady=5)
        
        ttk.Label(metrics_frame, textvariable=self.cpu_util_var).grid(row=0, column=0, padx=5)
        ttk.Label(metrics_frame, textvariable=self.throughput_var).grid(row=0, column=1, padx=5)
        ttk.Label(metrics_frame, textvariable=self.context_switches_var).grid(row=0, column=2, padx=5)

    def setup_metrics_labels(self):
        """Setup labels for metrics display"""
        self.cpu_util_label = ttk.Label(self.root, text="0%")
        self.context_switch_label = ttk.Label(self.root, text="0")
        self.throughput_label = ttk.Label(self.root, text="0/s")
        
    def setup_cpu_meter(self):
        """Setup permanent CPU meter at bottom"""
        self.cpu_meter_canvas = ttk.Canvas(self.bottom_frame, height=40)
        self.cpu_meter_canvas.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        
        # Add metrics labels next to CPU meter
        metrics_frame = ttk.Frame(self.bottom_frame)
        metrics_frame.grid(row=0, column=1, padx=5)
        
        ttk.Label(metrics_frame, textvariable=self.cpu_util_var).grid(row=0, column=0, padx=5)
        ttk.Label(metrics_frame, textvariable=self.throughput_var).grid(row=0, column=1, padx=5)
        ttk.Label(metrics_frame, textvariable=self.context_switches_var).grid(row=0, column=2, padx=5)

    def show_help(self):
        """Display help information dialog"""
        help_text = """
CPU Scheduler Simulator Help

Algorithms:
- Round Robin (Q=3): Time slice based scheduling
- SJF: Shortest Job First (Preemptive/Non-preemptive)
- Priority: Priority based scheduling

Controls:
- Add Process: Enter process details
- Run: Start simulation
- Pause: Pause simulation
- Step: Execute one time unit
- Save/Load: Save or load process configurations

Process Parameters:
- Arrival Time: When process enters system
- Burst Time: CPU time needed
- Priority: Lower number = Higher priority

Statistics:
- CPU Utilization: Percentage of CPU in use
- Context Switches: Number of process switches
- Throughput: Processes completed per unit time
"""
        messagebox.showinfo("Help", help_text)
        
    def reset_simulation(self):
        """Reset simulation state"""
        self.is_running = False
        self.paused = False
        self.step_mode = False
        self.current_time = 0
        self.context_switches = 0
        self.cpu_utilization = 0
        
        # Reset processes
        for p in self.scheduler.processes:
            p.state = "ready"
            p.remaining_time = p.burst_time
            p.waiting_time = 0
            p.turnaround_time = 0
            p.response_time = -1
            
        # Update display
        self.draw_enhanced_visualization()
        self.update_statistics()
        
    def add_process(self):
        """Add process with validation and error handling"""
        try:
            # Validate inputs
            if not self.validate_input():
                return
                
            arrival = int(self.arrival_var.get())
            burst = int(self.burst_var.get())
            priority = int(self.priority_var.get())
            
            # Check process limits
            if len(self.scheduler.processes) >= self.scheduler.max_processes:
                raise ValueError(f"Maximum limit of {self.scheduler.max_processes} processes reached")
            
            # Validate first process arrival time
            if not self.scheduler.processes and arrival > 0:
                raise ValueError("First process must arrive at time 0")
                
            # Create process
            pid = len(self.scheduler.processes) + 1
            self.scheduler.add_process(pid, arrival, burst, priority)
            
            # Add to table
            try:
                self.process_table.insert("", "end", values=(
                    f"P{pid}",
                    arrival,
                    burst,
                    priority,
                    "Ready",
                    burst,
                    0,
                    0
                ))
                
                # Clear inputs
                self.arrival_var.set("")
                self.burst_var.set("")
                self.priority_var.set("")
                
                # Update visualization
                self.draw_process_list()
                messagebox.showinfo("Success", f"Process P{pid} added successfully")
                
            except Exception as e:
                # Rollback process addition if table insert fails
                self.scheduler.processes.pop()
                raise Exception(f"Failed to add process to table: {str(e)}")
                
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")

    def draw_process_list(self):
        """Draw process list with state indicators"""
        self.canvas.delete("process_list")
        y = 20
        for p in self.scheduler.processes:
            # Process ID
            self.canvas.create_text(20, y, text=f"P{p.pid}", tags="process_list")
            
            # State indicator
            state_colors = {"ready": "yellow", "running": "green", "completed": "gray"}
            self.canvas.create_rectangle(40, y-10, 60, y+10,
                                      fill=state_colors[p.state],
                                      outline="black",
                                      tags="process_list")
            
            # Burst time bar
            progress = (p.burst_time - p.remaining_time) / p.burst_time
            total_width = p.burst_time * 30
            self.canvas.create_rectangle(70, y-10, 70 + total_width, y+10,
                                      fill="lightblue", outline="black",
                                      tags="process_list")
            self.canvas.create_rectangle(70, y-10, 70 + total_width * progress, y+10,
                                      fill="blue", outline="black",
                                      tags="process_list")
            
            # Process info
            self.canvas.create_text(280, y,
                text=f"Arrival: {p.arrival_time}, Burst: {p.burst_time}, "
                     f"Priority: {p.priority}, State: {p.state}",
                tags="process_list")
            y += 30
    
    def draw_gantt_chart(self):
        """Enhanced Gantt chart with accurate timings"""
        self.state_canvas.delete("gantt")
        x = 50
        y = 6  # Moved up from 60
        cell_width = 40
        cell_height = 30
        
        # Get timing data
        gantt_chart, time_chart = self.current_gantt_data
        max_time = time_chart[-1][1]
        
        # Draw timeline grid
        for i in range(max_time + 1):
            grid_x = x + (i * cell_width)
            self.state_canvas.create_line(
                grid_x, y,
                grid_x, y + len(self.scheduler.processes)*cell_height,
                fill="gray", dash=(2,2), tags="gantt"
            )
            self.state_canvas.create_text(
                grid_x, y - 15,
                text=str(i), tags="gantt"
            )
        
        # Draw process executions
        colors = ["#FFB6C1", "#98FB98", "#87CEFA", "#DDA0DD", "#F0E68C"]
        for i, (pid, (start, end)) in enumerate(zip(gantt_chart, time_chart)):
            process = next(p for p in self.scheduler.processes if p.pid == pid)
            color = colors[process.pid % len(colors)]
            
            # Draw execution block
            block_x1 = x + (start * cell_width)
            block_x2 = x + (end * cell_width)
            block_y = y + (process.pid-1)*cell_height
            
            self.state_canvas.create_rectangle(
                block_x1, block_y,
                block_x2, block_y + cell_height,
                fill=color, outline="black",
                tags="gantt"
            )
            
            # Draw process label
            self.state_canvas.create_text(
                (block_x1 + block_x2)/2, block_y + cell_height/2,
                text=f"P{pid}", tags="gantt"
            )

    def draw_state_transitions(self):
        """Draw process state transitions diagram"""
        x = 400
        y = 20
        radius = 15
        
        # Draw state bubbles
        states = {"ready": (x, y), 
                 "running": (x + 80, y),
                 "completed": (x + 160, y)}
        
        for state, (sx, sy) in states.items():
            color = {"ready": "yellow", "running": "green", "completed": "gray"}[state]
            self.canvas.create_oval(sx-radius, sy-radius, sx+radius, sy+radius,
                                 fill=color, outline="black")
            self.canvas.create_text(sx, sy, text=state.title())
        
        # Draw arrows between states
        self.canvas.create_line(x + radius, y, x + 80 - radius, y,
                              arrow=LAST)
        self.canvas.create_line(x + 80 + radius, y, x + 160 - radius, y,
                              arrow=LAST)
        
        # Draw preemption arrow
        self.canvas.create_line(x + 80, y + radius,
                              x + 80, y + 40,
                              x, y + 40,
                              x, y + radius,
                              arrow=LAST,
                              smooth=True)
    
    def update_process_table(self):
        """Update process table contents"""
        # Clear existing items
        for item in self.process_table.get_children():
            self.process_table.delete(item)
            
        # Re-add all processes with current state
        for p in self.scheduler.processes:
            self.process_table.insert("", "end", values=(
                f"P{p.pid}",
                p.arrival_time,
                p.burst_time,
                p.priority,
                p.state.title(),
                p.remaining_time,
                p.waiting_time,
                p.turnaround_time
            ))
    
    def animate_execution(self, gantt_data):
        """Animated execution with timing data using after() instead of Thread"""
        self.is_running = True
        self.current_time = 0
        self.current_gantt_data = gantt_data
        self.gantt_chart, self.time_chart = gantt_data
        self.current_index = 0
        self.current_time_index = 0
        self.last_pid = None
        
        def update_frame():
            if not self.is_running or (self.paused and not self.step_mode):
                self.root.after(100, update_frame)
                return
                
            if self.current_index < len(self.gantt_chart):
                pid = self.gantt_chart[self.current_index]
                start, end = self.time_chart[self.current_index]
                
                # Count context switches
                if self.last_pid is not None and self.last_pid != pid:
                    self.context_switches += 1
                self.last_pid = pid
                
                if self.current_time_index < end:
                    self.current_time = self.current_time_index
                    self.update_process_states(pid)
                    self.update_performance_metrics()
                    self.draw_enhanced_visualization()
                    self.current_time_index += 1
                    
                    delay = int(self.animation_speed * 1000)  # Convert to milliseconds
                    self.root.after(delay, update_frame)
                else:
                    self.current_index += 1
                    self.root.after(1, update_frame)
                    
                if self.step_mode:
                    self.step_mode = False
                    self.paused = True
            else:
                self.finalize_simulation()
        
        update_frame()

    def update_performance_metrics(self):
        """Calculate and update performance metrics"""
        # CPU Utilization
        active_time = sum(1 for p in self.scheduler.processes if p.state == "running")
        self.cpu_utilization = (active_time / self.current_time) * 100 if self.current_time > 0 else 0
        
        # Throughput
        completed = sum(1 for p in self.scheduler.processes if p.state == "completed")
        throughput = completed / self.current_time if self.current_time > 0 else 0
        
        # Update displays
        self.cpu_util_var.set(f"CPU Utilization: {self.cpu_utilization:.1f}%")
        self.throughput_var.set(f"Throughput: {throughput:.2f} processes/unit")
        self.context_switches_var.set(f"Context Switches: {self.context_switches}")

    def draw_enhanced_visualization(self):
        """Enhanced visualization with fixed CPU meter"""
        self.draw_process_list()
        self.draw_gantt_chart()
        self.draw_cpu_meter()  # Now draws in bottom frame
        self.draw_state_transitions()
        self.update_process_table()
        
        self.time_label.config(text=f"Time: {self.current_time}")
        self.calculate_metrics()
        self.root.update()

    def toggle_pause(self):
        """Pause/Resume simulation"""
        self.paused = not self.paused
        
    def step_simulation(self):
        """Enable single-step mode"""
        self.step_mode = True
        self.paused = False
        
    def save_config(self):
        """Save process configuration to file"""
        try:
            processes = []
            for p in self.scheduler.processes:
                processes.append({
                    'pid': p.pid,
                    'arrival_time': p.arrival_time,
                    'burst_time': p.burst_time,
                    'priority': p.priority
                })
            
            filename = 'process_config.json'
            with open(filename, 'w') as f:
                json.dump(processes, f, indent=2)
            messagebox.showinfo("Success", f"Configuration saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
    
    def load_config(self):
        """Load process configuration from file"""
        try:
            filename = 'process_config.json'
            if not os.path.exists(filename):
                messagebox.showerror("Error", "No saved configuration found")
                return
                
            with open(filename, 'r') as f:
                processes = json.load(f)
            
            # Reset current processes
            self.scheduler.processes.clear()
            
            # Load saved processes
            for p in processes:
                self.scheduler.add_process(
                    p['pid'],
                    p['arrival_time'],
                    p['burst_time'],
                    p['priority']
                )
            
            self.draw_process_list()
            messagebox.showinfo("Success", f"Loaded {len(processes)} processes")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
    
    def draw_cpu_meter(self):
        """Draw CPU utilization meter (now in bottom frame)"""
        canvas = self.cpu_meter_canvas
        canvas.delete("all")
        
        # Get canvas dimensions
        meter_width = canvas.winfo_width() - 20
        meter_height = 30
        x = 10
        y = 5
        
        # Background bar
        canvas.create_rectangle(x, y, x + meter_width, y + meter_height,
                              fill="white", outline="black")
        
        # Calculate CPU utilization
        running_processes = sum(1 for p in self.scheduler.processes if p.state == "running")
        total_time = self.current_time if self.current_time > 0 else 1
        self.cpu_utilization = (running_processes / total_time) * 100
        
        # CPU usage bar
        used_width = int((meter_width * self.cpu_utilization) / 100)
        canvas.create_rectangle(x, y, x + used_width, y + meter_height,
                              fill="green", outline="")
        
        # CPU percentage text
        canvas.create_text(x + meter_width/2, y + meter_height/2,
                          text=f"CPU: {self.cpu_utilization:.1f}%")

    def update_process_states(self, pid):
        """Enhanced process state management with transitions and table updates"""
        try:
            current_time = self.current_time
            last_state = None
            
            for p in self.scheduler.processes:
                if p.pid == pid:
                    # Transition to running
                    if p.state != "running":
                        self.animate_transition(p, "ready", "running")
                        p.update_state("running", current_time)
                        if self.last_process_state != pid:
                            self.context_switches += 1
                    
                    p.remaining_time -= 1
                    if p.remaining_time == 0:
                        self.animate_transition(p, "running", "completed")
                        p.update_state("completed", current_time)
                    
                    self.last_process_state = pid
                    self.current_process = p
                
                elif p.state != "completed":
                    if p.state == "running":
                        self.animate_transition(p, "running", "ready")
                    p.update_state("ready", current_time)

            # Update table
            for item in self.process_table.get_children():
                process_pid = int(self.process_table.item(item)['values'][0][1:])  # Remove 'P' prefix
                process = next((p for p in self.scheduler.processes if p.pid == process_pid), None)
                
                if process:
                    self.process_table.item(item, values=(
                        f"P{process.pid}",
                        process.arrival_time,
                        process.burst_time,
                        process.priority,
                        process.state.title(),
                        process.remaining_time,
                        process.waiting_time,
                        process.turnaround_time
                    ))

            # Ensure table updates
            self.root.after(10, self.update_process_table)  # Schedule table update
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update process states: {str(e)}")
            self.toggle_pause()  # Pause simulation on error

    def animate_transition(self, process, from_state, to_state):
        """Animate process state transitions"""
        x = 400 + (80 if to_state == "running" else 160)
        y = 20
        radius = 15
        
        # Highlight transition path
        if from_state == "ready" and to_state == "running":
            self.canvas.create_line(400 + radius, y, x - radius, y,
                                  fill="red", width=2, tags="transition")
        elif from_state == "running" and to_state == "completed":
            self.canvas.create_line(480 + radius, y, x - radius, y,
                                  fill="red", width=2, tags="transition")
        elif from_state == "running" and to_state == "ready":
            self.canvas.create_line(480, y + radius,
                                  480, y + 40,
                                  400, y + 40,
                                  400, y + radius,
                                  fill="red", width=2, tags="transition")
        
        self.root.after(500, lambda: self.canvas.delete("transition"))

    def calculate_metrics(self):
        """Enhanced performance metrics calculation"""
        if self.current_time == 0:
            return
            
        # CPU Utilization (weighted by time spent)
        total_run_time = sum(len([t for t, s in p.state_history if s == "running"]) 
                            for p in self.scheduler.processes)
        self.cpu_utilization = (total_run_time / self.current_time) * 100
        
        # Throughput (completed processes per unit time)
        completed = sum(1 for p in self.scheduler.processes if p.state == "completed")
        throughput = completed / self.current_time
        
        # Average Response Time
        avg_response = sum(p.response_time for p in self.scheduler.processes 
                         if p.response_time >= 0) / len(self.scheduler.processes)
        
        # Update displays
        self.cpu_util_var.set(f"CPU: {self.cpu_utilization:.1f}%")
        self.throughput_var.set(f"Throughput: {throughput:.2f}")
        self.context_switches_var.set(f"Switches: {self.context_switches}")
        
    def start_simulation(self):
        """Start scheduling simulation with process limit check"""
        if len(self.scheduler.processes) < self.scheduler.min_processes:
            messagebox.showwarning("Warning", 
                f"Need minimum {self.scheduler.min_processes} processes to run simulation")
            return
            
        if self.is_running:
            return
            
        # Reset process states
        for p in self.scheduler.processes:
            p.state = "ready"
            p.remaining_time = p.burst_time
        
        # Run selected algorithm
        algo = self.algo_var.get()
        try:
            if (algo == "rr"):
                gantt_data = self.scheduler.round_robin()
            elif (algo == "sjf"):
                gantt_data = self.scheduler.sjf_nonpreemptive()
            elif (algo == "sjf_p"):
                gantt_data = self.scheduler.sjf_preemptive()
            elif (algo == "priority"):
                gantt_data = self.scheduler.priority_scheduling(False)
            else:
                gantt_data = self.scheduler.priority_scheduling(True)
                
            self.animate_execution(gantt_data)
            self.update_statistics()
        except Exception as e:
            messagebox.showerror("Error", f"Simulation error: {str(e)}")
    
    def update_statistics(self):
        self.stats_text.delete(1.0, END)  # Changed from tk.END
        stats = "Statistics:\n"
        total_wait = 0
        total_turnaround = 0
        
        for p in self.scheduler.processes:
            stats += f"Process {p.pid}: Wait={p.waiting_time}, Turnaround={p.turnaround_time}\n"
            total_wait += p.waiting_time
            total_turnaround += p.turnaround_time
            
        avg_wait = total_wait / len(self.scheduler.processes)
        avg_turnaround = total_turnaround / len(self.scheduler.processes)
        stats += f"\nAverage Wait Time: {avg_wait:.2f}\n"
        stats += f"Average Turnaround Time: {avg_turnaround:.2f}"
        
        self.stats_text.insert(1.0, stats)

    def set_speed(self, value):
        """Set animation speed"""
        try:
            self.animation_speed = float(value)
        except ValueError:
            self.animation_speed = 1.0
            
    def finalize_simulation(self):
        """Clean up after simulation ends"""
        self.is_running = False
        for p in self.scheduler.processes:
            if p.state != "completed":
                p.state = "completed"
        self.draw_enhanced_visualization()
        self.calculate_metrics()
        messagebox.showinfo("Complete", "Simulation finished!")

        # Update final values in table
        for item in self.process_table.get_children():
            process_pid = int(self.process_table.item(item)['values'][0][1:])
            process = next((p for p in self.scheduler.processes if p.pid == process_pid), None)
            
            if process:
                self.process_table.item(item, values=(
                    f"P{process.pid}",
                    process.arrival_time,
                    process.burst_time,
                    process.priority,
                    "Completed",
                    0,  # Remaining time
                    process.waiting_time,
                    process.turnaround_time
                ))

    def show_credits(self):
        """Display team credits"""
        credits_text = """
CPU Scheduler Simulator

Created by:
- Talha ( Development)
- Harris (Scheduler Algorithms)
- Tharany & Vinthya (Testing & Documentation)

Version: 1.0
© 2024 OSS Project Team
        """
        messagebox.showinfo("About", credits_text)
        
    def change_theme(self, theme_name):
        """Change application theme"""
        try:
            self.style.theme_use(theme_name)
            messagebox.showinfo("Theme Changed", f"Theme changed to {theme_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to change theme: {str(e)}")

    def setup_process_table(self):
        """Initialize process table with proper configuration"""
        self.table_frame = ttk.Frame(self.scrollable_frame)
        self.table_frame.grid(row=6, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        # Create table with columns
        self.process_table = ttk.Treeview(self.table_frame)
        self.process_table['columns'] = ('PID', 'Arrival', 'Burst', 'Priority', 'State', 'Remaining', 'Wait', 'Turnaround')
        self.process_table['show'] = 'headings'
        
        # Define column widths and headings
        column_config = {
            'PID': (60, 'center'),
            'Arrival': (80, 'center'),
            'Burst': (80, 'center'),
            'Priority': (80, 'center'),
            'State': (100, 'center'),
            'Remaining': (100, 'center'),
            'Wait': (80, 'center'),
            'Turnaround': (100, 'center')
        }
        
        for col, (width, anchor) in column_config.items():
            self.process_table.column(col, width=width, anchor=anchor)
            self.process_table.heading(col, text=col)
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.process_table.yview)
        x_scrollbar = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.process_table.xview)
        self.process_table.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Grid layout
        self.process_table.grid(row=0, column=0, sticky="nsew")
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        x_scrollbar.grid(row=1, column=0, sticky="ew")
        
        self.table_frame.grid_columnconfigure(0, weight=1)
        self.table_frame.grid_rowconfigure(0, weight=1)

    def validate_input(self):
        """Validate process input parameters"""
        try:
            arrival = int(self.arrival_var.get())
            burst = int(self.burst_var.get())
            priority = int(self.priority_var.get())
            
            if arrival < 0:
                raise ValueError("Arrival time cannot be negative")
            if burst <= 0:
                raise ValueError("Burst time must be positive")
            if priority < 0:
                raise ValueError("Priority cannot be negative")
                
            return True
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
            return False

    def safe_update_table(self):
        """Safely update process table with error handling"""
        try:
            # Clear existing items
            for item in self.process_table.get_children():
                self.process_table.delete(item)
                
            # Re-add all processes with current state
            for p in self.scheduler.processes:
                self.process_table.insert("", "end", values=(
                    f"P{p.pid}",
                    p.arrival_time,
                    p.burst_time,
                    p.priority,
                    p.state.title(),
                    p.remaining_time,
                    p.waiting_time,
                    p.turnaround_time
                ))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update process table: {str(e)}")

if __name__ == "__main__":
    root = ttk.Window()  # Use ttk.Window instead of tk.Tk
    root.geometry("1200x800")  # Set initial window size
    app = SchedulerGUI(root)
    root.mainloop()
