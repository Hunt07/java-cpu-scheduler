package com.cpuscheduler.gui;

import java.util.List;

import com.cpuscheduler.model.Process;

import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.scene.control.TableColumn;
import javafx.scene.control.TableView;
import javafx.scene.control.cell.PropertyValueFactory;

public class ProcessTableModel {
    private final ObservableList<Process> processes;
    private final TableView<Process> tableView;

    public ProcessTableModel() {
        this.processes = FXCollections.observableArrayList();
        this.tableView = new TableView<>();
        setupTable();
    }

    private void setupTable() {
        TableColumn<Process, String> pidColumn = new TableColumn<>("PID");
        pidColumn.setCellValueFactory(data -> 
            javafx.beans.binding.Bindings.createStringBinding(
                () -> "P" + data.getValue().getPid()
            )
        );

        TableColumn<Process, Integer> arrivalColumn = new TableColumn<>("Arrival Time");
        arrivalColumn.setCellValueFactory(new PropertyValueFactory<>("arrivalTime"));

        TableColumn<Process, Integer> burstColumn = new TableColumn<>("Burst Time");
        burstColumn.setCellValueFactory(new PropertyValueFactory<>("burstTime"));

        TableColumn<Process, Integer> priorityColumn = new TableColumn<>("Priority");
        priorityColumn.setCellValueFactory(new PropertyValueFactory<>("priority"));

        TableColumn<Process, String> stateColumn = new TableColumn<>("State");
        stateColumn.setCellValueFactory(new PropertyValueFactory<>("state"));

        TableColumn<Process, Integer> remainingColumn = new TableColumn<>("Remaining Time");
        remainingColumn.setCellValueFactory(new PropertyValueFactory<>("remainingTime"));

        TableColumn<Process, Integer> waitingColumn = new TableColumn<>("Waiting Time");
        waitingColumn.setCellValueFactory(new PropertyValueFactory<>("waitingTime"));

        TableColumn<Process, Integer> turnaroundColumn = new TableColumn<>("Turnaround Time");
        turnaroundColumn.setCellValueFactory(new PropertyValueFactory<>("turnaroundTime"));

        tableView.getColumns().addAll(
            pidColumn, arrivalColumn, burstColumn, priorityColumn,
            stateColumn, remainingColumn, waitingColumn, turnaroundColumn
        );

        tableView.setItems(processes);

        // Set column widths
        pidColumn.setPrefWidth(60);
        arrivalColumn.setPrefWidth(80);
        burstColumn.setPrefWidth(80);
        priorityColumn.setPrefWidth(80);
        stateColumn.setPrefWidth(100);
        remainingColumn.setPrefWidth(100);
        waitingColumn.setPrefWidth(80);
        turnaroundColumn.setPrefWidth(100);
    }

    public void addProcess(Process process) {
        processes.add(process);
    }

    public void updateProcess(Process process) {
        int index = findProcessIndex(process.getPid());
        if (index >= 0) {
            processes.set(index, process);
        }
    }

    public void clear() {
        processes.clear();
    }

    private int findProcessIndex(int pid) {
        for (int i = 0; i < processes.size(); i++) {
            if (processes.get(i).getPid() == pid) {
                return i;
            }
        }
        return -1;
    }

    public void updateProcesses(List<Process> newProcesses) {
        processes.setAll(newProcesses);
    }

    public TableView<Process> getTableView() {
        return tableView;
    }
}
