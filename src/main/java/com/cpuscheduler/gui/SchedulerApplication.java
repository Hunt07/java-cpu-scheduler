package com.cpuscheduler.gui;

import java.util.List;
import java.util.Map;

import com.cpuscheduler.model.CPUScheduler;
import com.cpuscheduler.model.Process;

import javafx.application.Application;
import javafx.application.Platform;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Scene;
import javafx.scene.control.Button;
import javafx.scene.control.ComboBox;
import javafx.scene.control.Label;
import javafx.scene.control.TextArea;
import javafx.scene.control.TextField;
import javafx.scene.layout.GridPane;
import javafx.scene.layout.HBox;
import javafx.scene.layout.VBox;
import javafx.stage.Stage;

public class SchedulerApplication extends Application {
    private CPUScheduler scheduler;
    private ProcessTableModel tableModel;
    private TextField arrivalTimeField;
    private TextField burstTimeField;
    private TextField priorityField;
    private Label errorLabel;
    private VBox ganttChartPane;
    
    @Override
    public void start(Stage stage) {
        scheduler = new CPUScheduler();
        tableModel = new ProcessTableModel();
        
        VBox root = new VBox(10);
        root.setPadding(new Insets(10));
        
        // Input fields
        GridPane inputGrid = createInputGrid();
        
        // Error label
        errorLabel = new Label();
        errorLabel.setStyle("-fx-text-fill: red;");
        
        // Add process button
        Button addButton = new Button("Add Process");
        addButton.setOnAction(e -> handleAddProcess());
        
        root.getChildren().addAll(
            inputGrid, 
            addButton,
            errorLabel,
            tableModel.getTableView()
        );
        
        setupAlgorithmControls(root);
        
        ganttChartPane = new VBox(10);
        root.getChildren().add(ganttChartPane);
        
        Scene scene = new Scene(root, 800, 600);
        stage.setTitle("CPU Scheduler");
        stage.setScene(scene);
        stage.show();
    }
    
    private GridPane createInputGrid() {
        GridPane grid = new GridPane();
        grid.setHgap(10);
        grid.setVgap(10);
        
        // Create input fields with validation
        arrivalTimeField = new TextField();
        burstTimeField = new TextField();
        priorityField = new TextField();
        
        // Add labels and fields
        grid.addRow(0, new Label("Arrival Time:"), arrivalTimeField);
        grid.addRow(1, new Label("Burst Time:"), burstTimeField);
        grid.addRow(2, new Label("Priority:"), priorityField);
        
        // Add input validation
        arrivalTimeField.textProperty().addListener((obs, old, newValue) -> {
            if (!newValue.matches("\\d*")) {
                arrivalTimeField.setText(newValue.replaceAll("[^\\d]", ""));
            }
        });
        
        burstTimeField.textProperty().addListener((obs, old, newValue) -> {
            if (!newValue.matches("\\d*")) {
                burstTimeField.setText(newValue.replaceAll("[^\\d]", ""));
            }
        });
        
        priorityField.textProperty().addListener((obs, old, newValue) -> {
            if (!newValue.matches("\\d*")) {
                priorityField.setText(newValue.replaceAll("[^\\d]", ""));
            }
        });
        
        return grid;
    }
    
    private void handleAddProcess() {
        try {
            // Input validation
            if (arrivalTimeField.getText().trim().isEmpty() ||
                burstTimeField.getText().trim().isEmpty() ||
                priorityField.getText().trim().isEmpty()) {
                showError("All fields are required");
                return;
            }
            
            int arrivalTime = Integer.parseInt(arrivalTimeField.getText().trim());
            int burstTime = Integer.parseInt(burstTimeField.getText().trim());
            int priority = Integer.parseInt(priorityField.getText().trim());
            
            // Validate values
            if (arrivalTime < 0) {
                showError("Arrival time cannot be negative");
                return;
            }
            if (burstTime <= 0) {
                showError("Burst time must be positive");
                return;
            }
            if (priority < 0) {
                showError("Priority cannot be negative");
                return;
            }
            
            // Get next process ID
            int pid = scheduler.getProcessCount() + 1;
            
            // Create and add process
            Process process = new Process(pid, arrivalTime, burstTime, priority);
            scheduler.addProcess(pid, arrivalTime, burstTime, priority);
            tableModel.addProcess(process);
            
            // Clear inputs and error message
            clearInputs();
            errorLabel.setText("");
            
            // Show success message
            showSuccess("Process added successfully");
            
        } catch (NumberFormatException e) {
            showError("Please enter valid numbers");
        } catch (IllegalArgumentException e) {
            showError(e.getMessage());
        } catch (Exception e) {
            showError("An unexpected error occurred: " + e.getMessage());
        }
    }
    
    private void showError(String message) {
        Platform.runLater(() -> {
            errorLabel.setText(message);
            errorLabel.setStyle("-fx-text-fill: red;");
        });
    }
    
    private void showSuccess(String message) {
        Platform.runLater(() -> {
            errorLabel.setText(message);
            errorLabel.setStyle("-fx-text-fill: green;");
        });
    }
    
    private void clearInputs() {
        arrivalTimeField.clear();
        burstTimeField.clear();
        priorityField.clear();
    }
    
    private void setupAlgorithmControls(VBox root) {
        HBox algoBox = new HBox(10);
        algoBox.setPadding(new Insets(10));
        
        ComboBox<String> algoCombo = new ComboBox<>();
        algoCombo.getItems().addAll(
            "Round Robin (Q=3)", 
            "SJF (Non-preemptive)", 
            "SJF (Preemptive)",
            "Priority (Non-preemptive)",
            "Priority (Preemptive)"
        );
        algoCombo.setValue("Round Robin (Q=3)");

        Button startButton = new Button("Start Simulation");
        startButton.setStyle("-fx-background-color: #4CAF50; -fx-text-fill: white;");
        startButton.setOnAction(e -> runSimulation(algoCombo.getValue()));

        algoBox.getChildren().addAll(
            new Label("Select Algorithm: "), 
            algoCombo, 
            startButton
        );

        // Statistics area
        VBox statsBox = new VBox(10);
        statsBox.setPadding(new Insets(10));
        statsBox.setStyle("-fx-background-color: #f8f9fa; -fx-padding: 10;");

        TextArea statsArea = new TextArea();
        statsArea.setEditable(false);
        statsArea.setPrefRowCount(5);
        statsArea.setStyle("-fx-font-family: monospace;");

        Label statsLabel = new Label("Statistics");
        statsLabel.setStyle("-fx-font-weight: bold;");
        
        statsBox.getChildren().addAll(statsLabel, statsArea);

        // Gantt chart area
        ganttChartPane = new VBox(10);
        ganttChartPane.setPadding(new Insets(10));
        ganttChartPane.setStyle("-fx-background-color: white; -fx-border-color: #dee2e6;");

        root.getChildren().addAll(algoBox, statsBox, ganttChartPane);
    }

    private void runSimulation(String algorithm) {
        try {
            if (scheduler.getProcessCount() < 3) { // Changed from getMinProcesses()
                showError("At least 3 processes are required");
                return;
            }

            Map<String, List<?>> result = null;
            switch (algorithm) {
                case "Round Robin (Q=3)":
                    result = scheduler.roundRobin();
                    break;
                case "SJF (Non-preemptive)":
                    result = scheduler.sjf(false);
                    break;
                case "SJF (Preemptive)":
                    result = scheduler.sjf(true);
                    break;
                case "Priority (Non-preemptive)":
                    result = scheduler.priorityScheduling(false);
                    break;
                case "Priority (Preemptive)":
                    result = scheduler.priorityScheduling(true);
                    break;
            }

            if (result != null) {
                ganttChartPane.getChildren().clear();
                updateGanttChart(result);
                updateStatistics();
                tableModel.updateProcesses(scheduler.getProcesses()); // Changed from updateProcessTable()
            }

        } catch (Exception e) {
            showError("Simulation error: " + e.getMessage());
        }
    }

    private void updateStatistics() {
        Map<String, Double> stats = scheduler.calculateStatistics();
        StringBuilder sb = new StringBuilder();
        
        sb.append("Performance Metrics:\n\n");
        sb.append(String.format("Average Waiting Time: %.2f\n", stats.get("avgWaitingTime")));
        sb.append(String.format("Average Turnaround Time: %.2f\n", stats.get("avgTurnaroundTime")));
        sb.append(String.format("Average Response Time: %.2f\n", stats.get("avgResponseTime")));
        sb.append(String.format("CPU Utilization: %.2f%%\n", 
            scheduler.getProcesses().stream()
                    .mapToInt(p -> p.getBurstTime())
                    .sum() * 100.0 / scheduler.getTotalTime()));
        
        sb.append("\nProcess Details:\n");
        for (Process p : scheduler.getProcesses()) {
            sb.append(String.format("P%d: Wait=%d, Turnaround=%d, Response=%d\n",
                p.getPid(),
                p.getWaitingTime(),
                p.getTurnaroundTime(),
                p.getResponseTime()
            ));
        }

        TextArea statsArea = (TextArea) ((VBox) ganttChartPane.getParent()
            .lookup(".text-area")).getParent();
        statsArea.setText(sb.toString());
    }

    private void updateGanttChart(Map<String, List<?>> result) {
        List<Integer> ganttChart = (List<Integer>) result.get("ganttChart");
        List<int[]> timeChart = (List<int[]>) result.get("timeChart");
        
        // Clear previous chart
        ganttChartPane.getChildren().clear();
        
        // Create Gantt chart visualization
        HBox chart = new HBox(2); // 2px spacing between blocks
        
        for (int i = 0; i < ganttChart.size(); i++) {
            int pid = ganttChart.get(i);
            int[] time = timeChart.get(i);
            int duration = time[1] - time[0];
            
            // Create process block
            VBox block = new VBox();
            block.setPrefWidth(duration * 30); // Scale factor for visibility
            block.setStyle("-fx-background-color: " + getProcessColor(pid) + ";");
            
            // Add labels
            Label pidLabel = new Label("P" + pid);
            Label timeLabel = new Label(time[0] + "-" + time[1]);
            
            block.getChildren().addAll(pidLabel, timeLabel);
            chart.getChildren().add(block);
        }
        
        // Add time axis
        ganttChartPane.getChildren().addAll(chart);

        // Add timeline labels
        HBox timeline = new HBox(2);
        timeline.setAlignment(Pos.CENTER_LEFT);
        timeline.setPadding(new Insets(0, 0, 0, 50)); // Match block start position

        for (int[] time : timeChart) {
            Label timeLabel = new Label(String.valueOf(time[0]));
            timeLabel.setPrefWidth(30);
            timeline.getChildren().add(timeLabel);
        }
        
        // Add final time
        Label finalTime = new Label(String.valueOf(timeChart.get(timeChart.size()-1)[1]));
        timeline.getChildren().add(finalTime);

        ganttChartPane.getChildren().addAll(chart, timeline);
    }

    private String getProcessColor(int pid) {
        // Color palette for processes
        String[] colors = {
            "#FF9999", "#99FF99", "#9999FF", 
            "#FFFF99", "#FF99FF", "#99FFFF"
        };
        return colors[pid % colors.length];
    }
    
    public static void main(String[] args) {
        launch(args);
    }
}