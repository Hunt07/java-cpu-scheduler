package com.cpuscheduler.model;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Queue;

public class CPUScheduler {
    private List<Process> processes;
    private final int timeQuantum;
    private final int minProcesses;
    private final int maxProcesses;
    private int totalTime = 0;

    public CPUScheduler() {
        this.processes = new ArrayList<>();
        this.timeQuantum = 3;
        this.minProcesses = 3;
        this.maxProcesses = 10;
    }

    public void addProcess(int pid, int arrivalTime, int burstTime, int priority) {
        validateInput(arrivalTime, burstTime, priority);
        Process process = new Process(pid, arrivalTime, burstTime, priority);
        processes.add(process);
        notifyProcessAdded(process);
    }

    private void notifyProcessAdded(Process process) {
        // Implement observer pattern if needed
        System.out.println("Process added: " + process);
    }

    public List<Process> getProcesses() {
        return new ArrayList<>(processes);
    }

    public int getProcessCount() {
        return processes.size();
    }

    public void clearProcesses() {
        processes.clear();
    }

    public Process getProcess(int pid) {
        return processes.stream()
            .filter(p -> p.getPid() == pid)
            .findFirst()
            .orElse(null);
    }

    private void validateInput(int arrivalTime, int burstTime, int priority) {
        List<String> errors = new ArrayList<>();
        
        if (arrivalTime < 0) {
            errors.add("Arrival time cannot be negative");
        }
        if (burstTime <= 0) {
            errors.add("Burst time must be positive");
        }
        if (priority < 0) {
            errors.add("Priority cannot be negative");
        }
        if (processes.size() >= maxProcesses) {
            errors.add("Maximum process limit (" + maxProcesses + ") reached");
        }
        if (processes.isEmpty() && arrivalTime > 0) {
            errors.add("First process must arrive at time 0");
        }
        
        if (!errors.isEmpty()) {
            throw new IllegalArgumentException(String.join(", ", errors));
        }
    }

    public Map<String, List<?>> roundRobin() {
        List<Integer> ganttChart = new ArrayList<>();
        List<int[]> timeChart = new ArrayList<>();
        int currentTime = 0;
        int completedProcesses = 0;
        Queue<Process> readyQueue = new LinkedList<>();

        while (completedProcesses < processes.size()) {
            // Add newly arrived processes
            for (Process p : processes) {
                if (p.getArrivalTime() <= currentTime && p.getRemainingTime() > 0 
                    && !readyQueue.contains(p) && p.getState().equals("ready")) {
                    readyQueue.offer(p);
                }
            }

            if (!readyQueue.isEmpty()) {
                Process current = readyQueue.poll();
                int execTime = Math.min(timeQuantum, current.getRemainingTime());
                
                ganttChart.add(current.getPid());
                timeChart.add(new int[]{currentTime, currentTime + execTime});
                current.updateState("running", currentTime);

                currentTime += execTime;
                current.setRemainingTime(current.getRemainingTime() - execTime);

                if (current.getRemainingTime() == 0) {
                    current.updateState("completed", currentTime);
                    completedProcesses++;
                } else {
                    current.updateState("ready", currentTime);
                    readyQueue.offer(current);
                }
            } else {
                currentTime++;
            }
        }

        updateTotalTime(currentTime);

        Map<String, List<?>> result = new HashMap<>();
        result.put("ganttChart", ganttChart);
        result.put("timeChart", timeChart);
        return result;
    }

    public Map<String, List<?>> sjf(boolean preemptive) {
        List<Integer> ganttChart = new ArrayList<>();
        List<int[]> timeChart = new ArrayList<>();
        int currentTime = 0;
        int completedProcesses = 0;

        while (completedProcesses < processes.size()) {
            Process shortest = null;
            int shortestTime = Integer.MAX_VALUE;

            for (Process p : processes) {
                if (p.getArrivalTime() <= currentTime && p.getRemainingTime() > 0) {
                    if (p.getRemainingTime() < shortestTime) {
                        shortest = p;
                        shortestTime = p.getRemainingTime();
                    }
                }
            }

            if (shortest == null) {
                currentTime++;
                continue;
            }

            ganttChart.add(shortest.getPid());
            int startTime = currentTime;
            
            if (preemptive) {
                currentTime++;
                shortest.setRemainingTime(shortest.getRemainingTime() - 1);
            } else {
                currentTime += shortest.getRemainingTime();
                shortest.setRemainingTime(0);
            }

            timeChart.add(new int[]{startTime, currentTime});
            shortest.updateState("running", startTime);

            if (shortest.getRemainingTime() == 0) {
                shortest.updateState("completed", currentTime);
                completedProcesses++;
            }
        }

        updateTotalTime(currentTime);

        Map<String, List<?>> result = new HashMap<>();
        result.put("ganttChart", ganttChart);
        result.put("timeChart", timeChart);
        return result;
    }

    public Map<String, List<?>> priorityScheduling(boolean preemptive) {
        List<Integer> ganttChart = new ArrayList<>();
        List<int[]> timeChart = new ArrayList<>();
        int currentTime = 0;
        int completedProcesses = 0;

        while (completedProcesses < processes.size()) {
            Process highestPriority = null;
            int highestPriorityValue = Integer.MAX_VALUE;

            for (Process p : processes) {
                if (p.getArrivalTime() <= currentTime && p.getRemainingTime() > 0) {
                    if (p.getPriority() < highestPriorityValue) {
                        highestPriority = p;
                        highestPriorityValue = p.getPriority();
                    }
                }
            }

            if (highestPriority == null) {
                currentTime++;
                continue;
            }

            ganttChart.add(highestPriority.getPid());
            int startTime = currentTime;

            if (preemptive) {
                currentTime++;
                highestPriority.setRemainingTime(highestPriority.getRemainingTime() - 1);
            } else {
                currentTime += highestPriority.getRemainingTime();
                highestPriority.setRemainingTime(0);
            }

            timeChart.add(new int[]{startTime, currentTime});
            highestPriority.updateState("running", startTime);

            if (highestPriority.getRemainingTime() == 0) {
                highestPriority.updateState("completed", currentTime);
                completedProcesses++;
            }
        }

        updateTotalTime(currentTime);

        Map<String, List<?>> result = new HashMap<>();
        result.put("ganttChart", ganttChart);
        result.put("timeChart", timeChart);
        return result;
    }

    public Map<String, Double> calculateStatistics() {
        Map<String, Double> stats = new HashMap<>();
        double totalWaitingTime = 0;
        double totalTurnaroundTime = 0;
        double totalResponseTime = 0;

        for (Process p : processes) {
            totalWaitingTime += p.getWaitingTime();
            totalTurnaroundTime += p.getTurnaroundTime();
            totalResponseTime += p.getResponseTime();
        }

        stats.put("avgWaitingTime", totalWaitingTime / processes.size());
        stats.put("avgTurnaroundTime", totalTurnaroundTime / processes.size());
        stats.put("avgResponseTime", totalResponseTime / processes.size());
        return stats;
    }

    public int getTotalTime() {
        return totalTime;
    }

    private void updateTotalTime(int currentTime) {
        this.totalTime = Math.max(this.totalTime, currentTime);
    }

    // Add getters for min/max processes
    public int getMinProcesses() {
        return minProcesses;
    }

    public int getMaxProcesses() {
        return maxProcesses;
    }
}